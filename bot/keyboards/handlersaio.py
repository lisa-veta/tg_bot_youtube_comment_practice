import sys
import os
import types

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, message_id, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


import text
import config

sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/Королева/PycharmProjects/tg_youtube_analytics/bot/database'))
from db_service import DatabaseService
sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/Королева/PycharmProjects/tg_youtube_analytics/bot/services'))
from controller import Controller
sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/Королева/PycharmProjects/tg_youtube_analytics/bot/utils'))
import json_parser


router = Router()
db_service = DatabaseService(config.DB_USER, config.DB_PASSWORD)
controller = Controller()
class Form(StatesGroup):
     groups = State()

@router.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    if not db_service.user_exist(user_id):
        db_service.add_user(user_id, username)
    user = db_service.get_user(user_id)
    if user.role_id == 1:
        kb = [[KeyboardButton(text='История\U0001F4D6'),
              KeyboardButton(text='Избранное\U00002763'),
              KeyboardButton(text='Аккаунт\U0001F921'),
              KeyboardButton(text='Навигация\U0001F5FA')]]
        user_keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Добро пожаловать {username}!", reply_markup=user_keyboard)

@router.message(F.text.regexp(r'https?://(?:www\.)?youtube\.com/watch\?v=\w+'))
async def message_handler(message: Message, state: FSMContext):
    video_link = message.text
    message_id = message.message_id
    user_id = message.from_user.id
    db_service.add_request(user_id, video_link, message_id)
    await state.set_state(Form.groups)
    await message.answer(f"На сколько групп хотите разделить характеристики? Введите любое число от 3 до 50:")

@router.message(Form.groups)
async def groups_handler(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await state.set_state(Form.groups)
        await message.answer(f"Я вас не понял. Введите любое число от 3 до 50:")
    else:
        num_groups = int(message.text)
        if num_groups >= 3 and num_groups <= 50:
            await state.update_data(groups=num_groups)
            user_id = message.from_user.id
            request = db_service.get_request_by_user_id(user_id)
            video_info_json = controller.get_video_info(video_url=request.video_url)
            title, formatted_date_time, views, likes, comments = json_parser.parse_video_inf(video_info_json)
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="Запросить анализ видео", callback_data="get_video_info"))
            msg = await message.answer(text.video_info_text.format(title, formatted_date_time, likes, comments, views),
                                    reply_markup=builder.as_markup())
            await state.update_data(message=msg)

        else:
            await state.set_state(Form.groups)
            await message.answer(f"Я вас не понял. Введите любое число от 3 до 50:")

@router.callback_query(F.data == "get_video_info")
async def get_video_info(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    group_counter = data["groups"]
    request_msg = data["message"]
    await request_msg.edit_text(request_msg.text, reply_markup=None)
    msg = await callback_query.message.answer(f"Окей, идет обработка для {group_counter} групп...")
    # controller.get_json_groups_from_chat()
