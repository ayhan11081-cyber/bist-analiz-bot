import os
import telebot
import yfinance as yf
import google.generativeai as genai
from flask import Flask, request

# Konfigürasyon
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") # Render'ın kendi verdiği URL
ID = "1568398578"

# Model Ayarı
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Webhook Ayarı
WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def home(): return "Bot Aktif"

# Teknik Analiz Fonksiyonları
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
        if df.empty: return "Veri alınamadı."
        g = hesapla_teknik_gostergeler(df)
        if g is None: return "İndikatör hesaplanamadı."
        
        prompt = f"Hisse: {sembol}, Fiyat: {g['Close']:.2f}, RSI: {g['RSI']:.2f}, MACD: {g['MACD']:.4f}. Teknik analiz yap."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Analiz hatası: {str(e)}"

@bot.message_handler(commands=['tarama'])
def tarama_komutu(message):
    try:
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            hisseler = [line.strip() + ".IS" for line in f if line.strip()]
        bot.reply_to(message, f"🚀 {len(hisseler)} hisse için analiz başlıyor...")
        for hisse in hisseler:
            analiz = analiz_et(hisse)
            bot.send_message(ID, f"📊 **{hisse.replace('.IS', '')}**\n{analiz}")
    except Exception as e: bot.reply_to(message, f"Hata: {e}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
