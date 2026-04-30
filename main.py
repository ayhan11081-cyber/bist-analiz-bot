import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# GitHub Linkleri - Tüm ihtimalleri deniyoruz
URL_LISTESI = [
    "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/main/hisseler.txt",
    "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/main/Hisseler.txt",
    "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/master/hisseler.txt"
]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def get_hisse_listesi():
    son_hata = ""
    for url in URL_LISTESI:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                # Dosya bulundu!
                lines = r.text.splitlines()
                return [line.strip().upper() + ".IS" for line in lines if len(line.strip()) > 0]
            else:
                son_hata = f"Hata Kodu: {r.status_code} (Link: {url.split('/')[-2]}/{url.split('/')[-1]})"
        except Exception as e:
            son_hata = f"Bağlantı Hatası: {str(e)}"
            continue
    return [f"ERROR: {son_hata}"]

def borsa_taramasi():
    semboller = get_hisse_listesi()
    
    # Eğer listede hata mesajı döndüyse onu kullanıcıya ilet
    if semboller and "ERROR:" in semboller[0]:
        return semboller[0]

    try:
        # HIZLI TARAMA - Multi-threading açık
        data = yf.download(semboller, period="2d", interval="1d", progress=False, threads=True)
        
        bulgular = []
        for s in semboller:
            try:
                # pandas MultiIndex kontrolü
                hisse_kapanis = data['Close'][s]
                if hisse_kapanis.isnull().values.any(): continue
                
                degisim = ((hisse_kapanis.iloc[-1] - hisse_kapanis.iloc[-2]) / hisse_kapanis.iloc[-2]) * 100
                
                if degisim > 2.0: # %2 ve üzeri artanlar
                    bulgular.append(f"{s.replace('.IS','')}: %{degisim:.2f}")
            except:
                continue
        
        return "\n".join(bulgular[:15]) if bulgular else "Bugün listede %2 üzeri yükselen hisse bulunamadı."
    except Exception as e:
        return f"Tarama Hatası: {str(e)}"

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.reply_to(message, "🔍 Optima Robot 422 hisseyi süzüyor... Bu işlem 20-30 saniye sürebilir.")
    veriler = borsa_taramasi()
    
    if "ERROR:" in veriler:
        # Detaylı hatayı göster
        bot.send_message(message.chat.id, f"❌ {veriler}\n\nLütfen GitHub'daki dosya adının 'hisseler.txt' olduğundan ve deponun 'Public' olduğundan emin olun.")
    else:
        # Groq Analiz Kısmı
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        prompt = f"Şu hisseleri bir borsa eğitmeni gibi analiz et ve yarın için Ayhan Bey'e bir tüyo ver:\n{veriler}"
        
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "Sen Ayhan Bey'in uzman borsa danışmanısın."},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            r = requests.post(url, headers=headers, json=data, timeout=30)
            analiz = r.json()['choices'][0]['message']['content']
            bot.send_message(message.chat.id, f"🎯 **GÜNLÜK ANALİZ**\n\n{analiz}")
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
