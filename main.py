import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Bot ve AI Başlatma
bot = telebot.TeleBot(TOKEN, threaded=False)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

# --- WEBHOOK BAĞLANTISI ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Hata", 403

# --- MESAJ YANITLAMA ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Gemini'ye sor ve cevabı gönder
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        # Hata varsa doğrudan Telegram'dan bildir
        bot.reply_to(message, f"Sistem Notu: {str(e)}")

@app.route('/')
def home():
    return "BOT AKTİF"

if __name__ == "__main__":
    # Render URL'sini elle sabitledik (Garantili yol)
    RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    # Render'ın verdiği portu kullan
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
