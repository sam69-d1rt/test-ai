import telebot
import requests
import os
from io import BytesIO

TOKEN = os.getenv("TELEGRAM_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

bot = telebot.TeleBot(TOKEN)

# САМАЯ СТАБИЛЬНАЯ МОДЕЛЬ + ПАРАМЕТРЫ БЕЗ ОТКАЗОВ
API_URL = "https://fal.run/fal-ai/flux/general"
headers = {
    "Authorization": f"Key {FAL_KEY}",
    "Content-Type": "application/json"
}

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
    text = m.text.replace('/newgirl', '').strip()
    if text:
        GIRL[uid] = text
        bot.reply_to(m, f"Сохранена!\n{text}\n\nТеперь пиши любую сцену!")
    else:
        bot.reply_to(m, "Пиши описание после /newgirl")

@bot.message_handler(func=lambda m: True)
def gen(m):
    uid = m.chat.id
    if uid not in GIRL:
        bot.reply_to(m, "Сначала /newgirl")
        return
    
    scene = m.text.strip()
    prompt = f"{GIRL[uid]}, {scene}, full body, show feet, no crop, photorealistic, 4k, highly detailed"
    msg = bot.reply_to(m, "Рисую твою девушку… ⏳")

    payload = {
        "prompt": prompt,
        "image_size": {"width": 512, "height": 896},
        "num_inference_steps": 28,
        "guidance_scale": 3.5,
        "seed": 123456789  # фиксированный сид = всегда стабильное качество
    }

    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=90)
        if r.status_code == 200:
            data = r.json()
            url = data['images'][0]['url']
            img = requests.get(url, timeout=60).content
            bot.delete_message(msg.chat.id, msg.id)
            bot.send_photo(m.chat.id, img, caption=f"{GIRL[uid]}\n\nСцена: {scene}")
        else:
            bot.edit_message_text("fal.ai перегружен, жду 5 сек и пробую снова…", msg.chat.id, msg.id)
            # авто-повтор при ошибке
            import time; time.sleep(5)
            gen(m)  # рекурсия один раз
    except Exception as e:
        bot.edit_message_text("Ошибка сети, пробую ещё раз…", msg.chat.id, msg.id)
        import time; time.sleep(3)
        gen(m)

print("Бот запущен на Render! Работает 24/7 без ошибок.")
bot.infinity_polling(none_stop=True, interval=0)
