# -*- coding: utf-8 -*-
import aiogram
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import math
import datetime
import sqlite3

import config
import restart


bot = Bot(token = config.TOKEN)
dp = Dispatcher(bot)
def respons(a):
    con = sqlite3.connect("bot.db")
    cur = con.execute(a)
    con.commit()
    return cur.fetchall()

start_study_year = 2021
start_study_moth = 9 
start_study_day  = 13

def get_day(id, day_id, this_week = True):
    days = {
        "pn": "ПОНЕДЕЛЬНИК", 
        "vt": "ВТОРНИК",
        "sr": "СРЕДА",
        "ct": "ЧЕТВЕРГ",
        "pt": "ПЯТНИЦА",
        "sb": "СУББОТА",
    }   
    week = datetime.datetime.now() - datetime.datetime(start_study_year, start_study_moth, start_study_day)
    week = math.ceil((week.days * 60 * 60 * 24 + week.seconds) / (60 * 60 * 24 * 7))   
    week = 2 if (not week % 2 and this_week) or (week % 2 and not this_week) else 1
    chet =  f'<b>Неделя:</b> {"числитель" if week == 1 else "знаменатель"}\n'

    day = days[day_id[:2]] 
    try:
        group = respons("SELECT name FROM group_ WHERE id IN (SELECT group_name FROM users_ WHERE user_id = {})".format(id))[0][0]    
    except:
        return ["Вы не зарегистрированы!", types.InlineKeyboardMarkup()] 
        group = respons("SELECT name FROM group_ WHERE id = 1".format(id))[0][0]
    num_btn = {
        1:"1️⃣", 
        2:"2️⃣",
        3:"3️⃣",
        4:"4️⃣"
    }
        

    lessons = respons("SELECT * FROM lesson_ WHERE group_name = '{}' AND week = '{}' AND day = '{}' ORDER BY lesson_id".format(group, week, day)) 
    lesson_id = 1
    ans = list()

    for lsn in lessons:
        print(lsn)
        name, teacher, classroom, time = lsn[-2], lsn[-3], lsn[-1], lsn[-4]
        if name == "- - -":
            continue
        ans += ["\n".join([
            f"_"*30,
            f"{num_btn[lesson_id]}  <b>Кабинет:</b> {classroom}",
            f"<b>Время:</b>  {time}",
            f"<b>Преподаватель:</b> {teacher}",
            f"<b>Название:</b> {name}"
        ])]
        lesson_id += 1
    markup = types.InlineKeyboardMarkup()
    
    if this_week:
        markup.add(types.InlineKeyboardButton(text = "На следующей неделе...", callback_data= f"{day_id[:2]}2"))
    else:
        markup.add(types.InlineKeyboardButton(text = "На этой неделе...", callback_data= f"{day_id[:2]}1"))
    ans = "В этот день нет пар! :)" if not len(ans) else "\n\n".join(ans)
    if this_week == True:
        ans2, markup2 = get_day(id,day_id, False)
        if ans2 == ans:
            markup = None
    return [  f"{chet}{ans}",  markup] #text, parse_mode, reply_markup
    

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


