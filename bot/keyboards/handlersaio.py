import json
import sys
import os
import types

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, message_id, CallbackQuery, InlineKeyboardButton, \
    InputFile, FSInputFile, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import io
from PIL import Image

import text
import config
sys.path.insert(1, os.path.join(sys.path[0], 'D:/УНИВЕР/практика/проба/code/bot/database'))
from model import Request

sys.path.insert(1, os.path.join(sys.path[0], 'D:/УНИВЕР/практика/проба/code/bot/database'))
from db_service import DatabaseService
sys.path.insert(1, os.path.join(sys.path[0], 'D:/УНИВЕР/практика/проба/code/bot/services'))
from controller import Controller
sys.path.insert(1, os.path.join(sys.path[0], 'D:/УНИВЕР/практика/проба/code/bot/utils'))
import json_parser
all_media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'all_media')


router = Router()
db_service = DatabaseService(config.DB_USER, config.DB_PASSWORD)
controller = Controller()
class Form(StatesGroup):
     groups = State()
     processing = State()

@router.message(Command("start"))
async def start_handler(message: Message):
    print("Start command received")
    user_id = message.from_user.id
    username = message.from_user.username
    if not await db_service.get_user(user_id):
        await db_service.add_user(user_id, username, 'user')
    user = await db_service.get_user(user_id)
    if user.role_id == 1:
        kb = [[KeyboardButton(text='История\U0001F4D6'),
              KeyboardButton(text='Избранное\U00002763'),
              KeyboardButton(text='Аккаунт\U0001F921'),
              KeyboardButton(text='Навигация\U0001F5FA')]]
        user_keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Добро пожаловать {username}! Если хочешь получить анализ комментариев, скинь ссылку на видео YouTube!", reply_markup=user_keyboard)


@router.message(F.text.regexp(r'https?://(?:www\.)?youtube\.com/watch\?v=\w+') & ~F.text.startswith('start'))
async def message_handler(message: Message, state: FSMContext):
    video_link = message.text
    message_id = message.message_id
    user_id = message.from_user.id
    chat_id = message.chat.id
    request = db_service.get_request_by_url(video_link)
    await state.update_data(video_link=video_link)
    await state.update_data(url_message_id=message_id)
    await state.update_data(user_id=user_id)
    await state.update_data(chat_id=chat_id)
    video_info_json = await controller.get_video_info(video_url=video_link)
    title, formatted_date_time, views, likes, comments = json_parser.parse_video_inf(video_info_json)
    await state.update_data(video_info=video_info_json)
    if request is not None:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Построить анализ по характеристикам из БД (1 токен)", callback_data="get_from_db"))
        builder.row(InlineKeyboardButton(text="Обновить характеристики и построить анализ (1 токен)", callback_data="get_video_info"))
        builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
        msg = await message.answer(
            text.video_info_text.format(
                title, formatted_date_time, likes, comments, views
            ),
            reply_markup=builder.as_markup(),
        )
        await state.update_data(request_message=msg)
    else:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Запросить анализ видео (1 токен)", callback_data="get_video_info"))
        builder.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
        msg = await message.answer(text.video_info_text.format(title, formatted_date_time, likes, comments, views),
                                   reply_markup=builder.as_markup())
        await state.update_data(request_message=msg)



@router.callback_query(F.data == "get_from_db")
async def get_from_db_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    video_link = data.get("video_link")
    request_msg = data["request_message"]
    await callback_query.message.edit_reply_markup(reply_markup=None)
    processing_msg = await callback_query.message.answer(
        f"Идет обработка данных...:"
    )
    try:
        await state.update_data(processing_msg_id=processing_msg.message_id)

        await state.set_state(Form.processing)
        request = Request()
        request = db_service.get_request_by_url(video_link)
        characteristics = json_parser.get_characteristics(request.characteristics)
        await state.update_data(characteristics=characteristics)
        await processing_msg.edit_text(
            f"Выделено {len(characteristics)} характеристик, введите количество групп от 2 до {len(characteristics) - 1}"
        )
        await state.set_state(Form.groups)
        await state.update_data(source="db")
    except Exception as e:
        # Обработка других ошибок
        await callback_query.message.answer(
            f"Не удалось обработать данные. Поробуйте еще раз."
        )


