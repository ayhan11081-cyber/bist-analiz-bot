import os
import telebot
import yfinance as yf
import google.generativeai as genai
import threading
import time
import pandas as pd
from flask import Flask

# 1. Konfigürasyon
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578"

# Model Ayarları (Hata almamak için 'gemini-1.5-flash' kullandık)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home(): return "Sistem Aktif"

# 2. Teknik Analiz Hesaplama
def hesapla_teknik_gostergeler(df):
    try:
        # RSI (14 periyot)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD (12, 26, 9)
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        
        return df.iloc[-1]
    except:
        return None

# 3. Analiz Motoru
def analiz_et(sembol):
    try:
        ticker = yf.Ticker(sembol)
        df = ticker.history(period="1mo")
        if df.empty: return "Veri alınamadı."
        
        gostergeler = hesapla_teknik_gostergeler(df)
        if gostergeler is None: return "İndikatör hesaplanamadı."
        
        fiyat = gostergeler['Close']
        rsi = gostergeler['RSI']
        macd = gostergeler['MACD']
        
        prompt = f"""
        Hisse: {sembol}
        Güncel Fiyat: {fiyat:.2f} TL
        RSI: {rsi:.2f} (30 altı aşırı satım, 70 üstü aşırı alım)
        MACD: {macd:.4f}
        
        Yukarıdaki teknik verilere bakarak; trend yönünü belirle, 
        kısa ve net bir AL/SAT/BEKLE sinyali üret.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Analiz hatası: {str(e)}"

# 4. Yardımcılar ve Komutlar
def hisseleri_yukle():
    try:
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            return [line.strip() + ".IS" for line in f if line.strip()]
    except:
        return []

@bot.message_handler(commands=['tarama'])
def tarama_komutu(message):
    hisseler = hisseleri_yukle()
    if not hisseler:
        bot.reply_to(message, "Hisseler listesi boş!")
        return
        
    bot.reply_to(message, f"🚀 {len(hisseler)} hisse için analiz başlıyor...")
    
    for hisse in hisseler:
        analiz = analiz_et(hisse)
        bot.send_message(ID, f"📊 **{hisse.replace('.IS', '')}**\n{analiz}")
        time.sleep(2) 

# 5. Ana Çalıştırma (Hata düzeltmeleri eklendi)
if __name__ == "__main__":
    # Eski bağlantıları temizle (409 Conflict hatasını çözer)
    bot.remove_webhook()
    
    # Botu arka planda başlat
    threading.Thread(target=bot.infinity_polling, kwargs={'none_stop': True}, daemon=True).start()
    
    # Web sunucusunu başlat
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
