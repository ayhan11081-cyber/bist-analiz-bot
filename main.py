import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
# URL'nin başına https:// eklediğimizden emin oluyoruz
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
if not RENDER_URL.startswith("https://"):
    RENDER_URL = f"https://{RENDER_URL}"

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=API_KEY)

# Model tanımlamasını en yalın haliyle yapıyoruz
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

# Webhook rotası
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# BOT CEVAP KISMI
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Gemini bağlantısı
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        # Hata olursa model ismini otomatik düzelten alternatif deneme
        try:
            alt_model = genai.GenerativeModel('models/gemini-1.5-flash')
            response = alt_model.generate_content(message.text)
            bot.reply_to(message, response.text)
        except:
            bot.reply_to(message, f"Bağlantı Hatası: {str(e)}")

@app.route('/')
def home():
    return "Sistem Yayında"

if __name__ == "__main__":
    # Webhook'u her açılışta tekrar kuruyoruz
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=10000)
