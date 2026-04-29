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
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": user_message}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        result = response.json()
        
        # CEVAP KONTROLÜ
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        elif 'error' in result:
            return f"Groq Hatası: {result['error']['message']}"
        else:
            return f"Beklenmedik Yanıt Formatı: {str(result)}"
            
    except Exception as e:
        return f"Bağlantı Hatası: {str(e)}"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Error", 403

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    answer = ask_groq(message.text)
    bot.reply_to(message, answer)

@app.route('/')
def home():
    return "SİSTEM İZLEMEDE"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
