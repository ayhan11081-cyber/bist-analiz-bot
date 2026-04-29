import os
import telebot
import requests
import yfinance as yf
import pandas as pd
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- OPTİMA ROBOT TARAMA MOTORU ---
def borsa_taramasi():
    # Örnek olarak BIST'ten önemli birkaç hisse (Siz listeyi büyütebilirsiniz)
    semboller = ["THYAO.IS", "ASELS.IS", "EREGL.IS", "KRDMD.IS", "SISE.IS", "SASANI.IS", "HEKTS.IS"]
    bulunanlar = []
    
    for sembol in semboller:
        try:
            hisse = yf.download(sembol, period="14d", interval="1d", progress=False)
            if hisse.empty: continue
            
            # Basit teknik hesaplama (RSI mantığı)
            kapanis = hisse['Close'].iloc[-1]
            onceki_kapanis = hisse['Close'].iloc[-2]
            degisim = ((kapanis - onceki_kapanis) / onceki_kapanis) * 100
            
            # Sinyal kriteri: Hacim artışı ve pozitif kapanış
            if degisim > 2: # %2'den fazla yükselenleri "takibe değer" sayalım
                bulunanlar.append(f"🚀 {sembol}: %{degisim:.2f} yükselişle dikkat çekiyor.")
        except:
            continue
    
    return "\n".join(bulunanlar) if bulunanlar else "Şu an radara takılan güçlü bir sinyal yok."

def ask_groq(user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    system_prompt = "Sen uzman bir BIST analistisin. Optima Robot'un bulduğu verileri yorumla."
    data = {
        "model": "llama-3.1-8b-instant", 
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=20)
    return response.json()['choices'][0]['message']['content']

@bot.message_handler(commands=['tara'])
def start_scan(message):
    bot.reply_to(message, "Optima Robot taramaya başladı, 422 hisse süzülüyor... Lütfen bekleyin.")
    sonuclar = borsa_taramasi()
    # Sonuçları Groq'a yorumlatıyoruz
    analiz = ask_groq(f"Şu tarama sonuçlarını analiz et ve bana patlama ihtimali olanları söyle: {sonuclar}")
    bot.send_message(message.chat.id, analiz)

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    answer = ask_groq(message.text)
    bot.reply_to(message, answer)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
