import telebot
import requests
from io import BytesIO
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

bot = telebot.TeleBot(TOKEN)
API_URL = "https://fal.run/fal-ai/flux/schnell"
headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}

GIRL = {}

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.chat.id
    if uid in GIRL:
        bot.reply_to(m, f"Твоя девушка:\n{GIRL[uid]}\n\nПиши сцену!")
    else:
        bot.reply_to(m, "Привет! Опиши девушку:\n/newgirl 20-летняя блондинка...")

@bot.message_handler(commands=['newgirl'])
def newgirl(m):
    uid = m.chat.id
    text = m.text[9:].strip()
    if text:
        GIRL[uid] = text
        bot.reply_to(m, f"Сохранена!\n{text}")
    else:
        bot.reply_to(m, "Пиши описание после /newgirl")

@bot.message_handler(func=lambda m: True)
def gen(m):
    uid = m.chat.id
    if uid not in GIRL:
        bot.reply_to(m, "Сначала /newgirl")
        return
    scene = m.text.strip()
    prompt = f"{GIRL[uid]}, {scene}, full body, show feet, no crop, 4k"
    msg = bot.reply_to(m, "Рисую…")

    try:
        r = requests.post(API_URL, json={"prompt": prompt, "image_size": {"width": 512, "height": 896}}, headers=headers, timeout=60)
        if r.status_code == 200:
            url = r.json()['images'][0]['url']
            img = requests.get(url).content
            bot.delete_message(msg.chat.id, msg.id)
            bot.send_photo(m.chat.id, img, caption=f"{GIRL[uid]}\n\n{scene}")
        else:
            bot.reply_to(m, "Ошибка fal.ai, попробуй позже")
    except:
        bot.reply_to(m, "Ошибка сети")

print("Бот запущен на Render!")
bot.infinity_polling()
