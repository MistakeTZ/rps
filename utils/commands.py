from aiogram import F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hlink
from loader import dp, bot, sender
from os import path
from datetime import datetime

from config import get_env, get_config
import utils.kb as kb
from states import UserState
from database.model import DB
from support.tasks import menu


# Команда старта бота
@dp.message(CommandStart())
async def command_start_handler(msg: Message, state: FSMContext) -> None:
    user_id = msg.from_user.id
    nickname = DB.get("select nickname from users where telegram_id = ?", [user_id], True)
    if nickname:
        if nickname[0]:
            await menu(user_id, nickname[0])
            return

    else:
        print("New user:", user_id)
        DB.commit("insert into users (telegram_id, name, username, registered) values (?, ?, ?, ?)", 
                  [user_id, msg.from_user.full_name, msg.from_user.username, datetime.now()])

    await sender.message(user_id, "hello")
    await state.set_state(UserState.name)


# Команда рассылки
@dp.message(Command("mailing"))
async def command_settings(msg: Message, state: FSMContext) -> None:
    user_id = msg.from_user.id
    role = DB.get("select role from users where telegram_id = ?", [user_id], True)
    if not role:
        await sender.message(user_id, "not_allowed")
        return
    if role[0] != "admin":
        await sender.message(user_id, "not_allowed")
        return

    await sender.message(user_id, "write_message_for_mailing")
    await state.set_state(UserState.mailing)
    await state.set_data({"status": "begin"})


# Команда получения БД
@dp.message(Command("get"))
async def command_settings(msg: Message, state: FSMContext) -> None:
    user_id = msg.from_user.id
    role = DB.get('select role from users where telegram_id = ?', [user_id], True)
    if not role:
        return
    if role[0] != "admin":
        await sender.message(user_id, "not_allowed")
        return
    await sender.send_media(user_id, "file", "db.sqlite3", path="database", name="db")
