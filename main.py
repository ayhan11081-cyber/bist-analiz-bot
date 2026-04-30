import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
HİSSE_DOSYA_URL = "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/main/hisseler.txt"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def get_hisse_listesi():
    try:
        r = requests.get(HİSSE_DOSYA_URL, timeout=10)
        if r.status_code == 200:
            lines = r.text.splitlines()
            return [line.strip().upper() + ".IS" for line in lines if len(line.strip()) > 0]
    except:
        return []
    return []

def borsa_taramasi():
    semboller = get_hisse_listesi()
    if not semboller:
        return "HATA: GitHub'daki hisseler.txt okunamadı. Depoyu Public yaptığınızdan emin olun."

    try:
        data = yf.download(semboller, period="2d", interval="1d", progress=False, threads=True)
        bulgular = []
        for s in semboller:
            try:
                if s not in data['Close']: continue
                hisse_data = data['Close'][s]
                if hisse_data.isnull().values.any(): continue
                degisim = ((hisse_data.iloc[-1] - hisse_data.iloc[-2]) / hisse_data.iloc[-2]) * 100
                if degisim > 2.0:
                    bulgular.append(f"{s.replace('.IS','')}: %{degisim:.2f}")
            except: continue
        return "\n".join(bulgular[:15]) if bulgular else "Hareketli hisse bulunamadı."
    except Exception as e:
        return f"Tarama Hatası: {str(e)}"

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.reply_to(message, "🔍 Optima Robot 422 hisseyi süzüyor Ayhan Bey...")
    veriler = borsa_taramasi()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    prompt = f"Şu yükselen hisseleri teknik analist olarak yorumla ve Ayhan Bey'e bir tüyo ver:\n{veriler}"
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "system", "content": "Sen borsa uzmanısın."}, {"role": "user", "content": prompt}]
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        analiz = r.json()['choices'][0]['message']['content']
        bot.send_message(message.chat.id, f"🎯 **ANALİZ RAPORU**\n\n{analiz}")
    except:
        bot.send_message(message.chat.id, f"Hisseler:\n{veriler}")

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
