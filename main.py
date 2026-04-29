import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# AYARLAR (Render'dan otomatik çekilir)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

# Kurulum
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=API_KEY)

# Hata veren model ismini en stabil haliyle güncelledik
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

# Webhook Ayarı (Burası artık sorunsuz çalışıyor)
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Hata', 403

# MESAJI İŞLEYEN KISIM
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # AI'dan cevap bekleme
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        # Hata olursa Telegram'a detay yazdır (Çözmek için)
        bot.reply_to(message, f"Yapay Zeka Hatası: {str(e)}")

@app.route('/')
def index():
    return "Bot Aktif!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
