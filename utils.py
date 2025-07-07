import json
import os

DATA_FILE = "database.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "stories": [],
            "users": {}  # user_id: {likes_given: int, kindness_points: int}
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {
            "likes_given": 0,
            "kindness_points": 0
        }
    return data["users"][str(user_id)]

def get_kindness_rank(points: int) -> str:
    if points >= 30:
        return "🥇 Золото"
    elif points >= 15:
        return "🥈 Серебро"
    else:
        return "🥉 Бронза"
