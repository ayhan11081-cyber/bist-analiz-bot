import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# İKİ İHTİMALİ DE TANIMLIYORUZ
URL_KUCUK = "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/main/hisseler.txt"
URL_BUYUK = "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/main/Hisseler.txt"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def get_hisse_listesi():
    # Önce küçük harfli dosyayı dene
    for url in [URL_KUCUK, URL_BUYUK]:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                lines = r.text.splitlines()
                return [line.strip().upper() + ".IS" for line in lines if len(line.strip()) > 0]
        except:
            continue
    return []

def borsa_taramasi():
    semboller = get_hisse_listesi()
    if not semboller:
        return "HATA: GitHub'da 'hisseler.txt' dosyası bulunamadı. Lütfen dosya adını kontrol edin."

    try:
        # HIZLI TARAMA
        data = yf.download(semboller, period="2d", interval="1d", progress=False, threads=True)
        
        bulgular = []
        for s in semboller:
            try:
                # Veriyi güvenli bir şekilde çek
                if s not in data['Close']: continue
                c = data['Close'][s]
                if c.isnull().values.any(): continue
                
                degisim = ((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2]) * 100
                
                # SİNYAL: %2 ve üzeri yükselenler
                if degisim > 2.0:
                    bulgular.append(f"{s.replace('.IS','')}: %{degisim:.2f}")
            except:
                continue
        
        return "\n".join(bulgular[:20]) if bulgular else "Tarama bitti ama kriterlere uyan hisse yok."
    except Exception as e:
        return f"Tarama Hatası: {str(e)}"

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.reply_to(message, "🔍 Optima Robot 422 hisseyi süzüyor... Lütfen bekleyin Ayhan Bey.")
    veriler = borsa_taramasi()
    
    if "HATA" in veriler:
        bot.send_message(message.chat.id, veriler)
    else:
        # Groq Analizi
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        prompt = f"Aşağıdaki hisseleri analiz et. Hangileri yarın için patlamaya hazır? Teknik anlat ve bir tüyo ekle:\n{veriler}"
        
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Sen Ayhan Bey'in borsa eğitmenisin."},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            r = requests.post(url, headers=headers, json=data, timeout=30)
            analiz = r.json()['choices'][0]['message']['content']
            bot.send_message(message.chat.id, f"🎯 **GÜNLÜK ANALİZ**\n\n{analiz}")
        except:
            bot.send_message(message.chat.id, f"Sinyaller:\n{veriler}")

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
