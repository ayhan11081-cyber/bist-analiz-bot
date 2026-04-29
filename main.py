import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def borsa_taramasi():
    # İlk aşamada motoru yormamak için lokomotif hisseler
    hisseler = ["THYAO.IS", "ASELS.IS", "EREGL.IS", "KRDMD.IS", "SISE.IS", "BIMAS.IS", "AKBNK.IS"]
    rapor = ""
    
    for s in hisseler:
        try:
            # Son 5 günlük veriyi çek
            data = yf.download(s, period="5d", interval="1d", progress=False)
            if data.empty: continue
            
            son_fiyat = data['Close'].iloc[-1]
            degisim = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
            
            # Sadece pozitif olanları rapora ekle
            if degisim > 0:
                rapor += f"{s}: Fiyat {son_fiyat:.2f}, Günlük Değişim %{degisim:.2f}\n"
        except:
            continue
    return rapor if rapor else "Şu an pozitif bir sinyal yakalanamadı."

def ask_groq(rapor_verisi):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    # Bota kesin talimat: "Kullanıcıya soru sorma, veriyi yorumla!"
    prompt = f"Aşağıdaki borsa verilerini teknik bir analist gözüyle yorumla. Patlama potansiyeli olanları seç: \n{rapor_verisi}"
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Sen bir BIST analiz robotusun. Veri aldığında analiz yaparsın, soru sormazsın."},
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=20)
    return response.json()['choices'][0]['message']['content']

@bot.message_handler(commands=['tara'])
def handle_tara(message):
    bot.reply_to(message, "Optima Robot çalışıyor, BIST verileri çekiliyor... Lütfen bekleyin Ayhan Bey.")
    veriler = borsa_taramasi()
    analiz = ask_groq(veriler)
    bot.send_message(message.chat.id, analiz)

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    # Normal mesaj yazarsanız sadece sohbet eder
    bot.reply_to(message, "Ayhan Bey, analiz yapmamı isterseniz lütfen /tara komutunu kullanın.")

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
