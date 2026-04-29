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
    """Kütüphane kullanmadan doğrudan Groq API'sine bağlanır"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": user_message}]
    }
    # Doğrudan istek atıyoruz, kütüphane çakışması riski sıfır
    response = requests.post(url, headers=headers, json=data, timeout=20)
    return response.json()['choices'][0]['message']['content']

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Mesajı Groq'a gönder
        answer = ask_groq(message.text)
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"Ayhan Bey, bir bağlantı hatası oldu ama çözmeye çalışıyorum: {str(e)}")

@app.route('/')
def home():
    return "SİSTEM YALIN MODDA AKTİF"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
