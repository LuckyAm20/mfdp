import ast
import asyncio
import os
from typing import Dict, Optional

import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile

API_BASE = 'http://backend:8000/api/v1'

user_tokens: Dict[int, str] = {}

TOKEN = os.getenv('TELEGRAM_TOKEN', '1234567890:ABCdefGHIJKlmNoPQRsTUVwxyZ')

BOT_SECRET = os.environ.get('BOT_SECRET', '')
from aiogram.client.session.aiohttp import AiohttpSession

session = AiohttpSession(timeout=50)
bot = Bot(token=TOKEN, session=session)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


class Form(StatesGroup):
    auth = State()
    login = State()
    top_up = State()
    purchase_status = State()
    pred_paid = State()
    pred_free = State()
    pred_id = State()


async def api_post(path: str, token: str, json_data: dict) -> tuple[int, dict]:
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'X-Bot-Secret': BOT_SECRET,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{API_BASE}{path}', json=json_data, headers=headers) as resp:
            return resp.status, await resp.json()


async def api_get(path: str, token: str) -> tuple[int, dict]:
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Bot-Secret': BOT_SECRET,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_BASE}{path}', headers=headers) as resp:
            return resp.status, await resp.json()


def main_menu() -> types.ReplyKeyboardMarkup:
    keyboard = [
        [
            types.KeyboardButton(text='ⓘ Инфо'),
            types.KeyboardButton(text='🔑 Авторизация'),
        ],
        [
            types.KeyboardButton(text='💰 Баланс'),
            types.KeyboardButton(text='🔮 Предсказания'),
        ],
    ]
    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@router.message(F.text == '/start')
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await message.reply(
        'Добро пожаловать! Введите логин и пароль через пробел для регистрации.\n\n'
        'Например: user1 password123'
    )
    await state.set_state(Form.auth)


@router.message(Form.auth)
async def process_auth(message: types.Message, state: FSMContext) -> None:
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
    await state.clear()


@router.message(F.text == 'ⓘ Инфо')
async def info_handler(message: types.Message) -> None:
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


@router.message(F.text == '🔑 Авторизация')
async def login_handler(message: types.Message, state: FSMContext) -> None:
    await message.reply('Введите логин и пароль через пробел для авторизации.')
    await state.set_state(Form.login)


@router.message(Form.login)
async def process_login(message: types.Message, state: FSMContext) -> None:
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
    await state.clear()


@router.message(F.text == '💰 Баланс')
async def balance_menu(message: types.Message) -> None:
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    if not token:
        await message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        return

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text='Пополнить', callback_data='bal_topup')
            ],
            [
                types.InlineKeyboardButton(text='Купить статус', callback_data='bal_purchase'),
                types.InlineKeyboardButton(text='История', callback_data='bal_history')
            ],
        ]
    )
    await message.reply('Выберите действие с балансом:', reply_markup=kb)


@router.callback_query(F.data.startswith('bal_'))
async def process_balance_cb(callback: types.CallbackQuery, state: FSMContext) -> None:
    tg_id = callback.from_user.id
    token = user_tokens.get(tg_id)
    action = callback.data

    if not token:
        await callback.message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        await callback.answer()
        return

    if action == 'bal_topup':
        await callback.message.reply('Введите сумму для пополнения:')
        await state.set_state(Form.top_up)
        await callback.answer()
        return

    elif action == 'bal_purchase':
        kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text='silver'),
                    types.KeyboardButton(text='gold'),
                    types.KeyboardButton(text='diamond'),
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await callback.message.reply(
            'Выберите статус для покупки:',
            reply_markup=kb
        )

        await state.set_state(Form.purchase_status)
        await callback.answer()
        return

    elif action == 'bal_history':
        payload = {'amount': 5}
        status, data = await api_post('/balance/history', token, payload)
        if status != 200:
            await callback.message.reply(f'Ошибка: {data.get("detail", data)}')
        else:
            msgs = []
            for item in data['history']:
                txt = (
                    f'💵 {"+" if item["amount"] > 0 else ""}{item["amount"]} | '
                    f'{item["description"]} | {item["timestamp"]}'
                )
                msg = await callback.message.reply(txt)
                msgs.append(msg)

            await callback.answer()

            async def delete_later(messages_to_delete):
                await asyncio.sleep(30)
                for m in messages_to_delete:
                    try:
                        await m.delete()
                    except:
                        pass

            await asyncio.create_task(delete_later(msgs))
            return


@router.message(Form.top_up)
async def process_top_up(message: types.Message, state: FSMContext) -> None:
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
        await message.reply(
            f'Пополнено: {data["amount"]}\nНовый баланс: {data["new_balance"]}',
            reply_markup=main_menu()
        )
    await state.clear()


