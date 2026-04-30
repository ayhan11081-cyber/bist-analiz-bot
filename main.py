import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# GitHub Linkleri
URL_LIST = [
    "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/main/hisseler.txt",
    "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/main/Hisseler.txt"
]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def get_hisse_listesi():
    for url in URL_LIST:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return [line.strip().upper() + ".IS" for line in r.text.splitlines() if line.strip()]
        except: continue
    return []

def borsa_taramasi():
    semboller = get_hisse_listesi()
    if not semboller:
        return "HATA: GitHub dosyası henüz erişilebilir değil. Lütfen birkaç dakika bekleyin."

    try:
        # 422 Hisseyi hızlıca indir
        data = yf.download(semboller, period="2d", interval="1d", progress=False, threads=True)
        bulgular = []
        
        for s in semboller:
            try:
                c = data['Close'][s]
                if c.isnull().values.any(): continue
                degisim = ((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2]) * 100
                if degisim > 2.0: # %2 üzeri artış
                    bulgular.append(f"{s.replace('.IS','')}: %{degisim:.2f}")
            except: continue
        
        return "\n".join(bulgular[:15]) if bulgular else "Bugün kriterlere uyan hisse yok."
    except Exception as e:
        return f"Tarama Hatası: {str(e)}"

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.reply_to(message, "🔍 Optima Robot 422 hisseyi süzüyor... Ayhan Bey lütfen bekleyin.")
    veriler = borsa_taramasi()
    
    if "HATA" in veriler:
        bot.send_message(message.chat.id, veriler)
    else:
        # GÜNCEL MODEL: llama-3.3-70b-versatile
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        prompt = f"BIST uzmanı olarak bu verileri yorumla. Ayhan Bey için yarın patlama ihtimali olanları seç ve bir teknik tüyo ekle:\n{veriler}"
        
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "Sen Ayhan Bey'in özel borsa danışmanısın."},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            r = requests.post(url, headers=headers, json=data, timeout=30)
            analiz = r.json()['choices'][0]['message']['content']
            bot.send_message(message.chat.id, f"🎯 **ANALİZ VE EĞİTİM**\n\n{analiz}")
        except:
            bot.send_message(message.chat.id, f"Sinyal veren hisseler:\n{veriler}")

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