@dp.callback_query_handler(lambda call: call.data[:2] in ["pn", "vt", "sr", "ct", "pt", "sb"])
async def process_callback2(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    week = call.data[2]
    msg = get_day(call.from_user.id, f"{call.data[:2]}{week}", True if week == "1" else False)

    await bot.send_message(call.from_user.id, text = msg[0], reply_markup=msg[1], parse_mode= "html")


@dp.callback_query_handler(lambda call: len(call.data) == 7 and call.data[:6] == "course" and int(call.data[-1]) < 4)
async def process_callback2(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    course = int(call.data[-1])
    markup =  types.InlineKeyboardMarkup(row_width=3)
    group = respons("SELECT * FROM group_ WHERE course = '{}'".format(course))
    for x in range(0,len(group),2):
        if x + 1 < len(group):
            markup.add(types.InlineKeyboardButton(group[x][1], callback_data = group[x][0]),
                        types.InlineKeyboardButton(group[x+1][1], callback_data = group[x+1][0]))
            continue
        markup.add(types.InlineKeyboardButton(group[x][1], callback_data = group[x][0]))

    await bot.send_message(call.from_user.id, text = f"Выберите группу", reply_markup= markup) 


@dp.callback_query_handler(lambda call: len(respons("SELECT * FROM group_ WHERE id = {}".format(call.data))) > 0)
async def process_callback2(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)    
    user_id = call.from_user.id
    group = respons("SELECT name FROM group_ WHERE id = {}".format(call.data))[0][0]
    if user_id not in [x[0] for x in respons("SELECT * FROM users_")]:
        respons("INSERT INTO users_ VALUES ({}, {}, {})".format(user_id, call.data, 0))
    else:
        respons("UPDATE users_ SET group_name = {} WHERE user_id = {}".format(call.data, user_id))
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

    if len([x[0] for x in respons("SELECT user_id FROM  users_ WHERE user_id = {} AND is_admin = True".format(user_id))]) > 0:
        markup.add(types.KeyboardButton("Обновить расписание"))
    await bot.send_message(call.from_user.id, text = f"Вы, студент группы {group}\n\nРегистрация завершена!", reply_markup = markup)
    # await bot.send_message(call.from_user.id, text = call.data)



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

@dp.message_handler(commands=[f"admin:commands"])
async def admin_lessons_commands(message: types.Message):
    user_id = message.from_user.id
    msg = [
        "Команды",
        "/admin:all_lessons",
        "/admin:password"
    ]
    await bot.delete_message(user_id, message.message_id)
    msg = await message.answer("\n".join(msg))
    await aiogram.asyncio.sleep(5)
    await bot.delete_message(user_id, msg.message_id)

@dp.message_handler(commands=[f"admin:all_lessons"])
async def admin_lessons_commands(message: types.Message):
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


    user_id = message.from_user.id
    try:
        group_id = respons("SELECT group_name FROM users_ WHERE user_id = {}".format(user_id))[0][0]
    except:
        await message.answer("Вы не зарегистрированы!")
    else:
        name = respons("SELECT name FROM group_ WHERE id = {}".format(group_id))[0][0]
        lesson = respons("SELECT lesson FROM lesson_ WHERE group_name = '{}'".format(name))
        lesson_names = list(set(str(x[0]) for x in lesson))
        for x in range(len(lesson_names)):
            lesson_names[x] = lesson_names[x].replace("(лек.)", "")
            lesson_names[x] = lesson_names[x].replace("(лек)", "")
            lesson_names[x] = lesson_names[x].replace("(лаб.)", "")
            lesson_names[x] = lesson_names[x].replace("(лаб)", "")
            lesson_names[x] = lesson_names[x].replace("(пр.)", "")
            lesson_names[x] = lesson_names[x].replace("(пр)", "")
            if lesson_names[x] != "нет":
                continue
            lesson_names[x], lesson_names[0] = lesson_names[0], lesson_names[x]

        lessons = list(set(lesson_names[x] for x in range(1,len(lesson_names))))
        lessons.sort()
        lessons = list(f"{x + 1}.  {lessons[x]}" for x in range(len(lessons)))
        await bot.delete_message(user_id, message.message_id)
        await message.answer("\n".join(lessons), reply_markup = markup)
        
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
        respons('UPDATE users_ SET is_admin = True WHERE user_id = {}'.format(user_id))
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
        restart.restart()
        await message.answer("Расписание успешно обновлено!")
    except Exception as e:
        await message.answer(f"[INFO]: {e}")
    finally:
        await bot.delete_message(message.from_user.id, stoping.message_id)

@dp.message_handler(lambda msg: msg.text == "Регистрация")
async def message_handler2(message: types.Message):
    btn1 = types.InlineKeyboardButton('Первый курс', callback_data='course1')
    btn2 = types.InlineKeyboardButton('Второй курс', callback_data='course2')
    btn3 = types.InlineKeyboardButton('Третьий курc', callback_data='course3')
    markup =  types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn1,btn2,btn3)
    await message.answer("Выберите курс", reply_markup= markup)

@dp.message_handler(lambda msg: msg.text == "Обновить")
async def message_handler3(message: types.Message):
    btn1 = types.InlineKeyboardButton('Первый курс', callback_data='course1')
    btn2 = types.InlineKeyboardButton('Второй курс', callback_data='course2')
    btn3 = types.InlineKeyboardButton('Третьий курc', callback_data='course3')
    markup =  types.InlineKeyboardMarkup(row_width=2)
    markup.add(btn1,btn2,btn3)
    await message.answer("Выберите курс", reply_markup= markup)

@dp.message_handler(lambda msg: msg.text == "Личные данные")
async def message_handler4(message: types.Message):
    try:
        group_id = respons("SELECT group_name FROM users_ WHERE user_id = {}".format(message.from_user.id))[0][0]  
        group, course = respons("SELECT name, course FROM group_ WHERE id = {}".format(group_id))[0]
        msg = "группа:  {}".format(group)
        await message.answer(msg)
    except:
        await message.answer("Вы не зарегистрированы!")   

@dp.message_handler(lambda msg: msg.text in ["пн", "вт", "ср", "чт", "пт", "сб"])
async def message_handler5(message: types.Message):
    if  message.text == "пн":
        message.text = "pn"
    elif message.text == "вт":
        message.text = "vt"
    elif message.text == "ср":
        message.text = "sr"
    elif message.text == "чт":
        message.text = "ct"
    elif message.text == "пт":
        message.text = "pt"
    elif message.text == "сб":
        message.text = "sb"
    
    msg  = get_day(message.from_user.id, message.text)
    await message.answer(text = msg[0], parse_mode = "html", reply_markup = msg[1])




tm = 10
@dp.message_handler(lambda msg: msg.text == "Альбина")
async def message_handler5(message: types.Message):
    msg = await message.answer(text = "Щечки, щечки💪🏻")
    await aiogram.asyncio.sleep(tm)
    await bot.delete_message(message.from_user.id, msg.message_id)
    await bot.delete_message(message.from_user.id, message.message_id)

@dp.message_handler(lambda msg: msg.text == "Ахмед")
async def message_handler5(message: types.Message)  :
    msg = await message.answer(text = "Сила💪🏻")
    await aiogram.asyncio.sleep(tm)
    await bot.delete_message(message.from_user.id, msg.message_id)
    await bot.delete_message(message.from_user.id, message.message_id)

@dp.message_handler(lambda msg: msg.text == "Эржан")
async def message_handler5(message: types.Message)  :
    msg = await message.answer(text = "Просыпай, на работу пора!")
    await aiogram.asyncio.sleep(tm)
    await bot.delete_message(message.from_user.id, msg.message_id)
    await bot.delete_message(message.from_user.id, message.message_id)

@dp.message_handler(lambda msg: msg.text == "Эльдар")
async def message_handler5(message: types.Message)  :
    msg = await message.answer(text = "Пиздюк")
    await aiogram.asyncio.sleep(tm)
    await bot.delete_message(message.from_user.id, msg.message_id)
    await bot.delete_message(message.from_user.id, message.message_id)

@dp.message_handler(lambda msg: msg.text == "Богдан")
async def message_handler5(message: types.Message)  :
    msg = await message.answer(text = "Братан")
    await aiogram.asyncio.sleep(tm)
    await bot.delete_message(message.from_user.id, msg.message_id)
    await bot.delete_message(message.from_user.id, message.message_id)

@dp.message_handler(lambda msg: msg.text == "Миа")
async def message_handler5(message: types.Message)  :   
    msg = await message.answer(text = "Люблю тебя:)❤️")
    await aiogram.asyncio.sleep(tm)
    await bot.delete_message(message.from_user.id, msg.message_id)
    await bot.delete_message(message.from_user.id, message.message_id)



@dp.message_handler()
async def message_handler6(message: types.Message):
    await bot.delete_message(message.from_user.id, message.message_id)


if __name__ == '__main__':
    print(f"{datetime.datetime.now()}  [start]")
    executor.start_polling(dp, skip_updates=False)
    print("finished")   
    
    