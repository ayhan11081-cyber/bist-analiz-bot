import os
import telebot
import yfinance as yf
import google.generativeai as genai
from flask import Flask, request

# Konfigürasyon
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578"

# Bot ve Model Kurulumu
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Flask Kurulumu
app = Flask(__name__)

# Webhook rotası
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# Botun çalışması için bir kök dizin
@app.route('/')
def home():
    return "Bot aktif ve çalışıyor."

# Mesajları dinle
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot çalışıyor!")

if __name__ == "__main__":
    # Webhook'u Telegram'a otomatik tanıtmak için
    # Not: Render'da botun düzgün çalışması için manuel webhook ayarı gerekebilir
    # Ancak bu kod artık hata vermeyecek.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
