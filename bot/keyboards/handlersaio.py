import functools
import json
import sys
import os
import types
import asyncio
import concurrent.futures
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, message_id, CallbackQuery, InlineKeyboardButton, \
    InputFile, FSInputFile, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
import io
from PIL import Image

import text
import config
sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/vladi/PycharmProjects/tg_youtube_analytics/bot/database'))
from model import Request

sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/vladi/PycharmProjects/tg_youtube_analytics/bot/database'))
from db_service import DatabaseService
sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/vladi/PycharmProjects/tg_youtube_analytics/bot/services'))
from controller import Controller
sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/vladi/PycharmProjects/tg_youtube_analytics/bot/utils'))
import json_parser
all_media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'all_media')


router = Router()
db_service = DatabaseService(config.DB_USER, config.DB_PASSWORD)

controller = Controller()
class Form(StatesGroup):
     groups = State()
     processing = State()
     new_groups = State()
     comment_parts = State()
     new_groups_from_main = State()
     groups_from_favourite = State()
     token_requests = State()

from collections import deque

# class RequestQueue:
#    def __init__(self):
#        self.queue = deque()
#
#    async def put(self, request):
#        self.queue.append(request)
#        await self.process_queue()
#
#    async def process_queue(self):
#        while self.queue:
#            characteristics, num_groups = self.queue.popleft()
#            json_group = await controller.get_json_groups_existed(characteristics, num_groups)
#            return json_group
#
# request_queue = RequestQueue()


@router.message(Command("start"))
async def start_handler(message: Message):
    await db_service.create_engine()
    print("Start command received")
    user_id = message.from_user.id
    username = message.from_user.username
    if not await db_service.get_user(user_id):
        await db_service.add_user(user_id, username, 'user')
    user = await db_service.get_user(user_id)
    kb = [[KeyboardButton(text='История\U0001F4D6'),
           KeyboardButton(text='Избранное\U00002763'),
           KeyboardButton(text='Аккаунт\U0001F9DA'),
           KeyboardButton(text='Навигация\U0001F5FA')]]
    if user.role_id == 1:
        user_keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    elif user.role_id == 2:
        kb.append([KeyboardButton(text='Админ\U0001F6AA')])
        user_keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        f"Добро пожаловать {username}! Если хочешь получить анализ комментариев, скинь ссылку на видео YouTube!\n\n"
        f"Для более быстрой проверки работы бота воспользуйтесь видео, которые есть в хранилище:\n\n"
        f"БЕЗ СУФЛЕРА: как сэкономить на квартире? Медведи в опасности? О чем мечтает Дукалис?\n"
        f"https://www.youtube.com/watch?v=PgGsS5R_t3g\n\n"
        f"[BadComedian] - ЗОЯ (Спасение рядового ИИСУСА)\n"
        f"https://www.youtube.com/watch?v=nIkH6C3_CX8\n\n"
        f"Что Будет с Телом, Если Заниматься Спортом Каждый День\n"
        f"https://www.youtube.com/watch?v=Jp4SB_lOu8E\n\n"
        f"Скопируйте ссылку и отправьте ее боту!",
        reply_markup=user_keyboard
    )


@router.message(F.text == 'История\U0001F4D6')
async def get_history_requests(message: Message):
    await db_service.create_engine()
    user_id = message.from_user.id
    history = await db_service.get_request_by_id_20(user_id)
    video_in_history = []
    if len(history) != 0:
        for request in history:
            video_in_history.append(f"/{request.message_id} {request.video_information['title']} от {request.datetime.strftime('%d.%m.%Y %H:%M:%S')}")
        history_text = '\n'.join(video_in_history)
        await message.answer(history_text)
    else:
        await message.answer("В истории пока что нет ни одного запроса")

@router.message(F.text == 'Избранное\U00002763')
async def goto_favoutite_menu(message: Message, state: FSMContext):
    await db_service.create_engine()
    user_id = message.from_user.id
    favourites = await db_service.get_user_favourites(user_id)
    if len(favourites) != 0:
        video_in_favourite_button = InlineKeyboardBuilder()
        favourite_videos_m_id = []
        for video in favourites:
            video_in_favourite_button.row(InlineKeyboardButton(text=str(video.video_information['title']), callback_data='favourite_' + str(video.message_id)))
            favourite_videos_m_id.append(video.message_id)
        await state.update_data(favourites_video_m_id=favourite_videos_m_id)
        msg = await message.answer("Видео, которые вы добавили в избранное:", reply_markup=video_in_favourite_button.as_markup())
        await state.update_data(favs_msg_id=message.message_id)
    else:
        await message.answer("Вы еще не добавили ни одного видео в избранное")

@router.callback_query(F.data.startswith('favourite_'))
async def favourite_handler(callback_query: CallbackQuery, state: FSMContext, m_id=None):
    await db_service.create_engine()
    if m_id is None:
        m_id = int(callback_query.data[10:])
    user_id = callback_query.from_user.id
    request = await db_service.get_user_favourite_by_m_id(user_id, m_id)
    request = request[0]
    title = request['title']
    views = request['viewCount']
    likes = request['likeCount']
    comments = request['commentCount']
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Просмотреть анализ видео", callback_data=f"favorite_video_anal_{m_id}"))
    builder.row(InlineKeyboardButton(text="Обновить характеристики и построить анализ (1 токен)", callback_data="get_video_info"))
    builder.row(InlineKeyboardButton(text="Удалить видео из избранного", callback_data=f"delete_favourite_{m_id}"))
    builder.row(InlineKeyboardButton(text="<< Назад в избранное", callback_data="back_to_fav"))
    msg = await callback_query.message.edit_text(
        text.video_info_text_in_fav.format(
            title, likes, comments, views
        ), reply_markup=builder.as_markup(),
    )
    await state.update_data(request_message=msg)
