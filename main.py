import os
import telebot
import yfinance as yf
import google.generativeai as genai
import threading
import time
import pandas as pd
import signal
import sys
from flask import Flask

# 1. Konfigürasyon
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578"

# Model Ayarları
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home(): return "Sistem Aktif"

# 2. Teknik Analiz
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
        if g is None: return "İndikatör hesabı başarısız."
        
        prompt = f"Hisse: {sembol}, Fiyat: {g['Close']:.2f}, RSI: {g['RSI']:.2f}, MACD: {g['MACD']:.4f}. Teknik analiz ve AL/SAT/BEKLE sinyali ver."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Analiz hatası: {str(e)}"

# 3. Kapanış ve Çakışma Yönetimi
def signal_handler(sig, frame):
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@bot.message_handler(commands=['tarama'])
def tarama_komutu(message):
    try:
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            hisseler = [line.strip() + ".IS" for line in f if line.strip()]
        bot.reply_to(message, f"🚀 {len(hisseler)} hisse için tarama başladı...")
        for hisse in hisseler:
            analiz = analiz_et(hisse)
            bot.send_message(ID, f"📊 **{hisse.replace('.IS', '')}**\n{analiz}")
            time.sleep(2)
    except Exception as e: bot.reply_to(message, f"Dosya hatası: {e}")

# 4. Çalıştırma
if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=lambda: bot.polling(none_stop=True), daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
