import os
import telebot
import time
from flask import Flask
import threading

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ID = "1568398578"

# Token kontrolü
print(f"DEBUG: Token yüklendi mi? {'Evet' if TOKEN else 'HAYIR!'}")
bot = telebot.TeleBot(TOKEN)

@app.route('/')
def home():
    return "Bot Yayında"

def test_mesaj():
    print("DEBUG: Mesaj gönderme denemesi başlıyor...")
    try:
        bot.send_message(ID, "🚀 Bot test mesajı gönderiyor. Eğer bunu görüyorsan her şey tamamdır!")
        print("DEBUG: Mesaj başarıyla gönderildi!")
    except Exception as e:
        print(f"DEBUG: HATA OLUŞTU! {e}")

if __name__ == "__main__":
    # Botu hemen başlat
    threading.Thread(target=test_mesaj).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
