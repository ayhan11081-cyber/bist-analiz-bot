import os
import telebot
import threading
from flask import Flask

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ID = "1568398578"

# Botu burada tanımlıyoruz
bot = telebot.TeleBot(TOKEN)

# Hata ayıklama mesajı
print(f"DEBUG: Token yüklendi mi? {'Evet' if TOKEN else 'HAYIR!'}")

@app.route('/')
def home():
    return "Bot Yayında"

# Botun çalışıp çalışmadığını test eden fonksiyon
def test_mesaj():
    print("DEBUG: Mesaj gönderme denemesi başlıyor...")
    try:
        bot.send_message(ID, "🚀 Bot başarıyla başlatıldı ve size ulaştı!")
        print("DEBUG: Mesaj başarıyla gönderildi!")
    except Exception as e:
        print(f"DEBUG: HATA OLUŞTU! {e}")

# --- İŞTE BURASI ÇOK ÖNEMLİ ---
# Botu ve thread'i if bloğunun dışında başlatıyoruz ki Gunicorn bunu görsün!
threading.Thread(target=test_mesaj).start()

# Gunicorn ile çalıştığı için app.run() burada kullanılmaz, 
# Gunicorn zaten dosyayı import edip 'app' değişkenini çalıştırır.