@router.message(Form.purchase_status)
async def process_purchase_status(message: types.Message, state: FSMContext) -> None:
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
            f'Новый статус: {data["status"]}\n'
            f'Срок до: {data["status_date_end"]}\n'
            f'Остаток баланса: {data["remaining_balance"]}',
            reply_markup=main_menu()
        )
    await state.clear()


@router.message(F.text == '🔮 Предсказания')
async def prediction_menu(message: types.Message) -> None:
    tg_id = message.from_user.id
    token = user_tokens.get(tg_id)
    if not token:
        await message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        return

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text='Платное', callback_data='pred_paid'),
                types.InlineKeyboardButton(text='Бесплатное', callback_data='pred_free')
            ],
            [
                types.InlineKeyboardButton(text='Получить по ID', callback_data='pred_get'),
                types.InlineKeyboardButton(text='История', callback_data='pred_history')
            ],
            [
                types.InlineKeyboardButton(text='Карты', callback_data='pred_map')
            ]
        ]
    )
    await message.reply('Выберите действие с предсказаниями:', reply_markup=kb)


@router.callback_query(F.data.startswith('pred_'))
async def process_pred_cb(callback: types.CallbackQuery, state: FSMContext) -> None:
    tg_id = callback.from_user.id
    token = user_tokens.get(tg_id)
    action = callback.data

    if not token:
        await callback.message.reply('Сначала зарегистрируйтесь или авторизуйтесь.')
        await callback.answer()
        return
    if action == 'pred_map':
        base_dir = os.path.dirname(__file__)
        maps_dir = os.path.join(base_dir, 'maps')
        if not os.path.isdir(maps_dir):
            await callback.message.reply('Папка с картами не найдена')
        else:
            files = [f for f in os.listdir(maps_dir) if f.lower().endswith(('.jpg', '.jpeg'))]
            if not files:
                await callback.message.reply('Карта не найдена')
            else:
                for filename in files:
                    path = os.path.join(maps_dir, filename)

                    photo = FSInputFile(path)
                    await callback.message.reply_photo(photo)
        await callback.answer()
        return
    if action == 'pred_paid':
        await callback.message.reply('Введите номер района для платного предсказания:')
        await state.set_state(Form.pred_paid)

    elif action == 'pred_free':
        await callback.message.reply('Введите номер района для бесплатного предсказания:')
        await state.set_state(Form.pred_free)

    elif action == 'pred_get':
        await callback.message.reply('Введите ID предсказания:')
        await state.set_state(Form.pred_id)

    elif action == 'pred_history':
        payload = {'amount': 5}
        status_code, data = await api_post('/prediction/history', token, payload)
        if status_code != 200:
            await callback.message.reply(f'Ошибка: {data.get("detail", data)}')
        else:
            msgs = []
            for item in data['history']:
                txt = (
                    f'🆔 {item["id"]} | {item["city"]} | район {item["district"]} | '
                    f'час {item["hour"]} | статус {item["status"]} | {item["timestamp"]}'
                )
                msg = await callback.message.reply(txt)
                msgs.append(msg)

            await callback.answer()

            async def delete_later(messages_to_delete):
                await asyncio.sleep(30)
                for m in messages_to_delete:
                    try:
                        await m.delete()
                    except:
                        pass

            asyncio.create_task(delete_later(msgs))

    await callback.answer()


@router.message(Form.pred_paid)
async def process_pred_paid(message: types.Message, state: FSMContext) -> None:
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
    await state.clear()


@router.message(Form.pred_free)
async def process_pred_free(message: types.Message, state: FSMContext) -> None:
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
    await state.clear()


def format_hourly_demand_with_costs(
        hour_start: int,
        demand_str: str,
        costs_str: Optional[str] = None
) -> str:
    if demand_str == 'Пока нет результата':
        return demand_str
    demand_list = ast.literal_eval(demand_str)
    costs_list = ast.literal_eval(costs_str) if costs_str is not None else None

    lines = []
    for i, demand in enumerate(demand_list):
        hour = (hour_start + i - 8) % 24
        line = f'🕒 {hour:02d}:00 - 🚗 {demand} поездок'
        if costs_list is not None:
            cost = costs_list[i]
            line += f', 💰 {cost:.2f} $ per mile'
        lines.append(line)
    return '\n'.join(lines)


@router.message(Form.pred_id)
async def process_pred_id(message: types.Message, state: FSMContext) -> None:
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
        res_str = data.get('result') or 'Пока нет результата'
        word = ''
        res = format_hourly_demand_with_costs(data['hour'], res_str, data.get('trip_costs'))
        if data['trip_costs'] is not None:
            word = 'и стоимость '
        await message.reply(
            f'ID: {data["id"]}\nСтатус: {data["status"]}\nСпрос {word}по часам:\n{res}',
            reply_markup=main_menu()
        )
    await state.clear()


async def main() -> None:
    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())
