import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

bot = telebot.TeleBot(TOKEN, threaded=False)

# Google AI Konfigürasyonu
genai.configure(api_key=API_KEY)

app = Flask(__name__)

# --- WEBHOOK GÜVENLİĞİ ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

# --- MESAJ İŞLEME (EN GARANTİ YÖNTEM) ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # 'models/' ön ekini kaldırarak en kararlı ismi kullanıyoruz
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(message.text)
        
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Ayhan Bey, model cevap üretemedi. Lütfen soruyu değiştirin.")
            
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            # Eğer hala 404 verirse, alternatif ismi dene
            try:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(message.text)
                bot.reply_to(message, response.text)
            except:
                bot.reply_to(message, "Model isim hatası: Google bu ismi kabul etmiyor.")
        elif "429" in error_msg:
            bot.reply_to(message, "Ayhan Bey, ücretsiz kullanım limitiniz dolmuş. Biraz bekleyelim.")
        else:
            bot.reply_to(message, f"Sistem hatası: {error_msg}")

@app.route('/')
def home():
    return "SİSTEM AKTİF"

# Webhook ayarlarını tazele
bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
