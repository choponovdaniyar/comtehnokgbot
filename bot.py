from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import math
import datetime

from db import DB
import config



bot = Bot(token = config.TOKEN)
dp = Dispatcher(bot)
db = DB("bot.db")

start_study_year = 2021
start_study_moth = 9
start_study_day  = 15

def get_day(id, day_id, this_week = True):
    days = {
        "пн": 1, 
        "вт": 2,
        "ср": 3,
        "чт": 4,
        "пт": 5,
        "сб": 6,
    }   
    group_id = db.response("SELECT group_id FROM users_ WHERE user_id = {}".format(int(id)))[0][0]
    course = db.response("SELECT course FROM group_ WHERE id = {}".format(group_id))[0][0]
    week = datetime.datetime.now() - datetime.datetime(start_study_year, start_study_moth, start_study_day)
    week = math.ceil((week.days + 7) / 7)   
    minmax = "MAX" if (week % 2 and this_week) or (not week % 2 and not this_week) else "MIN"
    ans = list()
    num_btn = {
        1:"1️⃣", 
        2:"2️⃣",
        3:"3️⃣",
        4:"4️⃣"
    }
    response = '''
        SELECT  lesson, {}(week), lesson_id
        FROM day_
        WHERE day_id = {} AND group_name = {}
        GROUP BY lesson_id
    '''.format(minmax, days[day_id[:2]], group_id)
    res = db.response(response) 
    it = 1
    for x in res:
        name, teacher, classroom = db.response("SELECT name, teacher, classroom FROM lesson_ WHERE id = {}".format(x[0]))[0]
        if name == "- - -":
            continue
        start, finish = db.response("SELECT start, finish FROM lesson_time_ WHERE course = {} AND lesson = {}".format(course, x[2]))[0]
        ans += ["\n".join([
            f"_"*30,
            f"{num_btn[it]}  <b>Кабинет:</b> {classroom}",
            f"<b>Время:</b>  {start} - {finish}",
            f"<b>Преподаватель:</b> {teacher}",
            f"<b>Название:</b> {name}"
        ])]
        it += 1
    markup = types.InlineKeyboardMarkup()
    
    if this_week:
        markup.add(types.InlineKeyboardButton(text = "На следующей неделе...", callback_data= f"{day_id[:2]}2"))
    else:
        markup.add(types.InlineKeyboardButton(text = "На этой неделе...", callback_data= f"{day_id[:2]}1"))
    
    ans = "Выходной ежже :)!" if not len(ans) else "\n\n".join(ans)
    if this_week == True:
        ans2, markup2 = get_day(id,day_id, False)
        if ans2 == ans:
            markup = None
    return [ans,  markup] #text, parse_mode, reply_markup




