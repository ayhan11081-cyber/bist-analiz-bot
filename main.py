import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

# --- BAĞLANTILAR ---
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
app = Flask(__name__)

# --- WEBHOOK AYARI ---
# Render'dan gelen adresi kullanarak Telegram'a "Bana mesajları buraya gönder" der.
webhook_url = f"{RENDER_URL}/{TOKEN}"
bot.remove_webhook()
bot.set_webhook(url=webhook_url)

# --- MESAJ İŞLEME ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Hata oluştu: {e}")

@app.route('/')
def home():
    return "Bot Aktif ve Çalışıyor."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
