import asyncio  # Добавлено для управления асинхронным запуском
import time
import sys
import os
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup
from telebot import types
import re
sys.path.insert(1, os.path.join(sys.path[0], 'C:/Users/Королева/PycharmProjects/new_bot/services'))
import controller

class User:
    def __init__(self):
        self.user_name = 0
        self.user_id = 0
        self.role = 'user'
class Chat:
    def __init__(self):
        self.chat_id = 0
        self.current_message_id = 0
        self.temp_message_id = 0
        self.video_link = 0
        self.group_counter = 0
        self.date_request = 0
        self.json = 0
        self.group_names = 0

    def set_json(self, json):
        self.json = json

    def set_group_names(self):
        self.group_names = [group['group'] for group in self.json['groups']]

class BaseHandler:
    def __init__(self, bot: AsyncTeleBot, user: User, chat: Chat):
        self.bot = bot
        self.user = user
        self.chat = chat

    async def handle(self, message: Message):
        raise NotImplementedError("Обработчики должны реализовать метод handle.")

class StartHandler(BaseHandler):
    async def handle(self, message: Message):
        self.user.user_id = message.from_user.id
        self.user.user_name = message.from_user.username
        self.chat.chat_id = message.chat.id
        await self.bot.send_message(self.chat.chat_id, f"Добро пожаловать {self.user.user_name}! Используйте /help, чтобы увидеть доступные команды.")
        if self.user.role == 'user':
            user_keyboard = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
            b_history = types.KeyboardButton('История\U0001F4D6')
            b_favorite = types.KeyboardButton('Избранное\U00002763')
            b_account = types.KeyboardButton('Аккаунт\U0001F921')
            b_help = types.KeyboardButton('Навигация\U0001F5FA')
            user_keyboard.add(b_account, b_history, b_favorite, b_help)
            await self.bot.send_message(self.chat.chat_id, "Вы зашли под ролью - пользователь.\nОтправьте мне ссылку на видео, которое хотите проанализировать или использьзуйте вашу клавиатуру", reply_markup=user_keyboard)


class HelpHandler(BaseHandler):
    async def handle(self, message: Message):
        await self.bot.send_message(message.chat.id, "Доступные команды:\n/start - Запустить бота\n/help - Показать помощь")

class UnknownCommandHandler(BaseHandler):
    async def handle(self, message: Message):
        youtube_link_pattern = r'https?://(?:www\.)?youtube\.com/watch\?v=\w+'
        if re.search(youtube_link_pattern, message.text):
            tconv = lambda x: time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(x))
            self.chat.date_request = tconv(message.date)
            self.chat.video_link = message.text
            self.chat.chat_id = message.chat.id
            button = types.InlineKeyboardMarkup(row_width=3)
            b_list = [types.InlineKeyboardButton(text=str(i), callback_data=str(i)) for i in range(1, 11)]
            button.add(*b_list)
            c_m = await self.bot.send_message(self.chat.chat_id,
                                        "Выделенно 50 характеристик.\nВыберите количество групп, на которые вы хотите разделить характеристики",
                                        reply_markup=button)
            self.chat.current_message_id = c_m.message_id
        else:
            await self.bot.send_message(message.chat.id, "Извините, я не понял эту команду.")

