import telebot as tg
import telebot.types as types
import re
import time
import hashlib

token = '6672835844:AAH204zBLHfaGJKJvsWuSiHQpXgTTKLfKZo'
bot = tg.TeleBot(token)
unnown_u = []

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id_f = message.from_user.id
    user_id = 1 #потом уберу, когда будет база данных с пользователями
    user_name = message.from_user.username
    if user_id == 0:
        m = f'Здравствуйте {user_name}, вы впервые пользуетесь ботом.'
        bot.send_message(message.chat.id, text=m)
        keyboard = types.InlineKeyboardMarkup()
        reg = types.InlineKeyboardButton('Запомнить меня', callback_data='registration')
        keyboard.add(reg)
        bot.send_message(message.chat.id, text='Хотите зарегистрироваться?', reply_markup=keyboard)

    elif user_id == 1:
        m = f'Здравствуйте {user_name}, с возвращением!.'
        keyboard = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
        b_history = types.KeyboardButton('История\U0001F4D6')
        b_favorite = types.KeyboardButton('Избранное\U00002763')
        b_account = types.KeyboardButton('Аккаунт\U0001F921')
        b_help = types.KeyboardButton('Навигация\U0001F5FA')
        keyboard.add(b_account, b_history, b_favorite, b_help)
        bot.send_message(message.chat.id, text=m, reply_markup=keyboard)

        @bot.message_handler(func=lambda message: True)
        def handle_button(message):
            match message.text:
                case 'История\U0001F4D6':
                    history = get_last_20_by_user(message.from_user.id)
                    keys = []
                    values = []
                    result = "Последние 20 видео, запрашиваемые вами:\n"
                    i = 1
                    for message_id, video_id, request_date in history:
                        keys.append('/' + str(i))
                        values.append(message_id)
                        result += f"/{i} {video_id} от {request_date}\n"
                        i += 1
                    bot.send_message(message.chat.id, text=result)
                    global dict_com
                    dict_com = dict(zip(keys, values))


                case 'Избранное\U00002763':
                    # в дальнейшем будет подтягиваться из функции
                    if is_file_empty() != True and len(get_favorite_video_ids(message.from_user.id)) != 0:
                        fav = create_list_of_button(get_favorite_video_ids(message.from_user.id))
                        bot.send_message(chat_id=message.chat.id, text='Вы добавили в избранное следующие видео:', reply_markup=fav)
                    else:
                        bot.send_message(chat_id=message.chat.id, text='Вы еще не добавили ни одного видео в избранное.')
                case 'Аккаунт\U0001F921':
                    bot.send_message(chat_id=message.chat.id, text="Вы нажали на Кнопку 1!")
                case 'Навигация\U0001F5FA':
                    bot.send_message(chat_id=message.chat.id, text="Вы нажали на Кнопку 1!")
                case _:
                    youtube_link_pattern = r'https?://(?:www\.)?youtube\.com/watch\?v=\w+'
                    if re.search(youtube_link_pattern, message.text):
                        tconv = lambda x: time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(x))
                        m_date = tconv(message.date)
                        m_user_id = message.from_user.id
                        m_id = message.message_id
                        link = handle_youtube_link(message)
                        write_to_file(m_id, m_user_id, link, m_date)
                        m_queue = bot.send_message(chat_id=message.chat.id, text='Ваш запрос в очереди')
                        #тут должна быть очередь
                        time.sleep(5)
                        #должно подтягиваться из БД
                        # data = get_data()
                        # message_text = data[0]
                        #message_video_info = data[1]
                        text = 'Название видео, дата публикации, кол-во просмотров, кол-во лайков'

                        video_info = types.InlineKeyboardMarkup(row_width=1)
                        show_video_info = types.InlineKeyboardButton(text='Запросить анализ видео', callback_data='show_video_info')
                        add_favourite = types.InlineKeyboardButton(text='Добавить видео в избранное', callback_data='add_favourite')
                        video_info.add(show_video_info, add_favourite)
                        bot.edit_message_text(chat_id=message.chat.id, message_id=m_queue.message_id, text=text, reply_markup=video_info)

                    elif message.text in dict_com.keys():
                        bot.forward_message(message.chat.id, message.chat.id, dict_com[message.text])
                    else:
                        bot.send_message(chat_id=message.chat.id,
                                         text='Я вас не понял.\nВы можете посмортеть свои возможности, нажав кнопку Навигации')


    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        t_id = message.chat.id
        num_b = 0
        if str(call.data)[-1] in '12345':
            num_b = call.data[-1]
        if call.data == 'registration':
            unnown_u.append(message.from_user.id)
            bot.send_message(t_id, text='Мы вас запомнили')
            #тут должен быть запрос в базу на изменение роли пользователя

        elif bool(re.fullmatch(r'favourite[1-5]', call.data)):
            text = 'Здесь должно быть название, кол-во просмотров, дата публикации и кол-во лайков'#взять из функции в зависимости от видео(номера кнопки)
            bot.edit_message_text(chat_id=t_id, message_id=call.message.message_id,
                                  text=text, reply_markup=create_fav_info(num_b))

        elif bool(re.fullmatch(r'delete_video_info[1-5]', call.data)):
            k_delete = types.InlineKeyboardMarkup(row_width=2)
            yes = types.InlineKeyboardButton(text='Да', callback_data='delete_yes')
            no = types.InlineKeyboardButton(text='Нет', callback_data='delete_no')
            k_delete.add(yes, no)
            bot.edit_message_text(chat_id=t_id, message_id=call.message.message_id,
                                  text='Вы уверены, что хотите удалить видео из избранного?', reply_markup=k_delete)
        elif call.data == 'delete_yes':
            name = get_favorite_video_ids(message.from_user.id)[num_b - 1]
            bot.send_message(chat_id=t_id, text=f'Видео {name} больше не в избранном.')
            unfavorite_by_video_id(message.from_user.id, name)
            if len(get_favorite_video_ids(message.from_user.id)) != 0:
                bot.edit_message_text(chat_id=t_id,
                                      message_id=call.message.message_id,
                                      text='Вы добавили в избранное следующие видео:',
                                      reply_markup=create_list_of_button(get_favorite_video_ids(message.from_user.id)))
            else:
                bot.edit_message_text(chat_id=t_id,
                                      message_id=call.message.message_id,
                                      text='В избранном ничего нет')
        elif call.data == 'delete_no':
            bot.edit_message_text(chat_id=t_id, message_id=call.message.message_id,
                                  text='Здесь должно быть название, кол-во просмотров, дата публикации и кол-во лайков',
                                  reply_markup=create_fav_info(num_b))
        elif call.data == 'back_to_fav':
            fav = create_list_of_button(get_favorite_video_ids(message.from_user.id))
            bot.edit_message_text(chat_id=t_id, message_id=call.message.message_id,
                                  text='Вы добавили в избранное следующие видео:', reply_markup=fav)
        elif call.data == 'add_favourite':
            if is_file_empty() == True:
                toggle_last_favorite(message.from_user.id)
                bot.edit_message_text(chat_id=t_id,message_id=call.message.message_id, text='Видео добавленно в избранное')
            else:
                if check_favorite_limit(message.from_user.id):
                    toggle_last_favorite(message.from_user.id)
                    bot.edit_message_text(chat_id=t_id,message_id=call.message.message_id, text='Видео добавленно в избранное')
                else:
                    bot.edit_message_text(chat_id=t_id,message_id=call.message.message_id, text='Вы не можете добавить видео, так как в избранном уже сохраненно 5 видео')
        elif call.data == 'show_video_info':
            pass
        elif bool(re.fullmatch(r'hisrory[1-20]', call.data)):
                pass


