from aiogram import F
from loader import dp, sender, bot
from aiogram.fsm.context import FSMContext
from utils import kb
from random import randrange
from database.model import DB
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from states import UserState
import asyncio


games = {}
allow_moves = ["🌧", "🔥", "🌳", "🌚"]


class RPS:
    user_id = 0
    round = 1
    cycle = 0
    player = 0
    bot = 0
    nickname = ""
    opponent = "GoBot"
    moves = allow_moves.copy()
    bot_moves = allow_moves.copy()


    def __init__(self, user_id: int, nickname: str):
        self.user_id = user_id
        self.nickname = nickname

    def get_winner(index, bot_index):
        if index - bot_index == -1 or index - bot_index == 3:
            return "player"
        elif bot_index - index == -1 or bot_index - index == 3:
            return "bot"
        else:
            return "draw"

    async def end_game(self):
        winner = self.nickname if self.player > self.bot else self.opponent
        await sender.message(self.user_id, "game_over", ReplyKeyboardRemove(),
                            winner, self.nickname, self.player,
                            self.bot, self.opponent)

    async def check_move(self, move: str):
        if move in self.moves:
            self.moves.remove(move)
            bot_move = self.bot_moves[randrange(len(self.bot_moves))]
            self.bot_moves.remove(bot_move)
            return bot_move
        else:
            await sender.message(self.user_id, "wrong_move")
            return False


    async def move(self, player_move: str = None, bot_move: str = None):
        if player_move:
            index = allow_moves.index(player_move)
            bot_index = allow_moves.index(bot_move)

            winner = RPS.get_winner(index, bot_index)
            
            if winner == "player":
                await sender.message(self.user_id, "win")
                self.player += 1
            elif winner == "bot":
                await sender.message(self.user_id, "lose")
                self.bot += 1
            else:
                await sender.message(self.user_id, "draw")
                await asyncio.sleep(1)
                return await self.move()

            await asyncio.sleep(1)
            self.round += 1
            self.cycle = 0
            self.bot_moves = allow_moves.copy()
            self.moves = allow_moves.copy()

            if max(self.bot, self.player) == 3:
                await self.end_game()
                return False

            await bot.send_message(self.user_id, self.round_text())
            await asyncio.sleep(1)

        if not self.moves:
            self.moves = allow_moves.copy()
            self.bot_moves = allow_moves.copy()
        await sender.message(self.user_id, "your_move", kb.reply_table(4, *self.moves, is_keys=False))
        return True

    def round_text(self):
        return sender.text("round", self.round, self.nickname, self.player, self.bot, self.opponent)

    def __str__(self):
        return self.round_text()


async def start_game(user_id: int, state: FSMContext):
    nickname = DB.get("select nickname from users where telegram_id = ?", [user_id], True)[0]
    games[user_id] = RPS(user_id, nickname)

    await sender.message(user_id, "rps_start", kb.buttons(True, "start_game", "start_rps"))


@dp.callback_query(F.data == "start_rps")
async def start_rps(clbck: CallbackQuery, state: FSMContext) -> None:
    user_id = clbck.from_user.id
    await state.set_state(UserState.rps)
    game = games[user_id]
    await bot.send_message(user_id, game.round_text())
    await asyncio.sleep(1)
    await game.move()


@dp.message(UserState.rps, F.text)
async def move_handler(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    game = games[user_id]

    bot_move = await game.check_move(msg.text)
    await state.set_state(UserState.default)
    if not bot_move:
        await asyncio.sleep(1)
        await game.move()
    else:
        await bot.send_message(user_id, bot_move)
        await asyncio.sleep(1)
        if not await game.move(msg.text, bot_move):
            await state.set_state(UserState.default)
            games[user_id] = None
    await state.set_state(UserState.rps)
