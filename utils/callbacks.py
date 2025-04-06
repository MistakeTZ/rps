from aiogram import F
from aiogram.types.callback_query import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hlink
from loader import dp, bot, sender
import asyncio
import importlib
from os import path

from config import get_env, get_config

import utils.kb as kb
from states import UserState


# Возвращение в меню
@dp.callback_query(F.data == "back")
async def menu_handler(clbck: CallbackQuery, state: FSMContext) -> None:
    user_id = clbck.from_user.id
    await sender.edit_message(clbck.message, "menu")
    await state.set_state(UserState.default)


# Выбор игры
@dp.callback_query(F.data.startswith("game_"))
async def game_handler(clbck: CallbackQuery, state: FSMContext) -> None:
    user_id = clbck.from_user.id
    game = clbck.data.split("_")[-1]

    game = importlib.import_module(f"games.{game}")
    await game.start_game(user_id, state)
