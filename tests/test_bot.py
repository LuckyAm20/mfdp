import logging
import os
import sys

import pytest
import asyncio

from types import SimpleNamespace

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
APP_BACKEND_DIR = os.path.join(PROJECT_ROOT, 'app', 'tg_bot')
if APP_BACKEND_DIR not in sys.path:
    sys.path.insert(0, APP_BACKEND_DIR)

from bot import (
    dp,
    user_tokens,
    API_BASE,
    BOT_SECRET,
    Form,
    info_handler,
    cmd_start,
    process_auth,
    login_handler,
    process_login,
    balance_menu,
    process_balance_cb,
    process_top_up,
    process_purchase_status,
    prediction_menu,
    process_pred_cb,
    process_pred_paid,
    process_pred_free,
    process_pred_id,
    api_get,
    api_post,
)

pytestmark = pytest.mark.asyncio

class DummyUser:
    def __init__(self, user_id):
        self.id = user_id


class DummyMessage:
    def __init__(self, text, user_id=1):
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.replies = []

    async def reply(self, text, **kwargs):
        self.replies.append(text)
        return SimpleNamespace(message_id=123, text=text)


class DummyCallbackQuery:
    def __init__(self, data, user_id=1):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id)
        self.message = DummyMessage(text='', user_id=user_id)
        self.answered = False

    async def answer(self, **kwargs):
        self.answered = True


