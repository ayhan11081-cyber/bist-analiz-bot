import os
import telebot
import yfinance as yf
import google.generativeai as genai
from flask import Flask, request

# 1. AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") 
ID = "1568398578"

# 2. KURULUM
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
app = Flask(__name__)

# --- OTOMATİK BAĞLANTI (Webhook'u Koda Gömdük) ---
webhook_url = f"{RENDER_URL}/{TOKEN}"
bot.remove_webhook()
bot.set_webhook(url=webhook_url)

# 3. MESAJ YÖNETİMİ
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def home():
    return "Bot Yayında!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
