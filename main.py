import os
import telebot
from groq import Groq
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
# URL'yi loglarınızdaki adrese göre sabitledim
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

bot = telebot.TeleBot(TOKEN, threaded=False)
client = Groq(api_key=GROQ_KEY)

app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Llama 3 modelini en sade haliyle çağırıyoruz
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": message.text}]
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"Sistem Notu: {str(e)}")

@app.route('/')
def home():
    return "BOT CALISIYOR"

if __name__ == "__main__":
    # Webhook'u her seferinde temizleyip yeniden kuralım
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
