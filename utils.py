import json
import os

DATA_FILE = "database.json"

# Загрузка базы данных с безопасной инициализацией
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"stories": [], "users": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Гарантируем наличие ключей
    if "stories" not in data:
        data["stories"] = []
    if "users" not in data:
        data["users"] = {}

    return data

# Сохранение базы данных
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Получение или создание пользователя
def get_user(data, user_id):
    user_id = str(user_id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "kindness_points": 0,
            "likes_given": 0
        }
    return data["users"][user_id]

# Определение ранга доброты
def get_kindness_rank(points):
    if points >= 30:
        return "🥇 Золото"
    elif points >= 15:
        return "🥈 Серебро"
    else:
        return "🥉 Бронза"
