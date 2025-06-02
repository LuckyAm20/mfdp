import asyncio
import os
from typing import Dict

import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_BASE = 'http://backend:8000/api/v1'

user_tokens: Dict[int, str] = {}

TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    raise RuntimeError('TELEGRAM_TOKEN is not set')
BOT_SECRET = os.environ.get('BOT_SECRET', '')

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class Form(StatesGroup):
    auth = State()
    login = State()
    top_up = State()
    purchase_status = State()
    pred_paid = State()
    pred_free = State()
    pred_id = State()


async def api_post(path: str, token: str, json_data: dict):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'X-Bot-Secret': BOT_SECRET,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{API_BASE}{path}', json=json_data, headers=headers) as resp:
            return resp.status, await resp.json()


async def api_get(path: str, token: str):
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Bot-Secret': BOT_SECRET,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_BASE}{path}', headers=headers) as resp:
            return resp.status, await resp.json()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(
        'Добро пожаловать! Введите логин и пароль через пробел для регистрации.\n\n'
        'Например: user1 password123'
    )
    await Form.auth.set()


@dp.message_handler(state=Form.auth)
async def process_auth(message: types.Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.reply('Нужно ввести ровно два слова: логин и пароль через пробел.')
        return
    username, password = parts
    payload = {'username': username, 'password': password}
    status, data = await api_post('/auth/register', token='', json_data=payload)
    if status != 200:
        await message.reply(f'Ошибка регистрации: {data.get("detail", data)}')
        return
    bot_token = data['bot_token']
    user_tokens[message.from_user.id] = bot_token
    await message.reply(
        'Успешно зарегистрированы.\n'
        'Теперь используйте кнопки меню ниже.',
        reply_markup=main_menu()
    )
    await state.finish()


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('ⓘ Инфо', '🔑 Авторизация')
    kb.add('💰 Баланс', '🔮 Предсказания')
    return kb


@dp.message_handler(lambda m: m.text == 'ⓘ Инфо')
async def info_handler(message: types.Message):
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    if not token:
        await message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        return

    status_code, data = await api_get('/auth/me', token)
    if status_code != 200:
        await message.reply(f'Ошибка: {data.get("detail", data)}')
        return

    username = data.get('username')
    status_ = data.get('status')
    balance = data.get('balance')
    date_end = data.get('status_date_end')

    await message.reply(
        f'👤 Пользователь: {username}\n'
        f'🔖 Статус: {status_}\n'
        f'💰 Баланс: {balance}\n'
        f'🗓️ Срок до: {date_end}'
    )


@dp.message_handler(lambda m: m.text == '🔑 Авторизация')
async def login_handler(message: types.Message):
    await message.reply('Введите логин и пароль через пробел для авторизации.')
    await Form.login.set()


@dp.message_handler(state=Form.login)
async def process_login(message: types.Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.reply('Нужно ввести ровно два слова: логин и пароль через пробел.')
        return
    username, password = parts
    payload = {'username': username, 'password': password}
    status, data = await api_post('/auth/login', token='', json_data=payload)
    if status != 200:
        await message.reply(f'Ошибка авторизации: {data.get("detail", data)}')
        return
    bot_token = data['bot_token']
    user_tokens[message.from_user.id] = bot_token
    await message.reply('Успешно авторизовались.', reply_markup=main_menu())
    await state.finish()


# Обработчик "Баланс"
@dp.message_handler(lambda m: m.text == '💰 Баланс')
async def balance_menu(message: types.Message):
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    if not token:
        await message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton('Пополнить', callback_data='bal_topup')
    )
    kb.add(
        types.InlineKeyboardButton('Купить статус', callback_data='bal_purchase'),
        types.InlineKeyboardButton('История', callback_data='bal_history')
    )
    await message.reply('Выберите действие с балансом:', reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('bal_'))
async def process_balance_cb(callback_query: types.CallbackQuery):
    tg_id = callback_query.from_user.id
    token = user_tokens.get(tg_id)
    action = callback_query.data
    if not token:
        await callback_query.message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        await callback_query.answer()
        return

    elif action == 'bal_topup':
        await callback_query.message.reply('Введите сумму для пополнения:')
        await Form.top_up.set()
        await callback_query.answer()

    elif action == 'bal_purchase':
        await callback_query.message.reply(
            'Введите статус для покупки (silver, gold, diamond):'
        )
        await Form.purchase_status.set()
        await callback_query.answer()

    elif action == 'bal_history':
        payload = {'amount': 5}
        status, data = await api_post('/balance/history', token, payload)
        if status != 200:
            await callback_query.message.reply(f'Ошибка: {data.get("detail", data)}')
        else:
            msgs = []
            for item in data['history']:
                txt = (
                    f'💵 {"+" if item["amount"] > 0 else ""}{item["amount"]} | '
                    f'{item["description"]} | {item["timestamp"]}'
                )
                msg = await callback_query.message.reply(txt)
                msgs.append(msg)
            await asyncio.sleep(30)
            for m in msgs:
                try:
                    await m.delete()
                except:
                    pass
        await callback_query.answer()


@dp.message_handler(state=Form.top_up)
async def process_top_up(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    try:
        amount = float(message.text.strip())
    except:
        await message.reply('Введите корректное число.')
        return
    payload = {'amount': amount}
    status, data = await api_post('/balance/top_up', token, payload)
    if status != 200:
        await message.reply(f'Ошибка: {data.get("detail", data)}')
    else:
        await message.reply(f'Пополнено: {data["amount"]}\nНовый баланс: {data["new_balance"]}',
                            reply_markup=main_menu())
    await state.finish()


@dp.message_handler(state=Form.purchase_status)
async def process_purchase_status(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    status_str = message.text.strip().lower()
    if status_str not in ('silver', 'gold', 'diamond'):
        await message.reply('Неверный статус. Введите silver, gold или diamond.')
        return
    payload = {'status': status_str}
    status_code, data = await api_post('/balance/purchase', token, payload)
    if status_code != 200:
        await message.reply(f'Ошибка: {data.get("detail", data)}')
    else:
        await message.reply(
            f'Новый статус: {data["status"]}\nСрок до: {data["status_date_end"]}\n'
            f'Остаток баланса: {data["remaining_balance"]}',
            reply_markup=main_menu()
        )
    await state.finish()


# Обработчик "Предсказания"
@dp.message_handler(lambda m: m.text == '🔮 Предсказания')
async def prediction_menu(message: types.Message):
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    if not token:
        await message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton('Платное', callback_data='pred_paid'),
        types.InlineKeyboardButton('Бесплатное', callback_data='pred_free')
    )
    kb.add(
        types.InlineKeyboardButton('Получить по ID', callback_data='pred_get'),
        types.InlineKeyboardButton('История', callback_data='pred_history')
    )
    await message.reply('Выберите действие с предсказаниями:', reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('pred_'))
async def process_pred_cb(callback_query: types.CallbackQuery):
    tg_id = callback_query.from_user.id
    token = user_tokens.get(tg_id)
    action = callback_query.data
    if not token:
        await callback_query.message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        return

    if action == 'pred_paid':
        await callback_query.message.reply('Введите номер района для платного предсказания:')
        await Form.pred_paid.set()

    elif action == 'pred_free':
        await callback_query.message.reply('Введите номер района для бесплатного предсказания:')
        await Form.pred_free.set()

    elif action == 'pred_get':
        await callback_query.message.reply('Введите ID предсказания:')
        await Form.pred_id.set()

    elif action == 'pred_history':
        payload = {'amount': 5}
        status_code, data = await api_post('/prediction/history', token, payload)
        if status_code != 200:
            await callback_query.message.reply(f'Ошибка: {data.get("detail", data)}')
        else:
            msgs = []
            for item in data['history']:
                txt = (
                    f'🆔 {item["id"]} | {item["city"]} | район {item["district"]} | '
                    f'час {item["hour"]} | статус {item["status"]} | {item["timestamp"]}'
                )
                msg = await callback_query.message.reply(txt)
                msgs.append(msg)
            await asyncio.sleep(30)
            for m in msgs:
                try:
                    await m.delete()
                except:
                    pass

    await callback_query.answer()


@dp.message_handler(state=Form.pred_paid)
async def process_pred_paid(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    try:
        district = int(message.text.strip())
    except:
        await message.reply('Введите корректное целое число района.')
        return
    payload = {'district': district}
    status_code, data = await api_post('/prediction/nyc_cost', token, payload)
    if status_code == 402:
        await message.reply('Недостаточно средств для предсказания.', reply_markup=main_menu())
    elif status_code == 429:
        await message.reply('Исчерпан лимит бесплатных предсказаний.', reply_markup=main_menu())
    elif status_code != 201:
        await message.reply(f'Ошибка: {data.get("detail", data)}', reply_markup=main_menu())
    else:
        await message.reply(f'Задача создана, ID = {data["id"]}', reply_markup=main_menu())
    await state.finish()


@dp.message_handler(state=Form.pred_free)
async def process_pred_free(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    try:
        district = int(message.text.strip())
    except:
        await message.reply('Введите корректное целое число района.')
        return
    payload = {'district': district}
    status_code, data = await api_post('/prediction/nyc_free', token, payload)
    if status_code == 429:
        await message.reply('Исчерпан лимит бесплатных предсказаний.', reply_markup=main_menu())
    elif status_code != 201:
        await message.reply(f'Ошибка: {data.get("detail", data)}', reply_markup=main_menu())
    else:
        await message.reply(f'Задача создана, ID = {data["id"]}', reply_markup=main_menu())
    await state.finish()


@dp.message_handler(state=Form.pred_id)
async def process_pred_id(message: types.Message, state: FSMContext):
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    try:
        pred_id = int(message.text.strip())
    except:
        await message.reply('Введите корректный ID (число).')
        return
    status_code, data = await api_get(f'/prediction/{pred_id}', token)
    if status_code == 404:
        await message.reply('Предсказание не найдено.', reply_markup=main_menu())
    elif status_code != 200:
        await message.reply(f'Ошибка: {data.get("detail", data)}', reply_markup=main_menu())
    else:
        res = data['result'] or 'Пока нет результата'
        await message.reply(
            f'ID: {data["id"]}\nСтатус: {data["status"]}\nРезультат: {res}',
            reply_markup=main_menu()
        )
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
