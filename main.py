import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")

if RENDER_URL and not RENDER_URL.startswith("https://"):
    RENDER_URL = f"https://{RENDER_URL}"

bot = telebot.TeleBot(TOKEN, threaded=False)
genai.configure(api_key=API_KEY)

app = Flask(__name__)

# --- WEBHOOK ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Error", 403

# --- ASIL İCRAAT ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Denenecek model isimleri (Google bazen birini, bazen diğerini istiyor)
    model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash-latest']
    
    success = False
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(message.text)
            if response and response.text:
                bot.reply_to(message, response.text)
                success = True
                break # Cevap verildiyse döngüden çık
        except Exception:
            continue # Bu isim olmadıysa sonrakini dene

    if not success:
        bot.reply_to(message, "Ayhan Bey, Google modeline hala bağlanamıyorum. Lütfen API anahtarınızı kontrol edin veya 1 dakika sonra tekrar deneyin.")

@app.route('/')
def home():
    return "SİSTEM AYAKTA"

# Webhook'u her açılışta tazeleyelim
bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
