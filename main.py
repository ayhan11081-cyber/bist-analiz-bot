import os
import telebot
import yfinance as yf
import google.generativeai as genai
import threading
import time
from flask import Flask

# 1. AYARLAR
TOKEN = "8475111924:AAF6u6FsoVak73_YH3kA3LfQXLSuB6Zgy1w"
ID = "1568398578"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 2. GEMINI HAZIRLIK
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def home():
    return "Bot Yayında."

# 3. HİSSE LİSTESİ OKUMA
def get_hisseler():
    try:
        with open('hisseler.txt', 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["THYAO.IS", "ASELS.IS"]

# 4. ANALİZ MANTIĞI
def analiz_et(symbol):
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.fast_info['last_price']
        # Haber başlıklarını da alıp AI'a gönderiyoruz (Daha iyi analiz için)
        haberler = "\n".join([n['title'] for n in ticker.news[:3]])
        
        prompt = f"""
        Borsa hissesi {symbol} şu an {price} TL.
        Son 3 haber başlığı: {haberler}
        Bu verileri teknik ve temel analiz açısından yorumla. 
        Yatırımcıya yol gösterici, kısa ve net bir değerlendirme yap.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Analiz yapılamadı: {e}"

# 5. DÖNGÜ VE BOT
def stock_bot():
    bot.send_message(ID, "🚀 Bot Aktif ve İzlemede.")
    while True:
        hisseler = get_hisseler()
        for hisse in hisseler:
            mesaj = analiz_et(hisse)
            bot.send_message(ID, f"📊 {hisse} Analizi:\n\n{mesaj}")
            time.sleep(30) # Spam olmaması için bekleme
        time.sleep(21600) # 6 saat bekle

# Başlatma
if __name__ == "__main__":
    threading.Thread(target=stock_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