class DummyState:
    async def set_state(self, *args, **kwargs):
        pass

    async def clear(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def clear_user_tokens():
    user_tokens.clear()
    yield
    user_tokens.clear()


@pytest.fixture
def dummy_state():
    return DummyState()


@pytest.fixture(autouse=True)
def mock_api(monkeypatch):
    async def fake_api_get(path, token):
        if path == '/auth/me':
            return 200, {
                'username': 'ivan',
                'status': 'silver',
                'balance': 100.0,
                'status_date_end': '2025-07-01'
            }
        return 404, {'detail': 'Not Found'}

    async def fake_api_post(path, token, json_data):
        if path == '/auth/register':
            if json_data.get('username') and json_data.get('password'):
                return 200, {'bot_token': 'bot_jwt_token_example'}
            return 400, {'detail': 'Invalid data'}

        if path == '/auth/login':
            if json_data.get('username') == 'ivan' and json_data.get('password') == 'secret':
                return 200, {'bot_token': 'bot_jwt_token_example'}
            return 401, {'detail': 'Invalid credentials'}

        if path == '/balance/top_up':
            if json_data.get('amount') and token == 'bot_jwt_token_example':
                return 200, {'amount': json_data['amount'], 'new_balance': 150.0}
            return 400, {'detail': 'Bad Request'}

        if path == '/balance/purchase':
            if json_data.get('status') and token == 'bot_jwt_token_example':
                return 200, {
                    'status': json_data['status'],
                    'status_date_end': '2025-08-01',
                    'remaining_balance': 90.0
                }
            return 400, {'detail': 'Bad Request'}

        if path == '/balance/history':
            return 200, {
                'history': [
                    {'amount': 50.0, 'description': 'Пополнение', 'timestamp': '2025-06-01 12:00:00'},
                    {'amount': -10.0, 'description': 'Покупка статуса', 'timestamp': '2025-06-01 13:00:00'},
                ]
            }

        if path == '/prediction/nyc_cost':
            if json_data.get('district') == 5:
                return 201, {'id': 42}
            return 402, {'detail': 'Недостаточно средств'}

        if path == '/prediction/nyc_free':
            if json_data.get('district') == 3:
                return 201, {'id': 43}
            return 429, {'detail': 'Лимит исчерпан'}

        if path == '/prediction/history':
            return 200, {
                'history': [
                    {
                        'id': 42, 'city': 'NYC', 'district': 5,
                        'hour': 14, 'status': 'completed', 'timestamp': '2025-06-01 14:00:00'
                    },
                    {
                        'id': 43, 'city': 'NYC', 'district': 3,
                        'hour': 15, 'status': 'pending', 'timestamp': '2025-06-01 15:00:00'
                    },
                ]
            }

        if path.startswith('/prediction/'):
            pid = int(path.split('/')[-1])
            if pid == 42:
                return 200, {'id': 42, 'status': 'completed', 'result': '[100, 110]'}
            return 404, {'detail': 'Not Found'}

        return 404, {'detail': 'Not Found'}

    monkeypatch.setattr('bot.api_get', fake_api_get)
    monkeypatch.setattr('bot.api_post', fake_api_post)
    yield


@pytest.mark.asyncio
async def test_start_sets_state_and_requests_credentials(dummy_state):
    msg = DummyMessage('/start', user_id=10)
    await cmd_start(msg, dummy_state)
    assert msg.replies
    assert 'Введите логин и пароль' in msg.replies[0]


@pytest.mark.asyncio
async def test_successful_registration_stores_token_and_sends_menu(dummy_state):
    msg_start = DummyMessage('/start', user_id=11)
    await cmd_start(msg_start, dummy_state)

    msg_auth = DummyMessage('ivan secret', user_id=11)

    await process_auth(msg_auth, dummy_state)

    assert user_tokens[11] == 'bot_jwt_token_example'
    assert any('Успешно зарегистрированы' in r for r in msg_auth.replies)


@pytest.mark.asyncio
async def test_info_handler_without_token_prompts_registration():
    msg = DummyMessage('ⓘ Инфо', user_id=20)
    await info_handler(msg)
    assert msg.replies == ['Сначала зарегистрируйтесь или авторизуйтесь.']


@pytest.mark.asyncio
async def test_info_handler_with_token_returns_user_info():
    user_tokens[30] = 'bot_jwt_token_example'
    msg = DummyMessage('ⓘ Инфо', user_id=30)
    await info_handler(msg)

    assert len(msg.replies) == 1
    text = msg.replies[0]
    assert '👤 Пользователь: ivan' in text
    assert '🔖 Статус: silver' in text
    assert '💰 Баланс: 100.0' in text
    assert '🗓️ Срок до: 2025-07-01' in text


@pytest.mark.asyncio
async def test_balance_menu_without_token_prompts_registration():
    msg = DummyMessage('💰 Баланс', user_id=40)
    await balance_menu(msg)
    assert msg.replies == ['Сначала зарегистрируйтесь или авторизуйтесь.']


@pytest.mark.asyncio
async def test_balance_menu_shows_inline_keyboard():
    user_tokens[41] = 'bot_jwt_token_example'
    msg = DummyMessage('💰 Баланс', user_id=41)
    await balance_menu(msg)
    assert any('Выберите действие с балансом' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_balance_topup_flow(dummy_state):
    user_tokens[50] = 'bot_jwt_token_example'
    callback = DummyCallbackQuery(data='bal_topup', user_id=50)
    await process_balance_cb(callback, dummy_state)
    assert any('Введите сумму для пополнения' in r for r in callback.message.replies)
    assert callback.answered is True

    msg = DummyMessage('25', user_id=50)
    await process_top_up(msg, dummy_state)

    assert any('Пополнено: 25.0' in r for r in msg.replies)
    assert any('Новый баланс: 150.0' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_balance_purchase_flow(dummy_state):
    user_tokens[60] = 'bot_jwt_token_example'
    callback = DummyCallbackQuery(data='bal_purchase', user_id=60)
    await process_balance_cb(callback, dummy_state)
    assert any('Введите статус для покупки' in r for r in callback.message.replies)
    assert callback.answered is True

    msg = DummyMessage('gold', user_id=60)
    await process_purchase_status(msg, dummy_state)
    assert any('Новый статус: gold' in r for r in msg.replies)
    assert any('Срок до: 2025-08-01' in r for r in msg.replies)
    assert any('Остаток баланса: 90.0' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_balance_history_flow(dummy_state):
    user_tokens[70] = 'bot_jwt_token_example'
    callback = DummyCallbackQuery(data='bal_history', user_id=70)
    await process_balance_cb(callback, dummy_state)
    assert len(callback.message.replies) == 2
    assert 'Пополнение' in callback.message.replies[0]
    assert 'Покупка статуса' in callback.message.replies[1]


@pytest.mark.asyncio
async def test_prediction_menu_without_token_prompts_registration():
    msg = DummyMessage('🔮 Предсказания', user_id=80)
    await prediction_menu(msg)
    assert msg.replies == ['Сначала зарегистрируйтесь или авторизуйтесь.']


@pytest.mark.asyncio
async def test_prediction_menu_shows_inline_keyboard():
    user_tokens[81] = 'bot_jwt_token_example'
    msg = DummyMessage('🔮 Предсказания', user_id=81)
    await prediction_menu(msg)
    assert any('Выберите действие с предсказаниями' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_pred_paid_flow_success(dummy_state):
    user_tokens[90] = 'bot_jwt_token_example'

    callback = DummyCallbackQuery(data='pred_paid', user_id=90)
    await process_pred_cb(callback, dummy_state)
    assert any('Введите номер района для платного предсказания' in r for r in callback.message.replies)

    msg = DummyMessage('5', user_id=90)
    await process_pred_paid(msg, dummy_state)
    assert any('Задача создана, ID = 42' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_pred_paid_flow_insufficient_funds(dummy_state):
    user_tokens[91] = 'bot_jwt_token_example'

    callback = DummyCallbackQuery(data='pred_paid', user_id=91)
    await process_pred_cb(callback, dummy_state)

    msg = DummyMessage('4', user_id=91)
    await process_pred_paid(msg, dummy_state)
    assert any('Недостаточно средств' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_pred_free_flow_success(dummy_state):
    user_tokens[100] = 'bot_jwt_token_example'
    callback = DummyCallbackQuery(data='pred_free', user_id=100)
    await process_pred_cb(callback, dummy_state)

    msg = DummyMessage('3', user_id=100)
    await process_pred_free(msg, dummy_state)
    assert any('Задача создана, ID = 43' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_pred_free_flow_limit_exceeded(dummy_state):
    user_tokens[101] = 'bot_jwt_token_example'
    callback = DummyCallbackQuery(data='pred_free', user_id=101)
    await process_pred_cb(callback, dummy_state)

    msg = DummyMessage('2', user_id=101)
    await process_pred_free(msg, dummy_state)
    assert any('Исчерпан лимит бесплатных предсказаний' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_pred_get_flow_not_found(dummy_state):
    user_tokens[110] = 'bot_jwt_token_example'
    callback = DummyCallbackQuery(data='pred_get', user_id=110)
    await process_pred_cb(callback, dummy_state)
    assert any('Введите ID предсказания' in r for r in callback.message.replies)

    msg = DummyMessage('999', user_id=110)
    await process_pred_id(msg, dummy_state)
    assert any('Предсказание не найдено' in r for r in msg.replies)


@pytest.mark.asyncio
async def test_pred_history_flow(dummy_state):
    user_tokens[120] = 'bot_jwt_token_example'
    callback = DummyCallbackQuery(data='pred_history', user_id=120)
    await process_pred_cb(callback, dummy_state)

    assert len(callback.message.replies) == 2
    assert 'район 5' in callback.message.replies[0]
    assert 'район 3' in callback.message.replies[1]
