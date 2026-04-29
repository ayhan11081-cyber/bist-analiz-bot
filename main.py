import os
import time
import telebot
import yfinance as yf
import google.generativeai as genai
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
ID = "1568398578"

# --- KURULUM ---
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Webhook Ayarı (Telegram'a "Bana mesaj gelirse şu adrese yolla" diyoruz)
webhook_url = f"{RENDER_URL}/{TOKEN}"
bot.remove_webhook()
bot.set_webhook(url=webhook_url)

# --- İŞLEMLER ---
def tarama_yap():
    hisseler = ["THYAO.IS", "ASELS.IS", "TUPRS.IS", "BIMAS.IS"]
    for hisse in hisseler:
        try:
            ticker = yf.Ticker(hisse)
            df = ticker.history(period="1mo")
            if df.empty: continue
            
            fiyat = df['Close'].iloc[-1]
            prompt = f"Hisse: {hisse}, Fiyat: {fiyat:.2f}. Teknik analiz yap. AL/SAT sinyali varsa üret."
            response = model.generate_content(prompt)
            
            if "AL" in response.text.upper() or "SAT" in response.text.upper():
                bot.send_message(ID, f"📊 **{hisse} Sinyali:**\n{response.text}")
        except Exception as e:
            print(f"Hata: {e}")

# Arka Plan Görevi (Her saat başı otomatik çalışır)
scheduler = BackgroundScheduler()
scheduler.add_job(tarama_yap, 'interval', hours=1)
scheduler.start()

# --- WEB SUNUCU ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def home(): return "Bot Aktif ve Hata Yok"
