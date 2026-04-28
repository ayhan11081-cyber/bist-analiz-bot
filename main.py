import os
import telebot
import yfinance as yf
import google.generativeai as genai
import threading
import time
from flask import Flask

# 1. Ayarlar
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578"

# Bot ve Web Başlatma
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Flask Sağlık Kontrolü (Render'ın botu kapatmaması için)
@app.route('/')
def home():
    return "Bot ve Web Sunucusu Aktif!"

# 2. Fonksiyonlar
def hisseleri_yukle():
    try:
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            return [line.strip() + ".IS" for line in f if line.strip()]
    except Exception:
        return []

def analiz_et(sembol):
    try:
        ticker = yf.Ticker(sembol)
        data = ticker.history(period="1d")
        if data.empty: return "Veri yok."
        
        fiyat = data['Close'].iloc[-1]
        prompt = f"Hisse: {sembol}, Fiyat: {fiyat:.2f}. Teknik analiz ve AL/SAT/BEKLE sinyali ver."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Hata: {str(e)}"

# 3. Bot Komutları
@bot.message_handler(commands=['ping'])
def ping_komutu(message):
    bot.reply_to(message, "✅ Sistem çalışıyor!")

@bot.message_handler(commands=['tarama'])
def tarama_komutu(message):
    hisseler = hisseleri_yukle()
    bot.reply_to(message, f"🔍 {len(hisseler)} hisse taranıyor...")
    for hisse in hisseler:
        analiz = analiz_et(hisse)
        bot.send_message(ID, f"📊 **{hisse.replace('.IS', '')}**\n{analiz}")
        time.sleep(1)

# 4. Ana Çalıştırma Bloğu (Render Start Command ile tetiklenir)
if __name__ == "__main__":
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-001')
    
    # Botu arka planda başlat
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    
    # Web sunucusunu ön planda başlat (Render bu portu dinler)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