def get_last_20_by_user(user_id):
    try:
        with open('requests.txt', 'r') as file:
            lines = file.readlines()

        # Фильтруем строки по user_id в обратном порядке
        filtered_lines = [line.strip().split(',') for line in lines if line.split(',')[1] == str(user_id)]

        # Берем последние 20 строк (или меньше, если их меньше 20)
        last_20 = filtered_lines[-20:]

        # Возвращаем список кортежей (message_id, video_id, request_date)
        return [(parts[0], parts[2], parts[4]) for parts in last_20]

    except IOError:
        print("Ошибка при чтении из файла.")
        return []
def create_fav_info(num_b):
    fav_info = types.InlineKeyboardMarkup(row_width=2)
    show = types.InlineKeyboardButton(text='Просмотреть информацию', callback_data=('show_video_info' + str(num_b)))
    update = types.InlineKeyboardButton(text='Обновить информацию', callback_data=('update_video_info' + str(num_b)))
    delete = types.InlineKeyboardButton(text='Удалить видео', callback_data=('delete_video_info' + str(num_b)))
    back = types.InlineKeyboardButton(text='<< Назад в избранное', callback_data='back_to_fav')
    fav_info.add(show, update, delete, back)
    return fav_info
#создание кнопок для избранного
def create_list_of_button(list):
    if len(list) != 0:
        fav = types.InlineKeyboardMarkup()
        for i in range(len(list)):
            button = types.InlineKeyboardButton(list[i], callback_data=('favourite' + str(i+1)))
            fav.add(button)
        return fav

#метод который возвращает ссылку на видео
def handle_youtube_link(message):
    youtube_link = re.search(r'https?://(?:www\.)?youtube\.com/watch\?v=\w+', message.text).group()
    return youtube_link
