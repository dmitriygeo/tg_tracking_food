import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

WEATHER_TOKEN = os.getenv("WEATHER_TOKEN")
if not WEATHER_TOKEN:
    raise ValueError("Переменная окружения WEATHER_TOKEN не установлена!")

headers = {
    "Content-Type": "application/json",
    "x-app-id": '94e51803',
    "x-app-key": '95ed09003aa4365b7292b68a54c00b72'
}