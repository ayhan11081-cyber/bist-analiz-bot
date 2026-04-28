import os
import time
import threading
import telebot
import yfinance as yf
import google.generativeai as genai
from flask import Flask

# Konfigürasyon
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578" # Sizin ID

# Model ve Bot Kurulumu
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home(): return "Sistem 7/24 Aktif"

# Teknik Analiz
def analiz_et():
    hisseler = ["THYAO.IS", "ASELS.IS", "TUPRS.IS", "BIMAS.IS"] # Burayı hisseler.txt dosyanızdan da okutabilirsiniz
    for hisse in hisseler:
        try:
            ticker = yf.Ticker(hisse)
            df = ticker.history(period="1mo")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            prompt = f"Hisse: {hisse}, Fiyat: {close:.2f}. Teknik analiz yap ve sadece AL/SAT sinyali oluştuysa kısa bir yorum yaz."
            response = model.generate_content(prompt)
            
            # Sadece yapay zeka bir "AL" veya "SAT" sinyali ürettiyse mesaj at
            if "AL" in response.text.upper() or "SAT" in response.text.upper():
                bot.send_message(ID, f"🚀 **{hisse} Sinyal:**\n{response.text}")
                
            time.sleep(10) # API kotaları için bekleme
        except Exception as e:
            print(f"Hata: {e}")

# Arka plan döngüsü (Siz komut yazmasanız da çalışır)
def background_worker():
    while True:
        analiz_et()
        time.sleep(3600) # Her 1 saatte bir tarar

if __name__ == "__main__":
    # Web sunucusunu başlat (Render'ı canlı tutmak için)
    threading.Thread(target=background_worker, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