@router.callback_query(F.data.startswith('favorite_video_anal_'))
async def favorite_video_handler(callback_query: CallbackQuery):
    m_id = int(callback_query.data[20:])
    try:
        await callback_query.message.answer(
            text="Перейдите по ответу, чтобы посмотреть информацию по запросу",
            reply_to_message_id=m_id
        )
    except Exception as e:
        await callback_query.message.answer("Я вас не понял.")
@router.callback_query(F.data.startswith("delete_favourite_"))
async def delete_favourite(callback_query: CallbackQuery):
    m_id = int(callback_query.data[17:])
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да", callback_data=f"delete_yes_{m_id}"))
    builder.row(InlineKeyboardButton(text="Нет", callback_data=f"delete_no_{m_id}"))
    msg = await callback_query.message.edit_text("Вы уверены, что хотите удалить видео из избранного?",
                                                 reply_markup=builder.as_markup())
@router.callback_query(F.data.startswith('delete_yes_'))
async def delete_yes(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    m_id = int(callback_query.data[11:])
    await db_service.create_engine()
    await db_service.change_favourite_flag(m_id, False)
    favourites = await db_service.get_user_favourites(user_id)
    if len(favourites) != 0:
        await return_to_fav(callback_query, state)
    else:
        await callback_query.message.edit_text("В избранном пусто")

@router.callback_query(F.data.startswith("delete_no_"))
async def delete_no(callback_query: CallbackQuery, state: FSMContext):
    m_id = int(callback_query.data[10:])
    await favourite_handler(callback_query, state, m_id)
@router.callback_query(F.data =="back_to_fav")
async def return_to_fav(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    favourites = await db_service.get_user_favourites(user_id)
    if len(favourites) != 0:
        video_in_favourite_button = InlineKeyboardBuilder()
        favourite_videos_m_id = []
        for video in favourites:
            video_in_favourite_button.row(InlineKeyboardButton(text=str(video.video_information['title']),
                                                               callback_data='favourite_' + str(video.message_id)))
            favourite_videos_m_id.append(video.message_id)
        await state.update_data(favourites_video_m_id=favourite_videos_m_id)
        msg = await callback_query.message.edit_text("Видео, которые вы добавили в избранное:",
                                                     reply_markup=video_in_favourite_button.as_markup())
    else:
        await callback_query.message.answer("Вы еще не добавили ни одного видео в избранное")

@router.message(F.text == "Админ\U0001F6AA")
async def admin_handler(message: Message, state: FSMContext):
    kb = [[KeyboardButton(text='Управление пользователями\U0001F465'),
           KeyboardButton(text='Статистика БД\U0001F418\U0001F4CA'),
           KeyboardButton(text='Выдать токены\U0001F4B8'),],
          [KeyboardButton(text='Выйти из режима администрирования\U0001F6AA')]]
    admin_keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Рады приветствовать вас в панели администрирования! Выберите одну из предложенных кнопок!", reply_markup=admin_keyboard)

@router.message(F.text == "Управление пользователями\U0001F465")
async def manage_user_handler(message: Message, state: FSMContext):
    await state.update_data(manage_message=message)
    #Create keyboard
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Просмотреть пользователей", callback_data="view_users"))
    builder.row(InlineKeyboardButton(text="Статистика посещений пользователей", callback_data="s"))
    builder.row(InlineKeyboardButton(text="Статистика новых пользователей", callback_data="st"))
    await message.answer("<b>Управление пользователем</b>", reply_markup=builder.as_markup())

@router.callback_query(F.data == "view_users")
async def view_all_users(callback_query: CallbackQuery, state: FSMContext, index=0):
    await db_service.create_engine()
    await state.update_data(view_callback=callback_query)

    # Получениe текущего user
    users = await db_service.get_users()
    await state.update_data(index=index)
    user = users[index]
    await state.update_data(user=user)

    # Получение данных для отображения
    user_id = user.id
    username = user.username
    role_id = user.role_id
    role = await db_service.get_role(role_id)
    token_balance = user.token_balance
    date_registration = user.date_registration

    # Создание инлайн клавиатуры
    builder = InlineKeyboardBuilder()
    if len(users) == 1:
        pass
    elif index == 0:
        builder.row(InlineKeyboardButton(text=">", callback_data="next_user"))
    elif index == len(users) - 1:
        builder.row(InlineKeyboardButton(text="<", callback_data="previous_user"))
    else:
        builder.row(InlineKeyboardButton(text="<", callback_data="previous_user"),
                    InlineKeyboardButton(text=">", callback_data="next_user"))

    if role_id == 3:
        builder.row(InlineKeyboardButton(text="Разбанить", callback_data="unban"))
    elif role_id == 1:
        builder.row(InlineKeyboardButton(text="Бан", callback_data="ban"))
        builder.row(InlineKeyboardButton(text="Сделать администратором", callback_data="make_admin"))

    builder.row(InlineKeyboardButton(text="Начисление токенов", callback_data="add_tokens"))
    builder.row(InlineKeyboardButton(text="Статистика", callback_data="statistics"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="back_to_manage"))

    await callback_query.message.edit_text(
        text=text.user_text.format(index + 1, len(users), username, user_id, role, token_balance, date_registration),
        reply_markup=builder.as_markup())

@router.callback_query(F.data == "previous_user")
async def switch_to_previous(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data["index"] - 1
    await view_all_users(callback_query, state, index)


@router.callback_query(F.data == "next_user")
async def switch_to_next(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data["index"] + 1
    await view_all_users(callback_query, state, index)

@router.callback_query(F.data == "ban")
async def switch_to_next(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data["index"]
    user = data["user"]
    await db_service.ban(user.id)
    await callback_query.answer("Пользователь заблокирован")
    await view_all_users(callback_query, state, index)

@router.callback_query(F.data == "unban")
async def switch_to_next(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data["index"]
    user = data["user"]
    await db_service.unban(user.id)
    await callback_query.answer("Пользователь разблокирован")
    await view_all_users(callback_query, state, index)

@router.callback_query(F.data == "make_admin")
async def switch_to_next(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data["index"]
    user = data["user"]
    await db_service.make_admin(user.id)
    await callback_query.answer("Пользователь теперь - Администратор!")
    await view_all_users(callback_query, state, index)

@router.callback_query(F.data == "back_to_manage")
async def back(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message = data["manage_message"]
    await callback_query.message.delete()
    await manage_user_handler(message, state)

@router.callback_query(F.data == "add_tokens")
async def add_tokens(callback_query: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="5", callback_data="give_token_5"),
                 InlineKeyboardButton(text="7", callback_data="give_token_7"),
                 InlineKeyboardButton(text="10", callback_data="give_token_10"))
    keyboard.row(InlineKeyboardButton(text="<< Назад", callback_data="back_to_ac"))
    msg = await callback_query.message.edit_text("Сколько токенов выдать?", reply_markup=keyboard.as_markup())
    await state.update_data(ac_msg_id=msg.message_id)

@router.callback_query(F.data.startswith('give_token_'))
async def request_token(callback_query: CallbackQuery, state: FSMContext):
    await db_service.create_engine()
    data = await state.get_data()

    user = data["user"]
    index = data["index"]
    amount = int(callback_query.data[11:])
    try:
        await db_service.add_tokens(user.id, amount)
        await callback_query.answer(f"{amount} токенов добавлено пользователю {user.username}.")
        await view_all_users(callback_query, state, index)
    except Exception as e:
        await callback_query.answer(f"Ошибка: {e}", show_alert=True)



@router.message(F.text == "Статистика БД\U0001F418\U0001F4CA")
async def statistic_handler(message: Message, state: FSMContext):
    await message.answer("Статистика БД:)")

@router.message(F.text == "Выдать токены\U0001F4B8")
async def token_handler(message: Message, state: FSMContext, index=0):
    await db_service.create_engine()
    start_message = 0
    if message.text == "Выдать токены\U0001F4B8":
        start_message = message

    #Получения текущего токен реквеста
    token_requests = await db_service.get_token_requests()
    await state.update_data(index=index)
    if len(token_requests) == 0:
        if message == start_message:
            await message.answer("Запросов на получение токенов нет :(")
            return
        else:
            await message.edit_text("Запросов на получение токенов нет :(")
            return
    token_request = token_requests[index]
    await state.update_data(token_request=token_request)

    #Получение данных для отображения
    user_id = token_request.user_id
    username = await db_service.get_username(user_id)
    amount = token_request.amount
    date = token_request.datetime

    #Создание инлайн клавиатуры
    builder = InlineKeyboardBuilder()
    if len(token_requests) == 1:
        pass
    elif index == 0:
        builder.row(InlineKeyboardButton(text=">", callback_data="next_token_request"))
    elif index == len(token_requests) - 1:
        builder.row(InlineKeyboardButton(text="<", callback_data="previous_token_request"))
    else:
        builder.row(InlineKeyboardButton(text="<", callback_data="previous_token_request"),
                    InlineKeyboardButton(text=">", callback_data="next_token_request"))
    builder.row(InlineKeyboardButton(text="Подтвердить", callback_data="accept_token_request"))
    builder.row(InlineKeyboardButton(text="Отклонить", callback_data="cancel_token_request"))

    if message == start_message:
        await message.answer(text.token_request_text.format(index + 1, len(token_requests), username, amount, date), reply_markup=builder.as_markup())
    else:
        await message.edit_text(text.token_request_text.format(index + 1, len(token_requests), username, amount, date), reply_markup=builder.as_markup())

@router.callback_query(F.data == "previous_token_request")
async def switch_to_previous(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data["index"] - 1
    await token_handler(callback_query.message, state, index)


@router.callback_query(F.data == "next_token_request")
async def switch_to_next(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data["index"] + 1
    await token_handler(callback_query.message, state, index)

@router.callback_query(F.data == "accept_token_request")
async def accept_token_req(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token_request = data["token_request"]
    token_request_id = token_request.id
    await db_service.accept_token_request(token_request_id)
    await callback_query.answer("Токены начислены")
    await token_handler(callback_query.message, state)

@router.callback_query(F.data == "cancel_token_request")
async def cancel_token_req(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    token_request = data["token_request"]
    token_request_id = token_request.id
    await db_service.delete_token_request(token_request_id)
    await callback_query.answer("Запрос отклонен")
    await token_handler(callback_query.message, state)


@router.message(F.text.regexp(r'https?://(?:www\.)?youtube\.com/watch\?v=\w+') & ~F.text.startswith('start'))


@router.message(F.text == 'Аккаунт\U0001F9DA')
async def goto_favoutite_menu(message: Message, state: FSMContext):
    await db_service.create_engine()
    user_id = message.from_user.id
    user = await db_service.get_user(user_id)
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Купить токены",callback_data="buy_token"))
    await message.answer(text.account_text.format(user.token_balance, user.date_registration),
                         reply_markup=keyboard.as_markup())
@router.callback_query(F.data == 'buy_token')
async def buy_token(callback_query: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="5",callback_data="buy_token_5"),
                 InlineKeyboardButton(text="7", callback_data="buy_token_7"),
                 InlineKeyboardButton(text="10", callback_data="buy_token_10"))
    keyboard.row(InlineKeyboardButton(text="<< Назад", callback_data="back_to_ac"))
    msg = await callback_query.message.edit_text("Сколько токенов запросить?", reply_markup=keyboard.as_markup())
    await state.update_data(ac_msg_id=msg.message_id)
@router.callback_query(F.data.startswith('buy_token_'))
async def request_token(callback_query: CallbackQuery, state: FSMContext):
    await db_service.create_engine()
    user_id = callback_query.from_user.id
    token_request = int(callback_query.data[10:])
    try:
        await db_service.add_token_request(user_id, token_request)
        await callback_query.message.edit_text(
            f"Ваш запрос на {token_request} токенов отправлен на рассмотрение к администратору."
        )
    except Exception as e:
        await callback_query.answer(f"Ошибка: {e}", show_alert=True)
@router.callback_query(F.data == "back_to_ac")
async def back_to_ac(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg = data["ac_msg_id"]
    await callback_query.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=msg)
    await db_service.create_engine()
    user_id = callback_query.from_user.id
    user = await db_service.get_user(user_id)
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Купить токены", callback_data="buy_token"))
    await callback_query.message.answer(text.account_text.format(user.role_id, user.token_balance, user.date_registration),
                         reply_markup=keyboard.as_markup())

@router.message(
    (F.text.regexp(r'https?://(?:www\.)?youtube\.com/watch\?v=\w+') |
     F.text.regexp(r'https?://youtu\.be/\w+'))
    & ~F.text.startswith('start')
)
async def message_handler(message: Message, state: FSMContext):
    await db_service.create_engine()
    video_link = message.text
    message_id = message.message_id
    user_id = message.from_user.id
    chat_id = message.chat.id
    request = await db_service.get_request_by_url(video_link)
    await state.update_data(video_link=video_link)
    await state.update_data(url_message_id=message_id)
    await state.update_data(user_id=user_id)
    await state.update_data(chat_id=chat_id)
    video_info_json = await controller.get_video_info(video_url=video_link)
    title, formatted_date_time, views, likes, comments = await json_parser.parse_video_inf(video_info_json)
    await state.update_data(video_info=video_info_json)
    if request is not None:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Взять характеристики из хранилища (1 токен)", callback_data="get_from_db"))
        builder.row(InlineKeyboardButton(text="Обновить характеристики (1 токен)", callback_data="get_video_info"))
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
    await db_service.create_engine()
    can_request = await db_service.can_request(callback_query.from_user.id)
    if not can_request:
        await callback_query.answer("Недостаточно токенов. Проверьте баланс в разделе \"Аккаунт\"")
        return
    data = await state.get_data()
    video_link = data.get("video_link")
    request_msg = data["request_message"]
    await callback_query.message.edit_reply_markup(reply_markup=None)
    processing_msg = await callback_query.message.answer(
        f"Идет обработка данных..."
    )
    try:
        await state.update_data(processing_msg_id=processing_msg.message_id)

        await state.set_state(Form.processing)
        request = Request()
        request = await db_service.get_request_by_url(video_link)
        characteristics = await json_parser.get_characteristics(request.characteristics)
        await state.update_data(characteristics=characteristics)
        await processing_msg.edit_text(
            f"Выделено {len(characteristics)} характеристик, введите количество групп от 2 до {int((len(characteristics))/2)}"
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
    await db_service.create_engine()
    can_request = await db_service.can_request(callback_query.from_user.id)
    if not can_request:
        await callback_query.answer("Недостаточно токенов. Проверьте баланс в разделе \"Аккаунт\"")
        return
    data = await state.get_data()
    video_link = data.get("video_link")
    request_msg = data["request_message"]
    await callback_query.message.edit_reply_markup(reply_markup=None)
    processing_msg = await callback_query.message.answer(
        f"Идет обработка данных..."
    )
    try:
        await state.update_data(processing_msg_id=processing_msg.message_id)

        await state.set_state(Form.processing)
        video_info = data.get("video_info")
        comment_count = video_info['commentCount']
        await processing_msg.edit_text(
            f"В видео {comment_count} комментариев. \nВведите количество частей, на которые хотите разделить комментарии для последующего анализа.\n"
            f""
            f"\n(Будут проанализированы все части по очереди и подведен итог)"
        )
        await state.update_data(video_info=video_info)
        await state.set_state(Form.comment_parts)
        await state.update_data(source="new")
    except Exception as e:
        # Обработка других ошибок
        await callback_query.message.answer(
            f"Не удалось обработать данные. Попробуйте еще раз."
        )

@router.message(Form.comment_parts)
async def process_comment_parts(message: Message, state: FSMContext):
    data = await state.get_data()
    video_info = data.get("video_info")
    video_link = data.get("video_link")
    comment_count = int(video_info['commentCount'])
    try:
        parts = int(message.text)
        if parts < 1 or parts > comment_count:
            raise ValueError(f"Введите число от 1 до {comment_count}.")
    except ValueError as e:
        await state.set_state(Form.comment_parts)
        await message.answer(f"Я вас не понял. Введите число от 1 до {comment_count}.")
        return
    processing_msg = await message.answer(
        f"Идет обработка данных..."
    )
    await state.update_data(comment_parts=parts)
    await state.update_data(source="new")
    async def process_data(message):
        characteristics = await controller.get_characteristics_from_chat(video_link, parts)
        await state.update_data(characteristics=characteristics)
        await processing_msg.edit_text(
            f"По вашему запросу выделено {len(characteristics)} характеристик. \nВведите количество групп, "
            f"на которые хотите кластеризировать характеристики: значение от 2 до {int((len(characteristics))/2)}"
        )
        await state.set_state(Form.groups)

    await asyncio.create_task(process_data(message))

@router.callback_query(F.data.startswith("get_group:"))
async def get_group(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    json_group = data.get("json_group")
    video_info_json = data.get("video_info")
    user_id = data.get("user_id")
    new_groups = data.get("new_groups")
    group_name = callback_query.data.split(":")[1]
    try:
        count_of_characteristics = await json_parser.get_count_characteristics_from_groups(new_groups, group_name)
        if count_of_characteristics > 12:
            await callback_query.message.delete()
            processing_msg = await callback_query.message.answer(
                f"По вашему запросу выделено {count_of_characteristics} характеристик. \nВведите количество групп, "
            f"на которые хотите кластеризировать характеристики: значение от 2 до {int(count_of_characteristics/2)}"
            )
            await state.update_data(processing_msg_id=processing_msg.message_id)
            await state.set_state(Form.new_groups)
            await state.update_data(characteristics_count=count_of_characteristics)
            await state.update_data(curr_group_name=group_name)
            await state.update_data(callback_query=callback_query)
        else:
            await process_group_without_new_groups(callback_query.message, new_groups, group_name, video_info_json,
                                                   user_id)
    except Exception as e:
        try:
            count_of_characteristics = await json_parser.get_count_characteristics_from_groups(json_group, group_name)
            if count_of_characteristics >= 20:
                await callback_query.message.delete()
                processing_msg = await callback_query.message.answer(
                    f"В группе {group_name} {count_of_characteristics} характеристик. \nВведите количество групп, "
                    f"на которые хотите кластеризировать характеристики (значение от 2 до {int((count_of_characteristics) / 2)})"
                )
                await state.update_data(processing_msg_id=processing_msg.message_id)
                await state.set_state(Form.new_groups_from_main)
                await state.update_data(characteristics_count=count_of_characteristics)
                await state.update_data(first_group_name=group_name)
                await state.update_data(callback_query=callback_query)
            else:
                await process_group_without_new_groups(callback_query.message, json_group, group_name, video_info_json,
                                                       user_id)
        except Exception as e:
            group_name_f = data.get("first_group_name")
            await process_group_without_new_groups(callback_query.message, json_group, group_name_f, video_info_json, user_id)

async def process_new_groups(message: Message, new_groups, video_info_json, user_id, group_name):
    graph_data = await controller.get_main_general_graph(new_groups, video_info_json)
    if graph_data:
        graph_data.write_image(
            file=os.path.join(all_media_dir, f'graph_data_{user_id}.png'), width=2000,
            height=800)
        photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_data_{user_id}.png'))
        await message.answer_photo(
            photo=photo_file, caption=f"График для группы \"{group_name}\"",
            reply_markup=await build_group_buttons(new_groups, True)
        )
    else:
        await message.answer("Ошибка при создании графика.")

async def process_group_without_new_groups(message: Message, json_group, group_name, video_info_json, user_id):
    group = next((g for g in json_group["groups"] if g["group"] == group_name), None)
    if not group:
        await message.answer("Ошибка: группа не найдена", show_alert=True)
        return
    graph_data = await controller.get_main_group_graph(json_group, group_name, video_info_json)
    graph_data.write_image(
        file=os.path.join(all_media_dir, f'graph_main_group_{user_id}.png'), width=2000,
        height=800)
    photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_main_group_{user_id}.png'))
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Назад к главному графику", callback_data="back_to_main"))
    # Удаляем предыдущее сообщение
    await message.delete()
    # Отправляем новое сообщение с графиком и клавиатурой
    await message.answer_photo(
        photo=photo_file,
        caption=f"График по группе {group_name}",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_groups(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    json_group = data.get("json_group")
    video_info_json = data.get("video_info")
    user_id = data.get("user_id")
    graph_data = await controller.get_main_general_graph(json_group, video_info_json)
    if graph_data:
        graph_data.write_image(
            file=os.path.join(all_media_dir, f'graph_data_{user_id}.png'), width=1800,
            height=800)
        photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_data_{user_id}.png'))
        # Удаляем предыдущее сообщение
        await callback_query.message.delete()
        # Отправляем новое сообщение с графиком
        await callback_query.message.answer_photo(
            photo=photo_file, caption="Общий график",
            reply_markup=await build_group_buttons(json_group, False)
        )
    else:
        await callback_query.message.answer("Ошибка при создании графика.")

@router.message(Form.processing)
async def processing_handler(message: Message):
    await message.delete()


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    request_msg = data["request_message"]
    await request_msg.edit_text(request_msg.text, reply_markup=None)
    await callback_query.message.answer(
        f"Операция отменена")

@router.message(Form.new_groups)
async def groups_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    characteristics_count = data.get("characteristics_count")
    video_info_json = data.get("video_info")
    user_id = data.get("user_id")
    new_groups = data.get("new_groups")
    group_name = data.get("curr_group_name")
    group_name_f = data.get("first_group_name")
    if not message.text.isdigit():
        await state.set_state(Form.groups)
        await message.answer(f"Я вас не понял. Введите любое число от 2 до {int(characteristics_count / 2)}")
    else:
        num_groups = int(message.text)
        if num_groups >= 2 and num_groups <= ((characteristics_count / 2)):
            request = Request()
            msg = await message.answer("Строю новую диаграмму...")
            characteristics = await json_parser.ungroup_characteristics_for_one_group(new_groups, group_name)
            new_groups_n = await controller.get_json_groups_existed(characteristics, num_groups)
            await state.update_data(new_groups=new_groups_n)
            if new_groups_n:
                await process_new_groups(message, new_groups_n, video_info_json, user_id, group_name)
            else:
                await process_group_without_new_groups(message, new_groups, group_name, video_info_json, user_id)
        else:
            await state.set_state(Form.groups)
            await message.answer(f"Я вас не понял. Введите любое число от 2 до {int(characteristics_count / 2)}:")

@router.message(Form.new_groups_from_main)
async def groups_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    characteristics_count = data.get("characteristics_count")
    json_group = data.get("json_group")
    video_info_json = data.get("video_info")
    user_id = data.get("user_id")
    group_name_f = data.get("first_group_name")
    if not message.text.isdigit():
        await state.set_state(Form.groups)
        await message.answer(f"Я вас не понял. Введите любое число от 2 до {int(characteristics_count / 2)}")
    else:
        num_groups = int(message.text)
        if num_groups >= 2 and num_groups <= ((characteristics_count / 2)):
            request = Request()
            msg = await message.answer("Строю новую диаграмму...")
            characteristics = await json_parser.ungroup_characteristics_for_one_group(json_group, group_name_f)
            new_groups = await controller.get_json_groups_existed(characteristics, num_groups)
            await state.update_data(new_groups=new_groups)
            if new_groups:
                await process_new_groups(message, new_groups, video_info_json, user_id, group_name_f)
            else:
                await process_group_without_new_groups(message, json_group, group_name_f, video_info_json, user_id)
        else:
            await state.set_state(Form.groups)
            await message.answer(f"Я вас не понял. Введите любое число от 2 до {int(characteristics_count / 2)}:")


@router.message(Form.groups)
async def groups_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    characteristics = data.get("characteristics")
    if not message.text.isdigit():
        await state.set_state(Form.groups)
        await message.answer(f"Я вас не понял. Введите любое число от 2 до {int((len(characteristics))/2)}")
    else:
        num_groups = int(message.text)
        data = await state.get_data()
        if num_groups >= 2 and num_groups <= (((len(characteristics))/2)):
            await state.update_data(groups=num_groups)
            msg = await message.answer(f"Идет обработка для {num_groups} групп...")
            video_link = data.get("video_link")
            video_info_json = data.get("video_info")
            user_id = data.get("user_id")
            message_id = data.get("url_message_id")
            if message_id is None:
                message_id = -1
            source = data.get("source")
                # json_group_c = await asyncio.to_thread(controller.get_json_groups_existed, characteristics, num_groups)
                # json_group = await json_group_c
            #json_group = await request_queue.put((characteristics, num_groups))
            json_group = await controller.get_json_groups_existed(characteristics, num_groups)
            db_characteristics = await json_parser.add_count_group_to_characteristics(characteristics, num_groups)
            await db_service.add_request(user_id, video_link, video_info_json, message_id, db_characteristics, "ой")
            await db_service.minus_token(user_id)
            if json_group:
                groups = await json_parser.parse_groups(json_group)
                groups_text = "\n".join([f"Группа: {name}\nОписание: {description}\n" for name, description in groups])
                builder = InlineKeyboardBuilder()
                builder.row(
                    InlineKeyboardButton(text="Добавить в избранноe", callback_data="add_to_favorites"))
                msg = await message.answer(
                    f"По характеристикам были выделены следующие группы:\n\n{groups_text}",
                    reply_markup=builder.as_markup(),
                )
                await state.update_data(request_message=msg)
                await state.update_data(json_group=json_group)
                await build_and_send_graphs(json_group, video_info_json, user_id, message)
            else:
                await message.answer("Ошибка при получении данных.")
        else:
            await state.set_state(Form.groups)
            await message.answer(f"Я вас не понял. Введите любое число от 2 до {int((len(characteristics))/2)}")


async def build_and_send_graphs(json_group, video_info_json, user_id, message):
    graph_data = await controller.get_main_general_graph(json_group, video_info_json)
    graph_bubble_posit = await controller.get_general_positive_bubble_graph(json_group, video_info_json)
    graph_bubble_negat = await controller.get_general_negative_bubble_graph(json_group, video_info_json)
    graph_bubble_pos_3d = await controller.get_general_positive_bubble_plot_3d(json_group, video_info_json)
    graph_bubble_neg_3d = await controller.get_general_negative_bubble_plot_3d(json_group, video_info_json)
    if graph_data:
        if graph_bubble_posit and graph_bubble_negat:
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
            graph_bubble_posit.write_html(
                file=os.path.join(all_media_dir, f'bubble_positive_{user_id}.html')
            )
            html_file = FSInputFile(path=os.path.join(all_media_dir, f'bubble_positive_{user_id}.html'))
            await message.answer_document(document=html_file)

            graph_bubble_negat.write_html(
                file=os.path.join(all_media_dir, f'bubble_negative_{user_id}.html')
            )
            html_file = FSInputFile(path=os.path.join(all_media_dir, f'bubble_negative_{user_id}.html'))
            await message.answer_document(document=html_file)
        if graph_bubble_pos_3d and graph_bubble_neg_3d:
            graph_bubble_pos_3d.write_image(
                file=os.path.join(all_media_dir, f'graph_bubble_pos_3d{user_id}.png'), width=1800,
                height=800)
            graph_bubble_neg_3d.write_image(
                file=os.path.join(all_media_dir, f'graph_bubble_neg_3d{user_id}.png'), width=1800,
                height=800)
            photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_bubble_pos_3d{user_id}.png'))
            await message.answer_photo(photo=photo_file)
            photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_bubble_neg_3d{user_id}.png'))
            await message.answer_photo(photo=photo_file)

            graph_bubble_pos_3d.write_html(
                file=os.path.join(all_media_dir, f'bubble_positive_3d_{user_id}.html')
            )
            html_file = FSInputFile(path=os.path.join(all_media_dir, f'bubble_positive_3d_{user_id}.html'))
            await message.answer_document(document=html_file)

            graph_bubble_neg_3d.write_html(
                file=os.path.join(all_media_dir, f'bubble_negative_3d_{user_id}.html')
            )
            html_file = FSInputFile(path=os.path.join(all_media_dir, f'bubble_negative_3d_{user_id}.html'))
            await message.answer_document(document=html_file)

        graph_data.write_image(
            file=os.path.join(all_media_dir, f'graph_data_{user_id}.png'), width=1800,
            height=800)
        photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_data_{user_id}.png'))
        group_buttons = await build_group_buttons(json_group, False)
        await message.answer_photo(photo=photo_file, caption="Общий график", reply_markup=group_buttons)
    else:
        await message.answer("Ошибка при создании графика.")

async def build_and_send_main_graphs(json_group, video_info_json, user_id, message):
    graph_data = await controller.get_main_general_graph(json_group, video_info_json)
    if graph_data:
        graph_data.write_image(
            file=os.path.join(all_media_dir, f'graph_data_{user_id}.png'), width=1800,
            height=800)
        photo_file = FSInputFile(path=os.path.join(all_media_dir, f'graph_data_{user_id}.png'))
        group_buttons = await build_group_buttons(json_group, False)
        await message.answer_photo(photo=photo_file, caption="Общий график", reply_markup=group_buttons)
    else:
        await message.answer("Ошибка при создании графика.")

async def build_group_buttons(json_groups: dict, add_buttom: bool) -> InlineKeyboardMarkup:
    buttons = {}
    for group in json_groups["groups"]:
        button = InlineKeyboardButton(text=group["group"], callback_data=f"get_group:{group['group']}")
        buttons[group["group"]] = button
    if add_buttom:
        back_button = InlineKeyboardButton(text="Назад к главному графику", callback_data="back_to_main")
        buttons["back_to_main"] = back_button
    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[[buttons[group]] for group in buttons])


@router.callback_query(F.data == "add_to_favorites")
async def add_to_favorites(callback_query: CallbackQuery, state: FSMContext):
    await db_service.create_engine()
    data = await state.get_data()
    user_id = data.get("user_id")
    video_link = data.get("video_link")
    message_id = data.get("url_message_id")
    requests = await db_service.get_favourite_requests(user_id)
    countOfFavorites = len(requests)
    if(countOfFavorites < 5):
        await db_service.change_favourite_flag(message_id, True)
        await callback_query.answer("Группы успешно добавлены в избранное!")
    else:
        await callback_query.answer("В избранном не может быть больше пяти анализов. Проверить это можно в разделе \"Избранное\".")




@router.message(F.text.startswith('/') & F.text[1:].isdigit())
async def goto_request_message(message: Message):
    try:
        message_id = int(message.text[1:])
        await message.answer(
            text="Перейдите по ответу, чтобы посмотреть информацию по запросу",
            reply_to_message_id=message_id
        )
    except Exception as e:
        await message.answer("Я вас не понял.")

@router.callback_query(F.data.startswith('favourite_'))
async def favourite_handler(callback_query: CallbackQuery, state: FSMContext, m_id=None):
    await db_service.create_engine()
    if m_id is None:
        m_id = int(callback_query.data[10:])
    user_id = callback_query.from_user.id
    request = await db_service.get_user_favourite_by_m_id(user_id, m_id)
    request = request[0]
    await state.update_data(video_info=request)
    title = request['title']
    views = request['viewCount']
    likes = request['likeCount']
    comments = request['commentCount']
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Просмотреть анализ видео", callback_data=f"favorite_video_anal_{m_id}"))
    builder.row(InlineKeyboardButton(text="Обновить характеристики и построить анализ (1 токен)", callback_data="get_video_info"))
    builder.row(InlineKeyboardButton(text="Удалить видео из избранного", callback_data=f"delete_favourite_{m_id}"))
    builder.row(InlineKeyboardButton(text="<< Назад в избранное", callback_data="back_to_fav"))
    msg = await callback_query.message.edit_text(
        text.video_info_text_in_fav.format(
            title, likes, comments, views
        ), reply_markup=builder.as_markup(),
    )
    await state.update_data(request_message=msg)
@router.callback_query(F.data.startswith('favorite_video_anal_'))
async def favorite_video_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    m_id = int(callback_query.data[20:])
    request = await db_service.get_user_favourite_by_m_id_char(user_id, m_id)
    request = request[0]

    try:
        processing_msg = await callback_query.message.answer(
            text="Перейдите по ответу, чтобы посмотреть информацию по запросу",
            reply_to_message_id=m_id
        )
        characteristics_with_group = request
        characteristics = await json_parser.get_characteristics(characteristics_with_group)

        await callback_query.message.answer(
            f"Идет обработка данных..."
        )
        try:
            await state.update_data(characteristics=characteristics)
            await callback_query.message.answer(
                f"Выделено {len(characteristics)} характеристик, введите количество групп от 2 до {int((len(characteristics)) / 2)}"
            )
            await state.set_state(Form.groups_from_favourite)  # Установка состояния здесь
        except Exception as e:
            await callback_query.message.answer(
                f"Не удалось обработать данные. Поробуйте еще раз."
            )
    except Exception as e:
        await callback_query.message.answer("Я вас не понял.")

@router.message(Form.groups_from_favourite)
async def get_main_graph_from_fav(message: Message, state: FSMContext):
    data = await state.get_data()
    characteristics = data.get("characteristics")
    if not message.text.isdigit():
        await state.set_state(Form.groups_from_favourite)
        await message.answer(f"Я вас не понял. Введите любое число от 2 до {int((len(characteristics)) / 2)}")
    else:
        num_groups = int(message.text)
        data = await state.get_data()
        if num_groups >= 2 and num_groups <= (((len(characteristics)) / 2)):
            await state.update_data(groups=num_groups)
            msg = await message.answer(f"Идет обработка для {num_groups} групп...")
            video_link = data.get("video_link")
            video_info_json = data.get("video_info")
            user_id = data.get("user_id")
            source = data.get("source")
            json_group = await controller.get_json_groups_existed(characteristics, num_groups)
            if json_group:
                groups = await json_parser.parse_groups(json_group)
                groups_text = "\n".join([f"Группа: {name}\nОписание: {description}\n" for name, description in groups])
                builder = InlineKeyboardBuilder()
                msg = await message.answer(
                    f"По характеристикам были выделены следующие группы:\n\n{groups_text}",
                    reply_markup=builder.as_markup(),
                )
                await state.update_data(request_message=msg)
                await state.update_data(json_group=json_group)
                await build_and_send_main_graphs(json_group, video_info_json, user_id, message)
            else:
                await message.answer("Ошибка при получении данных.")
        else:
            await state.set_state(Form.groups_from_favourite)
            await message.answer(f"Я вас не понял. Введите любое число от 2 до {int((len(characteristics)) / 2)}")



@router.callback_query(F.data.startswith("delete_favourite_"))
async def delete_favourite(callback_query: CallbackQuery):
    m_id = int(callback_query.data[17:])
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да", callback_data=f"delete_yes_{m_id}"))
    builder.row(InlineKeyboardButton(text="Нет", callback_data=f"delete_no_{m_id}"))
    msg = await callback_query.message.edit_text("Вы уверены, что хотите удалить видео из избранного?",
                                                 reply_markup=builder.as_markup())
@router.callback_query(F.data.startswith('delete_yes_'))
async def delete_yes(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    m_id = int(callback_query.data[11:])
    await db_service.create_engine()
    await db_service.change_favourite_flag(m_id, False)
    favourites = await db_service.get_user_favourites(user_id)
    if len(favourites) != 0:
        await return_to_fav(callback_query, state)
    else:
        await callback_query.message.edit_text("В избранном пусто")

@router.callback_query(F.data.startswith("delete_no_"))
async def delete_no(callback_query: CallbackQuery, state: FSMContext):
    m_id = int(callback_query.data[10:])
    await favourite_handler(callback_query, state, m_id)
@router.callback_query(F.data =="back_to_fav")
async def return_to_fav(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    favourites = await db_service.get_user_favourites(user_id)
    if len(favourites) != 0:
        video_in_favourite_button = InlineKeyboardBuilder()
        favourite_videos_m_id = []
        for video in favourites:
            video_in_favourite_button.row(InlineKeyboardButton(text=str(video.video_information['title']),
                                                               callback_data='favourite_' + str(video.message_id)))
            favourite_videos_m_id.append(video.message_id)
        await state.update_data(favourites_video_m_id=favourite_videos_m_id)
        msg = await callback_query.message.edit_text("Видео, которые вы добавили в избранное:",
                                                     reply_markup=video_in_favourite_button.as_markup())
    else:
        await callback_query.message.answer("Вы еще не добавили ни одного видео в избранное")



