import os
import telebot
import yfinance as yf
import google.generativeai as genai
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# Konfigürasyon
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
ID = "1568398578"

# Model ve Bot
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Webhook'u Telegram'a kaydet
bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")

# 1. Otomatik Tarama Görevi
def tarama_yap():
    hisseler = ["THYAO.IS", "ASELS.IS", "TUPRS.IS", "BIMAS.IS"]
    for hisse in hisseler:
        try:
            ticker = yf.Ticker(hisse)
            df = ticker.history(period="1mo")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            prompt = f"Hisse: {hisse}, Fiyat: {close:.2f}. Teknik analiz yap. AL/SAT sinyali varsa üret."
            response = model.generate_content(prompt)
            
            if "AL" in response.text.upper() or "SAT" in response.text.upper():
                bot.send_message(ID, f"📊 **{hisse} Sinyali:**\n{response.text}")
        except Exception as e:
            print(f"Tarama Hatası: {e}")

# 2. Flask Webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def home(): return "Sistem 7/24 Aktif"

# 3. Başlatıcı
if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(tarama_yap, 'interval', hours=1) # Her saat başı tarar
    scheduler.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
