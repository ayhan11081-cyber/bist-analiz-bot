import os
import telebot
import yfinance as yf
import google.generativeai as genai
import threading
import time
from flask import Flask

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
ID = "1568398578"

bot = telebot.TeleBot(TOKEN)

@app.route('/')
def home():
    return "Bot Yayında"

# Yeni: Bota mesaj atınca cevap vermesi için
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot çalışıyor! Şimdi analizleri yapmaya hazırım.")

# Yeni: Test mesajı
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Mesajınız alındı! Bot aktif. ID: {message.chat.id}")

def stock_bot():
    # ... (diğer kodlarınız aynı kalabilir)
    # bot.send_message(ID, "✅ Bot sıfırdan güvenli başlatıldı.") # Bunu dilerseniz açabilirsiniz
    
    # Döngü burada çalışmaya devam edecek
    while True:
        # Kodun burası 1 saat uyuyor olabilir, o yüzden test için yukarıdaki 
        # mesaj handler'larını ekledik.
        time.sleep(3600) 

# Flask ve Botu başlat
if __name__ == "__main__":
    threading.Thread(target=stock_bot, daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
