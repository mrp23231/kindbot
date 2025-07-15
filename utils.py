import json
import os

DATA_FILE = "database.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"stories": [], "users": {}, "subscriptions": {}, "thanks": {}, "author_of_week": None}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    user_id = str(user_id)
    if "users" not in data:
        data["users"] = {}
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "points": 0,
            "thanks": 0,
            "badge": "",
            "username": "",
        }
    return data["users"][user_id]

def update_user_points(data, user_id, delta):
    user = get_user(data, user_id)
    user["points"] += delta

def add_thanks(data, to_user_id, from_user_id, story_index):
    key = f"{story_index}_{from_user_id}"
    if key in data.get("thanks", {}):
        return False  # Уже благодарил
    data.setdefault("thanks", {})[key] = to_user_id
    user = get_user(data, to_user_id)
    user["thanks"] += 1
    update_user_points(data, to_user_id, 1)
    return True

def get_badge(user, user_id, data):
    badge = ""
    if str(user_id) == str(data.get("author_of_week")):
        badge = "🥇 Автор недели"
    elif user["thanks"] >= 10:
        badge = "🙏 Душа компании"
    elif user["points"] >= 20:
        badge = "💡 Мотиватор"
    return badge