class InlineButtonHandler(BaseHandler):
    def __init__(self, bot: AsyncTeleBot, user: User, chat: Chat, controller: controller.Controller):
        self.bot = bot
        self.user = user
        self.chat = chat
        self.controller = controller

    async def handle(self, call: CallbackQuery):
        if call.data.isdigit():
            self.chat.group_counter = int(call.data)
            self.chat.set_json(self.controller.get_json_groups(self.chat.video_link, self.chat.group_counter))##тут тоже работает
            self.chat.set_group_names()##работает
            m_c = await self.bot.edit_message_text(chat_id=self.chat.chat_id,
                                                   message_id=self.chat.current_message_id, text='Ваш запрос в очереди')
            self.chat.current_message_id = m_c.message_id
            keyboard = types.InlineKeyboardMarkup()
            b1 = types.InlineKeyboardButton('Запросить анализ видео', callback_data='video_analis')
            keyboard.add(b1)
            m_c = await self.bot.edit_message_text(chat_id=self.chat.chat_id,
                                             message_id=self.chat.current_message_id,
                                             text='xnxjxj', reply_markup=keyboard)
            self.chat.current_message_id = m_c.message_id
        elif call.data == 'video_analis':
            await self.bot.send_message(chat_id=self.chat.chat_id, text='Вот графики по вашему видео')
            # await self.bot.edit_message_text(chat_id=self.chat.chat_id,
            #                                  message_id=self.chat.current_message_id,
            #                                  text='Вот графики по вашему видео')
            fig_b_p = self.controller.get_general_positive_bubble_graph(self.chat.json)
            fig_b_n = self.controller.get_general_negative_bubble_graph(self.chat.json)
            fig_g = self.controller.get_main_general_graph(self.chat.json)

            fig_b_p.write_image(f"gen_positive_bubble_{self.user.user_id}.png", width=1800, height=800)
            fig_b_n.write_image(f"gen_negative_bubble_{self.user.user_id}.png", width=1800, height=800)
            fig_g.write_image(f"gen_histogram_{self.user.user_id}.png", width=1800, height=800)
            keyboard = types.InlineKeyboardMarkup(row_width=3)
            list = [types.InlineKeyboardButton(text=f'{self.chat.group_names[i]}',
                                               callback_data=f'{self.chat.group_names[i]}'+str(i+1)) for i in range(len(self.chat.group_names))]
            keyboard.add(*list)
            with open(f"gen_positive_bubble_{self.user.user_id}.png", 'rb') as photo:
                await self.bot.send_photo(chat_id=self.chat.chat_id, photo=photo)
            with open(f"gen_negative_bubble_{self.user.user_id}.png", 'rb') as photo:
                await self.bot.send_photo(chat_id=self.chat.chat_id, photo=photo)
            with open(f"gen_histogram_{self.user.user_id}.png", 'rb') as photo:
                await self.bot.send_photo(chat_id=self.chat.chat_id, photo=photo, caption='', reply_markup=keyboard)
class Bot:
    def __init__(self, token: str):
        self.bot = AsyncTeleBot(token)
        self.user = User()
        self.chat = Chat()
        self.handlers = self.setup_handlers()
        self.query_handlers = self.setup_query_handlers()

    def setup_handlers(self):
        return {
            'start': StartHandler(self.bot, self.user, self.chat),
            'help': HelpHandler(self.bot, self.user, self.chat),
            'unknown': UnknownCommandHandler(self.bot, self.user, self.chat),
            'Управление пользователями\U0001F465': 0,
            'Статистика БД\U0001F418\U0001F4CA': 0,
            'Выдать токены\U0001F4B8': 0,
            'Выйти из режима администрирования\U0001F6AA': 0,
            'История\U0001F4D6': 0,
            'Избранное\U00002763': 0,
            'Аккаунт\U0001F921': 0,
            'Навигация\U0001F5FA': 0,
            'Войти в режим администрирования\U0001F6AA': 0
        }
    def setup_query_handlers(self):
        return {
            'inline_button': InlineButtonHandler(self.bot, self.user, self.chat, controller.Controller())
        }

    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        async def start_command(message: Message):
            await self.handlers['start'].handle(message)

        @self.bot.message_handler(commands=['help'])
        async def help_command(message: Message):
            await self.handlers['help'].handle(message)

        @self.bot.message_handler(func=lambda message: True)
        async def unknown_command(message: Message):
            await self.handlers['unknown'].handle(message)


    def register_query_handlers(self):
        @self.bot.callback_query_handler(func=lambda call: True)
        async def callback_query_handler(call: CallbackQuery):
            await self.query_handlers['inline_button'].handle(call)

    async def run(self):
        self.register_handlers()
        self.register_query_handlers()
        await self.bot.infinity_polling()

if __name__ == "__main__":
    bot = Bot('6672835844:AAH204zBLHfaGJKJvsWuSiHQpXgTTKLfKZo')
    # Запуск асинхронного цикла
    asyncio.run(bot.run())
