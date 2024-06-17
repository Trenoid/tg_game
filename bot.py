import asyncio
import logging
import os
import requests
from aiogram import Bot, Dispatcher, types,F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart,Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InputFile
from aiogram.types import InputMediaPhoto

from threading import Thread
from flask import Flask, request, jsonify

from config import GAME_URL
from db import add_user, init_db, create_teams, user_exists, get_user_profile,get_rating_table,COMANDS_NAME,update_user_score,update_team_score


app = Flask(__name__)
bot = Bot(token="7489624166:AAGCWo2Q_I0cZ8ME47BopaNnyHOS6GQdQ48")
dp = Dispatcher()


# ikb = InlineKeyboardButton("Перейти", web_app=WebAppInfo('https://<your_domain>'))
# kb = KeyboardButton("Перейти", web_app=WebAppInfo('https://<your_domain>'))

# Настройка логирования
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Получение логгера для aiogram
logger = logging.getLogger('aiogram')


# Схема базы данных
class User(StatesGroup):
    user_id = State()
    username = State()
    team_name = State()
    score = State()


# Обработка POST-запроса с результатами игры
@app.route('/update_score', methods=['POST'])
async def update_score():
    data = request.json
    try:
        user_id = data['user_id']
        score = data['score']
        user = await get_user_profile(user_id)
        if user:
            team_id = user['team_id']
            await update_user_score(user_id, score)
            await update_team_score(team_id, score)
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except KeyError as e:
        return jsonify({"error": "Missing key in JSON data"}), 400



def create_game_url(user_id: int = None, team_id: int = None) -> str:
    return f"{GAME_URL}"
    # return f"{GAME_URL}?user_id={user_id}&team_id={team_id}"

#Создаем инлайн-клавиатуру с командами
def create_team_keyboard():
    builder = InlineKeyboardBuilder()
    for i in range(10):
        builder.add(InlineKeyboardButton(
            text=f"Команда {COMANDS_NAME[i]}",
            callback_data=f"team_{i}"
        ))
    builder.adjust(2)  # Устанавливаем количество кнопок в ряду
    return builder.as_markup()

def create_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Мой профиль"))
    builder.add(types.KeyboardButton(text="Рейтинговая таблица"))
    builder.add(types.KeyboardButton(text="Играть"))
    builder.add(types.KeyboardButton(text = "Игра", web_app=WebAppInfo(url='https://habr.com')))
    builder.adjust(1)  # Устанавливаем количество кнопок в ряду
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if await user_exists(user_id):
        main_keyboard = create_main_keyboard()
        await message.answer("Привет!", reply_markup=main_keyboard)
    else:
        team_keyboard = create_team_keyboard()
        await message.answer("Привет! Выберите команду для участия:", reply_markup=team_keyboard)


# @dp.message(F.text == "Мой профиль")
# async def my_profile(message: types.Message):
#     user_id = message.from_user.id
#     profile = await get_user_profile(user_id)
#     if profile:
#         response = (
#             f"Ваш профиль:\n"
#             f"Имя пользователя: {profile['username']}\n"
#             f"Имя: {profile['first_name']}\n"
#             f"Личные очки: {profile['points']}\n"
#             f"Команда: {profile['team_name']}\n"
#             f"Очки команды: {profile['team_points']}\n"
#         )
#     else:
#         response = "Ваш профиль не найден. Пожалуйста, выберите команду."
#
#     await message.answer(response)

@dp.message(F.text == "Мой профиль")
async def my_profile(message: types.Message):
    user_id = message.from_user.id
    profile = await get_user_profile(user_id)

    if profile:
        response = (
            f"Ваш профиль:\n\n"
            f"👤 Имя пользователя: {profile['username']}\n"
            f"📛 Имя: {profile['first_name']}\n"
            f"🏅 Личные очки: {profile['points']}\n"
            f"🎌 Команда: {profile['team_name']}\n"
            f"🏆 Очки команды: {profile['team_points']}\n"
        )

        image_path = "images/mem_cup.jpg"
        photo = FSInputFile(image_path)
        # await message.answer_photo(photo, caption="caption")

        if os.path.exists(image_path):
            await message.answer_photo(photo, caption=response)
        else:
            await message.answer(response, parse_mode=ParseMode.HTML)
    else:
        response = "Ваш профиль не найден. Пожалуйста, выберите команду."
        await message.answer(response, parse_mode=ParseMode.HTML)

@dp.message(F.text == "photo")
async def return_photo(message: types.Message):
    image_path = "images/mem_cup.jpg"
    photo = FSInputFile(image_path)
    await message.answer_photo(photo=photo, caption="caption")

@dp.message(F.text == "Рейтинговая таблица")
async def rating_table(message: types.Message):
    rating = await get_rating_table()
    if rating:
        response = "Рейтинговая таблица команд:\n\n"
        for i, team in enumerate(rating, start=1):
            if i == 1:
                emoji = "🥇"
            elif i == 2:
                emoji = "🥈"
            elif i == 3:
                emoji = "🥉"

            else:
                emoji = "⭐️"  # Можно выбрать другой смайлик для остальных мест
            response += f"{emoji}{i}. {team['team_name']} - {team['team_points']} очков\n"
    else:
        response = "Рейтинговая таблица пуста."

    image_path = "images/mem_cup.jpg"
    photo = FSInputFile(image_path)

    await message.answer_photo(photo, caption=response)


@dp.message(F.text == "Играть")
async def play_game(message: types.Message):
    user_id = message.from_user.id
    user = await get_user_profile(user_id)
    if user:
        # game_url = create_game_url(user_id, user['team_id'])
        game_url = create_game_url()
        await message.answer(f"Вы можете играть по [этой ссылке]({game_url})", parse_mode="Markdown")
    else:
        team_keyboard = create_team_keyboard()
        await message.answer("Вы еще не выбрали команду. Пожалуйста, выберите команду для игры:", reply_markup=team_keyboard)


@dp.callback_query(F.data.startswith('team_'))
async def cmd_team_selected(callback: types.CallbackQuery):
    team_number = int(callback.data.split('_')[-1])
    await add_user(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        team_id=team_number
    )
    await callback.message.edit_text(f"Вы присоединились к команде {COMANDS_NAME[int(team_number)-1]}")


# async def update_score_on_server(user_id: int, username: str, team_name: str, score: int):
#     url = "http://web-app.com/update_score"
#     data = {
#         "user_id": user_id,
#         "username": username,
#         "team_name": team_name,
#         "score": score
#     }
#     response = requests.post(url, json=data)
#     response.raise_for_status()


async def on_startup():
    await init_db()
    await create_teams()

async def main():
    await on_startup()
    await dp.start_polling(bot)


asyncio.run(main())