import os
import telebot
import yfinance as yf
import google.generativeai as genai
import threading
import time
from flask import Flask

app = Flask(__name__)

# Render'daki gizli ayarlardan okuyacak
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578"

bot = telebot.TeleBot(TOKEN)

@app.route('/')
def home():
    return "Bot Yayında"

def stock_bot():
    if not API_KEY or not TOKEN:
        print("HATA: Ayarlar eksik!")
        return
        
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-001')
    bot.send_message(ID, "✅ Bot sıfırdan güvenli başlatıldı.")
    
    while True:
        try:
            hisse = "THYAO.IS"
            ticker = yf.Ticker(hisse)
            price = ticker.fast_info['last_price']
            response = model.generate_content(f"{hisse} hissesi {price} TL. Yorumla.")
            bot.send_message(ID, f"🚀 {hisse}: {response.text}")
        except Exception as e:
            print(f"Hata: {e}")
        time.sleep(3600) # 1 saat bekle

if __name__ == "__main__":
    threading.Thread(target=stock_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
