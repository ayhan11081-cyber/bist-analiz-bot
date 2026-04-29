import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 1. AYARLAR - Render'dan çekiyoruz
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
# URL'nin sonundaki "/" işaretini kod içinde biz temizliyoruz (Hata payı sıfır)
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL").strip("/")

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=API_KEY)

# Gemini 1.5 Flash Modelini en garanti sürümle çağırıyoruz
model = genai.GenerativeModel('models/gemini-1.5-flash')

app = Flask(__name__)

# 2. WEBHOOK KURULUMU (Hata payını bitiren kısım)
@app.route('/setup', methods=['GET'])
def setup():
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    s = bot.set_webhook(url=webhook_url)
    if s:
        return f"BAĞLANTI KURULDU! Mesajlar buraya gelecek: {webhook_url}", 200
    return "BAĞLANTI BAŞARISIZ!", 400

# 3. MESAJ YAKALAMA (Loglarda 404 almamak için)
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Hatalı İstek', 403

# 4. BOT CEVAP SİSTEMİ
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Mesaj geldiğinde hemen cevap ver (İcraat başladığını gör diye)
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        # Hata olsa bile bot size "Neden hata aldığını" Telegram'dan söylesin
        bot.reply_to(message, f"Yapay Zeka Hatası Aldım Ayhan Bey: {str(e)}")

@app.route('/')
def home():
    return "SUNUCU AYAKTA - SİSTEM ÇALIŞIYOR"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
