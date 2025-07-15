import json
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def load_data():
    try:
        with open("database.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "stories": [], "subscriptions": {}}

def save_data(data):
    with open("database.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, uid, username=None):
    key = str(uid)
    users = data.setdefault("users", {})
    if key not in users:
        users[key] = {"username": username or f"user{uid}", "points": 0, "thanks": 0}
    return users[key]

def get_badge(user, uid, data):
    return "✨ Автор недели" if str(uid) in data.get("author_of_week", []) else None

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📖 Читать истории"))
    kb.add(KeyboardButton("✍️ Поделиться историей"))
    kb.add(KeyboardButton("👤 Профиль"))
    kb.add(KeyboardButton("🧱 Стена благодарности"))
    return kb
