import os
import telebot
import yfinance as yf
import google.generativeai as genai
import threading
import time
from flask import Flask

# 1. Flask ve Bot Yapılandırması
app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-001')
bot = telebot.TeleBot(TOKEN)

@app.route('/')
def home():
    return "Bot ve Web Sunucusu Aktif!"

# 2. Yardımcı Fonksiyonlar
def hisseleri_yukle():
    try:
        # GitHub'daki hisseler.txt dosyasını okur
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            return [line.strip() + ".IS" for line in f if line.strip()]
    except FileNotFoundError:
        return []

def analiz_et(sembol):
    try:
        ticker = yf.Ticker(sembol)
        data = ticker.history(period="1d")
        if data.empty: return "Fiyat verisi şu an alınamıyor."
        
        fiyat = data['Close'].iloc[-1]
        prompt = f"""
        Hisse: {sembol}, Son Kapanış Fiyatı: {fiyat:.2f} TL.
        Sen profesyonel bir borsa analiz uzmanısın.
        Teknik analiz yap ve "AL/SAT/BEKLE" sinyali üret.
        Eğer piyasada önemli bir durum varsa belirt.
        Cevabını kısa, net ve profesyonel tut.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Analiz hatası: {str(e)}"

# 3. Komutlar
@bot.message_handler(commands=['ping'])
def ping_komutu(message):
    bot.reply_to(message, "✅ Bot aktif, sistem çalışıyor.")

@bot.message_handler(commands=['tarama'])
def tarama_komutu(message):
    hisseler = hisseleri_yukle()
    if not hisseler:
        bot.reply_to(message, "Hisseler listesi boş! 'hisseler.txt' dosyasını kontrol edin.")
        return

    bot.reply_to(message, f"🚀 Toplam {len(hisseler)} hisse taranıyor. Lütfen bekleyin...")
    
    for hisse in hisseler:
        analiz = analiz_et(hisse)
        # Hız için 1 saniye bekleme
        time.sleep(1) 
        bot.send_message(ID, f"📊 **{hisse.replace('.IS', '')}**\n{analiz}")

# 4. BOT BAŞLATMA (KRİTİK KISIM)
# Bu kısım if bloğunun dışında olduğu için Render/Gunicorn bunu direkt görür ve başlatır.
def bot_polling():
    bot.infinity_polling()

threading.Thread(target=bot_polling, daemon=True).start()

# Flask Web Sunucusu
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
