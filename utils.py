import json
import os

DATA_FILE = "database.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"stories": [], "users": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "users" not in data:
        data["users"] = {}
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "likes_given": 0,
            "kindness_points": 0,
            "submitted": 0
        }
    return data["users"][uid]

def update_user_points(user, amount):
    user["kindness_points"] += amount
    if user["kindness_points"] < 0:
        user["kindness_points"] = 0
