import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

bot = telebot.TeleBot(TOKEN, threaded=False)
genai.configure(api_key=API_KEY)

# Modeli en garanti isimle tanımlayalım
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        if "429" in str(e):
            bot.reply_to(message, "Ayhan Bey, Google ücretsiz kullanım limitiniz dolmuş. Lütfen 1 dakika bekleyip tekrar deneyin.")
        else:
            bot.reply_to(message, f"Hata: {str(e)}")

@app.route('/')
def home():
    return "BOT CALISIYOR"

bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