@router.callback_query(F.data == "get_video_info")
async def get_video_info(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    video_link = data.get("video_link")
    request_msg = data["request_message"]
    await callback_query.message.edit_reply_markup(reply_markup=None)
    processing_msg = await callback_query.message.answer(
        f"Идет обработка данных...:"
    )
    try:
        await state.update_data(processing_msg_id=processing_msg.message_id)

        await state.set_state(Form.processing)

        characteristics = await controller.get_characteristics_from_chat(video_link)
        await state.update_data(characteristics=characteristics)
        await processing_msg.edit_text(
            f"Выделено {len(characteristics)} характеристик, введите количество групп от 2 до {len(characteristics) - 1}"
        )
        await state.set_state(Form.groups)
        await state.update_data(source="new")
    except Exception as e:
        # Обработка других ошибок
        await callback_query.message.answer(
            f"Не удалось обработать данные. Поробуйте еще раз."
        )
    # await state.update_data(callback_query=callback_query)
    # controller.get_json_groups_from_chat()

@router.callback_query(F.data == "get_group")
async def get_group(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    json_group = data.get("json_group")
    video_info_json = data.get("video_info")
    user_id = data.get("user_id")
    group_name = callback_query.data.split(":")[1]

    # Находим нужную группу в json_group
    group = next((g for g in json_group["groups"] if g["group"] == group_name), None)
    if not group:
        await callback_query.answer("Ошибка: группа не найдена", show_alert=True)
        return

    # Вызываем метод из контроллера для обработки группы
    graph_data = await controller.get_main_group_graph(json_group, group_name, video_info_json)
    graph_data.write_image(
        file=os.path.join(all_media_dir, f'graph_bubble_negat_{user_id}.png'), width=1800,
        height=800)
    photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_bubble_posit_{user_id}.png'))
    await callback_query.answer_photo(photo=photo_file)

    # # Добавляем кнопку "Назад"
    # keyboard = InlineKeyboardMarkup(row_width=1)
    # back_button = InlineKeyboardButton("Назад", callback_data="back")
    # keyboard.add(back_button)
    # # Сохраняем название группы в state
    # await state.update_data(current_group=group_name)


@router.message(Form.processing)
async def processing_handler(message: Message, state: FSMContext):
    await message.delete()


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    request_msg = data["request_message"]
    await request_msg.edit_text(request_msg.text, reply_markup=None)
    await callback_query.message.answer(
        f"Операция отменена")


@router.message(Form.groups)
async def groups_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    characteristics =  data.get("characteristics")
    if not message.text.isdigit():
        await state.set_state(Form.groups)
        await message.answer(f"Я вас не понял. Введите любое число от 2 до {(len(characteristics)-1)}")
    else:
        num_groups = int(message.text)
        data = await state.get_data()
        if num_groups >= 2 and num_groups <= (len(characteristics)-1):
            await state.update_data(groups=num_groups)
            msg = await message.answer(f"Идет обработка для {num_groups} групп...")
            video_link = data.get("video_link")
            video_info_json = data.get("video_info")
            user_id = data.get("user_id")
            message_id = data.get("message_id")
            if message_id is None:
                message_id = -1
            source = data.get("source")
            if source == "db":
                json_group = await controller.get_json_groups_existed(characteristics, num_groups)
                await state.update_data(json_group=json_group)
                db_characteristics = json_parser.add_count_group_to_characteristics(characteristics, num_groups)
                db_service.add_request(user_id, video_link, video_info_json, message_id, db_characteristics, "ой")
            elif source == "new":
                json_group = await controller.get_json_groups_existed(characteristics, num_groups)
                await state.update_data(json_group=json_group)
                db_characteristics = json_parser.add_count_group_to_characteristics(characteristics, num_groups)
                db_service.add_request(user_id, video_link, video_info_json, message_id, db_characteristics, "ой")
            if json_group:
                groups = json_parser.parse_groups(json_group)
                groups_text = "\n".join([f"Группа: {name}\nОписание: {description}\n" for name, description in groups])
                builder = InlineKeyboardBuilder()
                builder.row(
                    InlineKeyboardButton(text="Добавить в избранноe", callback_data="add_to_favorites"))
                msg = await message.answer(
                    f"По характеристикам были выделены следующие группы:\n\n{groups_text}",
                    reply_markup=builder.as_markup(),
                )
                await state.update_data(request_message=msg)
                await build_and_send_graphs(json_group, video_info_json, user_id, message)
            else:
                await message.answer("Ошибка при получении данных.")
        else:
            await state.set_state(Form.groups)
            await message.answer(f"Я вас не понял. Введите любое число от 3 до 50:")

async def build_and_send_graphs(json_group, video_info_json, user_id, message):

    graph_data = await controller.get_main_general_graph(json_group, video_info_json)
    graph_bubble_posit = await controller.get_general_positive_bubble_graph(json_group, video_info_json)
    graph_bubble_negat = await controller.get_general_negative_bubble_graph(json_group, video_info_json)
    if graph_data and graph_bubble_posit and graph_bubble_negat:
        graph_data.write_image(
            file=os.path.join(all_media_dir, f'graph_data_{user_id}.png'), width=1800,
            height=800)
        graph_bubble_posit.write_image(
            file=os.path.join(all_media_dir, f'graph_bubble_posit_{user_id}.png'), width=1800,
            height=800)
        graph_bubble_negat.write_image(
            file=os.path.join(all_media_dir, f'graph_bubble_negat_{user_id}.png'), width=1800,
            height=800)
        photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_bubble_posit_{user_id}.png'))
        await message.answer_photo(photo=photo_file)
        photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_bubble_negat_{user_id}.png'))
        await message.answer_photo(photo=photo_file)
        photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_data_{user_id}.png'))
        group_buttons = await build_group_buttons(json_group)
        await message.answer_photo(photo=photo_file, reply_markup=group_buttons)
    else:
        await message.answer("Ошибка при создании графика.")

async def build_group_buttons(json_group: dict) -> InlineKeyboardMarkup:
    buttons = {}
    for group in json_group["groups"]:
        button = InlineKeyboardButton(text=group["group"], callback_data=f"group:{group['group']}")
        buttons[group["group"]] = button
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[[buttons[group]] for group in buttons])

@router.callback_query(F.data == "add_to_favorites")
async def add_to_favorites(callback_query: CallbackQuery, state: FSMContext):
    # data = await state.get_data()
    # json_group = data.get("json_group")
    # video_info_json = data.get("video_info")
    # user_id = data.get("user_id")
    # video_link = data.get("video_link")
    # request = Request()
    # request = db_service.get_request_by_url(video_link)
    # db_service.change_favourite(request.id, True)
    await callback_query.answer("Группы успешно добавлены в избранное!")

