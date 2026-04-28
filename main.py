import os
import telebot
import yfinance as yf
import google.generativeai as genai
import threading
import time
import pandas as pd
from flask import Flask

# Konfigürasyon
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578"

# Model Ayarı
genai.configure(api_key=API_KEY)
# Versiyon sorununu aşmak için güncel model ismi
model = genai.GenerativeModel('gemini-1.5-flash') 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home(): return "Sistem Aktif"

def hesapla_teknik_gostergeler(df):
    try:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        return df.iloc[-1]
    except: return None

def analiz_et(sembol):
    try:
        ticker = yf.Ticker(sembol)
        df = ticker.history(period="1mo")
        if df.empty: return "Veri yok."
        g = hesapla_teknik_gostergeler(df)
        if g is None: return "İndikatör hatası."
        
        prompt = f"Hisse: {sembol}, Fiyat: {g['Close']:.2f}, RSI: {g['RSI']:.2f}, MACD: {g['MACD']:.4f}. Teknik analiz ve AL/SAT/BEKLE sinyali ver."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Analiz hatası: {str(e)}"

@bot.message_handler(commands=['tarama'])
def tarama_komutu(message):
    try:
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            hisseler = [line.strip() + ".IS" for line in f if line.strip()]
        bot.reply_to(message, "🚀 Analiz başlıyor...")
        for hisse in hisseler:
            analiz = analiz_et(hisse)
            bot.send_message(ID, f"📊 **{hisse.replace('.IS', '')}**\n{analiz}")
            time.sleep(3) # Telegram API hızı için
    except Exception as e: bot.reply_to(message, f"Hata: {e}")

if __name__ == "__main__":
    # 409 hatasını önlemek için webhook'u temizle
    bot.remove_webhook()
    
    # 409'u önleyen asıl ayar: timeout sürelerini uzatıyoruz
    threading.Thread(target=lambda: bot.infinity_polling(timeout=60, long_polling_timeout=60), daemon=True).start()
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
