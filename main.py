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
        r = requests.get(HİSSE_DOSYA_URL)
        if r.status_code == 200:
            lines = r.text.splitlines()
            # TAM LİSTE: Herhangi bir kısıtlama olmadan tüm hisseleri alıyoruz
            return [line.strip().upper() + ".IS" for line in lines if line.strip()]
    except Exception as e:
        return ["THYAO.IS", "ASELS.IS", "EREGL.IS"]

def borsa_taramasi():
    semboller = get_hisse_listesi()
    bulgular = []
    
    # 422 hisseyi hızlıca indiriyoruz
    # threads=True sayesinde tüm hisseler tek tek değil, gruplar halinde iner
    data_all = yf.download(semboller, period="2d", interval="1d", progress=False, threads=True)
    
    for s in semboller:
        try:
            # Her hissenin son fiyat ve değişimini kontrol et
            hisse_data = data_all['Close'][s]
            if hisse_data.isnull().values.any(): continue
            
            son_fiyat = float(hisse_data.iloc[-1])
            onceki_fiyat = float(hisse_data.iloc[-2])
            degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
            
            # SİNYAL KRİTERİ: %2 ve üzeri yükselenleri "radara girdi" sayalım
            if degisim > 2.0:
                bulgular.append(f"{s}: %{degisim:.2f} 📈")
        except:
            continue
            
    # Sadece en çok yükselen ilk 15 hisseyi Groq'a gönderelim (limit aşmamak için)
    return "\n".join(bulgular[:15]) if bulgular else "Bugün listede %2 üzeri hareket eden hisse bulunamadı."

def ask_groq(analiz_verisi):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    prompt = (
        "Sen Ayhan Bey'in stratejik borsa danışmanısın. Aşağıdaki hisse hareketlerini "
        "bir mühendis titizliğiyle yorumla. Hangi sektörde hareketlenme var, Ayhan Bey yarın "
        "sabah neye dikkat etmeli? Eğitim amaçlı bir teknik analiz tüyosu ile bitir."
    )
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Radara takılan hareketli hisseler:\n{analiz_verisi}"}
        ]
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        return r.json()['choices'][0]['message']['content']
    except:
        return "Bağlantı yoğunluğu nedeniyle analiz gecikti, lütfen bir dakika sonra tekrar deneyin."

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.reply_to(message, f"🚀 Optima Robot 422 hisseyi taramaya başladı... Lütfen bekleyin Ayhan Bey.")
    veriler = borsa_taramasi()
    analiz = ask_groq(veriler)
    bot.send_message(message.chat.id, f"🎯 **422 HİSSE TARAMA SONUCU & EĞİTİM**\n\n{analiz}")

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