@dp.callback_query_handler(lambda call: len(call.data) == 7 and call.data[:6] == "course" and int(call.data[-1]) < 4)
async def process_callback2(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    course = int(call.data[-1])
    markup =  types.InlineKeyboardMarkup(row_width=3)
    group = [ x[0] for x in db.response("SELECT name FROM  group_ WHERE course = {}".format(course))]
    
    for x in range(0,len(group),2):
        if x + 1 < len(group):
            markup.add(types.InlineKeyboardButton(group[x], callback_data = group[x]),
                        types.InlineKeyboardButton(group[x+1], callback_data = group[x+1]))
            continue
        markup.add(types.InlineKeyboardButton(group[x], callback_data = group[x]))

    await bot.send_message(call.from_user.id, text = f"Выберите группу", reply_markup= markup) 

@dp.callback_query_handler(lambda call: call.data == "contact")
async def process_callback1(call: types.CallbackQuery):
    txt = [
        "<b>Почтовый индекс: </b>720048",
        "<b>Адрес:</b> г. Бишкек, ул.Анкара(Горького), 1/17",
        "<b>Тел.:</b>  0779-881-948, 0707-881-948",
        "<b>WhatsApp:</b> (0707)-37-99-57",
        "<b>e-mail:</b> comtehno.kg@gmail.com"
    ]
    await   bot.send_message(call.from_user.id , text = "\n".join(txt), parse_mode="html")

@dp.callback_query_handler(lambda call: len(db.response(f"SELECT name FROM  group_ WHERE name = '{call.data}'")) > 0)
async def process_callback2(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    group_id, group, course = db.response("SELECT * FROM  group_ WHERE name = '{}'".format(call.data))[0]    
    user_id = call.from_user.id

    row = (
        user_id,
        group_id,
        False
    )

    if user_id not in [x[0] for x in db.response("SELECT user_id FROM users_")]:
        db.insert("users_", row)
    else:
        db.response(
            '''
                UPDATE users_
                SET group_id = {}
                WHERE user_id = {}
            '''.format(group_id, user_id)
        )

    markup = types.ReplyKeyboardMarkup(row_width=7, resize_keyboard = True)
    markup.add( 
        types.KeyboardButton("пн"), 
        types.KeyboardButton("вт"), 
        types.KeyboardButton("ср"), 
        types.KeyboardButton("чт"), 
        types.KeyboardButton("пт"), 
        types.KeyboardButton("сб")
    )
    markup.add(
        types.KeyboardButton("Личные данные"),
        types.KeyboardButton("Обновить")
    )

    if len([x[0] for x in db.response("SELECT user_id FROM  users_ WHERE user_id = '{}' and is_admin = True".format(user_id))]) > 0:
        markup.add(types.KeyboardButton("Обновить расписание"))
    await bot.send_message(call.from_user.id, text = f"Вы, студент {course} курса, группы {group}\n\nРегистрация завершена!", reply_markup = markup)

@dp.callback_query_handler(lambda call: call.data[:2] in ["пн", "вт", "ср", "чт", "пт", "сб"])
async def process_callback2(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    week = call.data[2]
    msg = get_day(call.from_user.id, f"{call.data[:2]}{week}", True if week == "1" else False)

    await bot.send_message(call.from_user.id, text = msg[0], reply_markup=msg[1], parse_mode= "html")




@dp.message_handler(commands=["help"])
async def help_and_start_commands(message: types.Message):
    msg = [
        "Этот бот выводит расписание колледжа КомТехно\n",
        "Регистрация:",
        "1.  Нажмите на кнопку [Регистрация].",
        "2.  Выберите курс.",
        "3.  И группу.",
        "Регистрация завершена!",
        "",
        "После регистрации вы можете:",
        "- Получать расписание дня недели нажав на кнопки.",
        "- Смотреть и Обновлять личные данные",
        "",
        "[ пн ] - [ пт ]  - расписание выбранного дня",
        "[ обновить ] - обновление данных, введенные при регистрации",
        "[ абитуриентам ] - информация для абитуриентов",
        "[ личные данные ] - информация о дааных при регистрации"
    ]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Регистрация"),types.KeyboardButton("Абитуриентам:"))

    await message.answer("\n".join(msg), reply_markup=markup)

@dp.message_handler(commands=["start"])
async def help_and_start_commands(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
    markup.add(types.KeyboardButton("Регистрация"),types.KeyboardButton("Абитуриентам:"))
    await bot.send_message(message.from_user.id,"Информация для справки - [/help]", reply_markup= markup)    

@dp.message_handler(commands=[f"admin:{config.ADMIN_PASSWORD}"])
async def admin_password_commands(message: types.Message):
    try:
        markup = types.ReplyKeyboardMarkup(row_width=7, resize_keyboard = True)
        markup.add( 
            types.KeyboardButton("пн"), 
            types.KeyboardButton("вт"), 
            types.KeyboardButton("ср"), 
            types.KeyboardButton("чт"), 
            types.KeyboardButton("пт"), 
            types.KeyboardButton("сб")
        )
        markup.add(
            types.KeyboardButton("Личные данные"),
            types.KeyboardButton("Обновить")
        )
        markup.add(
            types.KeyboardButton("Обновить расписание")
        )
        user_id = str(message.from_user.id)
        
        update = '''
            UPDATE users_
            SET is_admin = True
            WHERE user_id = {}
        '''.format(user_id)
        db.response(update)

        await bot.delete_message(user_id, message.message_id)
        await message.answer("Добавлена кнопка [Обновить_расписание]", reply_markup = markup)
        
    except:
        await message.answer("Вы не зарегистрированы!")

@dp.message_handler(lambda msg: msg.text == "Абитуриентам:")
async def message_handler0(message: types.Message):
    markup = types.InlineKeyboardMarkup(row_width = 2)
    markup.add(types.InlineKeyboardButton("Онлайн тестирование", callback_data="online_test", url = config.ONLINE_TEST))
    markup.add(
        types.InlineKeyboardButton("Консультатция", callback_data="consultation", url = config.CONSULTATION),
        types.InlineKeyboardButton("Контакты", callback_data="contact")    
    )
    await message.answer("Информация:", reply_markup = markup)
    

@dp.message_handler(lambda msg: msg.text == "Обновить расписание")
async def message_handler1(message: types.Message):  
    stoping = await message.answer("Пожалуйста подождите\nИдет обновление...")
    try:
        db.restart()
        await message.answer("Расписание успешно обновлено!")
    except:
        await message.answer("Простите, произошла системная ошибка\nПожалуйста, обратитесь к разработчикам!")
    finally:
        await bot.delete_message(message.from_user.id, stoping.message_id)

@dp.message_handler(lambda msg: msg.text == "Регистрация")
async def message_handler2(message: types.Message):
    btn1 = types.InlineKeyboardButton('Первый курс', callback_data='course1')
    btn2 = types.InlineKeyboardButton('Второй курс', callback_data='course2')
    btn3 = types.InlineKeyboardButton('Третьий курc', callback_data='course3')
    markup =  types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn1,btn2,btn3)
    await message.answer("Выберите курс:", reply_markup= markup)

@dp.message_handler(lambda msg: msg.text == "Обновить")
async def message_handler3(message: types.Message):
    btn1 = types.InlineKeyboardButton('Первый курс', callback_data='course1')
    btn2 = types.InlineKeyboardButton('Второй курс', callback_data='course2')
    btn3 = types.InlineKeyboardButton('Третьий курc', callback_data='course3')
    markup =  types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn1,btn2,btn3)
    await message.answer("Выберите курс:", reply_markup= markup)

@dp.message_handler(lambda msg: msg.text == "Личные данные")
async def message_handler4(message: types.Message):
    get_data = '''
        SELECT name, course 
        FROM group_
        WHERE id IN (
            SELECT group_id
            FROM users_
            WHERE user_id = {}
        )   
    '''.format(message.from_user.id)
    group, course = db.response(get_data)[0]
    try:
        msg = "курс:  {}\nгруппа:  {}".format(course, group)
        await message.answer(msg)
    except KeyError:
        await message.answer("Вы не зарегистрированы!")   

@dp.message_handler(lambda msg: msg.text in ["пн", "вт", "ср", "чт", "пт", "сб"])
async def message_handler5(message: types.Message):
    msg  = get_day(message.from_user.id, message.text)
    await message.answer(text = msg[0], parse_mode = "html", reply_markup = msg[1])

@dp.message_handler()
async def message_handler6(message: types.Message):
    await bot.delete_message(message.from_user.id, message.message_id)


if __name__ == '__main__':
    print(f"{datetime.datetime.now()}  [start]")
    executor.start_polling(dp, skip_updates=False)
    print("finished")   
    
    