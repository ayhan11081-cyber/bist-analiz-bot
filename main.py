import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# --- AYARLAR (Boşlukları otomatik temizler) ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")

# URL'nin başında https:// olduğundan emin olalım
if RENDER_URL and not RENDER_URL.startswith("https://"):
    RENDER_URL = f"https://{RENDER_URL}"

# Botu ve Yapay Zekayı Başlat (threaded=False daha kararlıdır)
bot = telebot.TeleBot(TOKEN, threaded=False)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

app = Flask(__name__)

# --- WEBHOOK KURULUMU ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        # Loglarda mesajı görelim (İcraat takibi için)
        print(f"YENİ MESAJ GELDİ: {update.message.text if update.message else 'Mesaj içeriği boş'}")
        bot.process_new_updates([update])
        return "Tamam", 200
    return "Hata", 403

# --- ASIL İCRAAT (MESAJI CEVAPLAMA) ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    print(f"Mesaj işleniyor: {message.text}")
    try:
        # Gemini'ye soralım
        response = model.generate_content(message.text)
        
        if response and response.text:
            bot.reply_to(message, response.text)
            print("Cevap başarıyla gönderildi.")
        else:
            bot.reply_to(message, "Yapay zeka boş cevap döndürdü, tekrar deneyin.")
            
    except Exception as e:
        error_msg = f"Hata oluştu Ayhan Bey: {str(e)}"
        print(error_msg)
        bot.reply_to(message, error_msg)

@app.route('/')
def home():
    return "BOT AKTİF VE YAYINDA"

# Webhook'u Telegram'a otomatik kaydet (Her açılışta)
bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
print(f"Webhook ayarlandı: {RENDER_URL}/{TOKEN}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
