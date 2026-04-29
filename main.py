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

app = Flask(__name__)

# ÇALIŞAN MODELİ OTOMATİK BULAN FONKSİYON
def get_model():
    try:
        # Google'dan sizin için aktif olan modelleri listelemesini istiyoruz
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # 1.5 flash varsa onu seç, yoksa ilk bulduğun çalışan modeli ver
                if 'gemini-1.5-flash' in m.name:
                    return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-pro') # Yedek plan
    except:
        return genai.GenerativeModel('models/gemini-1.5-flash')

# Webhook rotası
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

# MESAJ İŞLEME
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Her mesajda çalışan modeli tazeleyerek soruyoruz
        current_model = get_model()
        response = current_model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Sistem Notu: {str(e)}")

@app.route('/')
def home():
    return "BOT AKTIF"

# Webhook'u tazele
bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
