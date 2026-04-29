import os
import telebot
import requests
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def ask_groq(user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    
    # Bota "Sen bir Borsa Analistisin" talimatı veriyoruz
    system_prompt = (
        "Sen deneyimli bir BIST analistisin. Kullanıcı sana hisse verisi sorduğunda; "
        "hacim artışı, RSI ve hareketli ortalamaları (MA) teknik olarak yorumla. "
        "Spekülatif yorumdan kaçın, veriye odaklan. Katılım endeksi kriterlerini hatırla."
    )
    
    data = {
        "model": "llama-3.1-8b-instant", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Analiz Hatası: {str(e)}"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Kullanıcıdan gelen mesajı "Analiz Et" komutuyla birleştiriyoruz
    answer = ask_groq(message.text)
    bot.reply_to(message, answer)

@app.route('/')
def home():
    return "ANALİZ BOTU YAYINDA"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
