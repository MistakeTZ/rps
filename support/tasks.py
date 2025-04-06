from database.model import DB
from loader import sender
from utils import kb
from config import get_config


async def menu(user_id, nickname=None):
    # if not nickname:
    #     nickname = DB.get("select nickname from users where telegram_id = ?", [user_id], True)[0]

    games = get_config("games")
    game_buttons = []
    for game in games:
        game_buttons.extend([game["name"], "game_" + game["id"]])
        
    await sender.message(user_id, "menu", kb.buttons(False, *game_buttons))