#метож который записывает ссылку на видео и айди сообщения в файл, НАДО БУДЕТ ИЗМЕНИТЬ НА ЗАПИСЬ В БД + надо будет записывать название видео

def write_to_file(message_id, param1, param2, param3, param4=0, param5=0, param6=0):
    try:
        with open('requests.txt', 'a') as file:
            # Словарь для хранения соответствия между ссылками на видео и их айди
            video_ids = {}

            # Генерируем или получаем айди видео на основе ссылки
            if param2 in video_ids:
                video_id = video_ids[param2]
            else:
                video_id = hashlib.md5(param2.encode()).hexdigest()[:8]
                video_ids[param2] = video_id

            # Формируем строку данных
            data_line = f"{message_id},{param1},{video_id},{param2},{param3},{0},{param4},{param5},{param6}\n"

            # Записываем строку в файл
            file.write(data_line)
    except IOError:
        print("Ошибка при записи в файл.")


#метод, который забирает из файла параметры и возвращает список параметров, в дальнейщем надо поменять под БД
def read_from_file(message_id=None, param1=None, param2=None, param3=None, param4=None, param5=None, param6=None):
    try:
        with open('requests.txt', 'r') as file:
            lines = file.readlines()

            filtered_lines = []
            for line in lines:
                parts = line.strip().split(',')

                # Проверяем, соответствует ли строка указанным параметрам
                if (message_id is None or parts[0] == str(message_id)) and \
                        (param1 is None or parts[1] == str(param1)) and \
                        (param2 is None or parts[3] == param2) and \
                        (param3 is None or parts[4] == param3) and \
                        (param4 is None or int(parts[6]) == param4) and \
                        (param5 is None or int(parts[7]) == param5) and \
                        (param6 is None or int(parts[8]) == param6):
                    filtered_lines.append(line)

            return filtered_lines
    except IOError:
        print("Ошибка при чтении из файла.")
        return []

#call.message.from_user.id
def toggle_last_favorite(user_id):
    try:
        lines = []

        # Читаем все строки из файла
        with open('requests.txt', 'r') as file:
            lines = file.readlines()

        # Если файл пуст, возвращаем
        if not lines:
            return

        # Ищем последнюю строку с указанным user_id
        for i in range(len(lines) - 1, -1, -1):
            parts = lines[i].strip().split(',')
            if parts[1] == str(user_id):
                # Меняем флаг фаворита с 0 на 1
                parts[5] = '1'
                lines[i] = ','.join(parts) + '\n'
                break

        # Перезаписываем файл с обновленными данными
        with open('requests.txt', 'w') as file:
            file.writelines(lines)
    except IOError:
        print("Ошибка при работе с файлом.")

def is_file_empty():
    try:
        with open('requests.txt', 'r') as file:
            lines = file.readlines()
            if not lines:
                return True
            else:
                return False
    except IOError:
        print("Ошибка при чтении из файла.")
        return True
def get_favorite_video_ids(user_id):
    try:
        with open('requests.txt', 'r') as file:
            lines = file.readlines()

        favorite_video_ids = set()

        for line in lines:
            parts = line.strip().split(',')
            if parts[1] == str(user_id) and parts[5] == '1':
                favorite_video_ids.add(parts[2])

        return list(favorite_video_ids)

    except IOError:
        print("Ошибка при чтении из файла.")
        return []


def check_favorite_limit(user_id):
    try:
        with open('requests.txt', 'r') as file:
            lines = file.readlines()

        favorite_count = 0
        for line in lines:
            parts = line.strip().split(',')
            if parts[1] == str(user_id) and parts[5] == '1':
                favorite_count += 1
                if favorite_count > 5:
                    return False

        return True

    except IOError:
        print("Ошибка при чтении из файла.")
        return False


def unfavorite_by_video_id(user_id, video_id):
    try:
        lines = []

        # Читаем все строки из файла
        with open('requests.txt', 'r') as file:
            lines = file.readlines()

        # Обновляем флаг фаворита в строках с указанными user_id и video_id
        updated = False
        for i, line in enumerate(lines):
            parts = line.strip().split(',')
            if parts[1] == str(user_id) and parts[2] == video_id and parts[5] == '1':
                parts[5] = '0'
                lines[i] = ','.join(parts) + '\n'
                updated = True

        # Если ни одна строка не была обновлена, возвращаем
        if not updated:
            return

        # Перезаписываем файл с обновленными данными
        with open('requests.txt', 'w') as file:
            file.writelines(lines)

    except IOError:
        print("Ошибка при работе с файлом.")

def get_data():
    pass

def create_history_m(dict):
    pass
bot.polling(none_stop=True)
