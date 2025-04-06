from aiogram import F
from aiogram.filters import Filter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.markdown import hlink
from aiogram.fsm.context import FSMContext
from loader import dp, bot, sender
from datetime import datetime

from os import path
from config import get_env, get_config, time_difference
import asyncio
import unicodedata as ud

import utils.kb as kb
from states import UserState
from database.model import DB
from support.tasks import menu


# Установка никнейма
@dp.message(UserState.name, F.text)
async def set_name(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    if len(msg.text) > 20 or len(msg.text) < 3:
        await sender.message(user_id, "wrong_name")
        return
    for char in msg.text:
        if not 'LATIN' in ud.name(char) and not char.isdigit() and char != "_":
            await sender.message(user_id, "wrong_name")
            return
    count = DB.get("select count(*) from users where nickname = ?", [msg.text], True)
    if count[0] > 0:
        await sender.message(user_id, "nickname_exists", None, msg.text)
        return

    DB.commit("update users set nickname = ? where telegram_id = ?", [msg.text, user_id])
    await sender.message(user_id, "nickname_set", None, msg.text)
    await menu(user_id, msg.text)
    await state.set_state(UserState.default)


# Проверка на отсутствие состояний
class NoStates(Filter):
    async def __call__(self, msg: Message, state: FSMContext):
        stat = await state.get_state()
        return stat is None


# Сообщение без состояний
@dp.message(NoStates())
async def no_states_handler(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    nickname = DB.get("select nickname from users where telegram_id = ?", [user_id], True)
    if not nickname:
        return
    elif nickname[0]:
        await menu(msg.from_user.id, nickname[0])
    await sender.message(user_id, "hello")
    await state.set_state(UserState.name)


# Рассылка
@dp.message(UserState.mailing)
async def mailing(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    data = await state.get_data()

    match data["status"]:
        case "begin":
            DB.commit("insert into repetitions (chat_id, message_id) values (?, ?)", [user_id, msg.message_id])
            zapis_id = DB.get("select id from repetitions where message_id = ?", [msg.message_id], True)[0]
            await state.set_data({"status": "is_button", "id": zapis_id})
            await sender.message(user_id, "want_to_add_button", kb.reply_table(2, *sender.text("yes_not").split(), is_keys=False))

        case "is_button":
            is_true = sender.text("yes_not").split().index(msg.text) == 0
            if is_true:
                await state.set_data({"status": "link", "id": data["id"]})
                await sender.message(user_id, "write_button_link", ReplyKeyboardRemove())
            else:
                await state.set_data({"status": "time", "id": data["id"], "link": "", "text": ""})
                await sender.message(user_id, "write_time", kb.reply("now"))
        
        case "link":
            await state.set_data({"status": "text", "id": data["id"], "link": msg.text})
            await sender.message(user_id, "write_button_text")

        case "text":
            if len(msg.text) > 30:
                await sender.message(user_id, "wrong_text")
            else:
                await state.set_data({"status": "time", "id": data["id"], "link": data["link"], "text": msg.text})
                await sender.message(user_id, "write_time", kb.reply("now"))
        
        case "time":
            try:
                if msg.text == sender.text("now"):
                    date = datetime.now() - time_difference
                else:
                    date = datetime.strptime(msg.text, "%d.%m.%Y %H:%M") - time_difference
                DB.commit("update repetitions set button_text = ?, button_link = ?, time_to_send = ? where id = ?",
                          [data["text"], data["link"], date, data["id"]])
                await sender.message(user_id, "message_to_send")

                message_id = DB.get("select message_id from repetitions where id = ?", [data["id"]], True)[0]
                await bot.copy_message(user_id, user_id, message_id, reply_markup=kb.link(data["text"], data["link"]) if data["link"] else None)
                await sender.message(user_id, "type_confirm", ReplyKeyboardRemove(), sender.text("confirm"))
                await state.set_data({"status": "confirm", "id": data["id"]})
            except:
                await sender.message(user_id, "wrong_date")

        case "confirm":
            await state.set_state(UserState.default)
            if msg.text.lower() == sender.text("confirm").lower():
                await sender.message(user_id, "message_sended")
                DB.commit("update repetitions set confirmed = ? where id = ?",
                          [True, data["id"]])
            else:
                await sender.message(user_id, "aborted")


# Установка базы данных
@dp.message(F.document)
async def set_databse(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    role = DB.get('select role from users where telegram_id = ?', [user_id], True)
    if not role:
        return
    if role[0] != "admin":
        return
    
    doc = msg.document
    if doc.file_name.split(".")[-1] != "sqlite3":
        return
    
    file = await bot.get_file(doc.file_id)
    await bot.download_file(file.file_path, path.join("database", "db.sqlite3"))
