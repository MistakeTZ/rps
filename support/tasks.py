from database.model import DB
from loader import sender
from utils import kb


async def menu(user_id, nickname=None):
    if not nickname:
        nickname = DB.get("select nickname from users where telegram_id = ?", [user_id], True)[0]
    await sender.message(user_id, "menu", kb.buttons(False, "menu"))
