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
            # Gereksiz boşlukları ve karakterleri temizle
            return [line.strip().upper() + ".IS" for line in lines if len(line.strip()) > 0]
        return []
    except:
        return []

def borsa_taramasi():
    semboller = get_hisse_listesi()
    if not semboller:
        return "HATA: GitHub'daki hisse listesi okunamadı veya dosya boş."

    try:
        # 422 hisseyi daha küçük bir veri paketiyle (period=2d) hızlıca çekiyoruz
        # group_by='ticker' ekleyerek veriyi daha düzenli alıyoruz
        data = yf.download(semboller, period="2d", interval="1d", progress=False, threads=True, group_by='ticker')
        
        bulgular = []
        for s in semboller:
            try:
                # Verinin gelip gelmediğini kontrol et
                hisse_data = data[s]
                if hisse_data.empty: continue
                
                kapanis = hisse_data['Close'].iloc[-1]
                onceki = hisse_data['Close'].iloc[-2]
                degisim = ((kapanis - onceki) / onceki) * 100
                
                # Kriter: %2'den fazla artanları yakala
                if degisim > 2.0:
                    bulgular.append(f"{s.replace('.IS','')}: %{degisim:.2f}")
            except:
                continue
        
        return "\n".join(bulgular) if bulgular else "Tarama tamamlandı ama %2 üzeri yükselen hisse bulunamadı."
    except Exception as e:
        return f"Tarama sırasında hata oluştu: {str(e)}"

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    sent_msg = bot.reply_to(message, "⚙️ Optima Robot 422 hisseyi süzüyor, bu işlem 15-20 saniye sürebilir...")
    
    veriler = borsa_taramasi()
    
    # Veriler geldiyse Groq'a gönderip analiz ettiriyoruz
    if "HATA" in veriler or "bulunamadı" in veriler:
        bot.edit_message_text(veriler, message.chat.id, sent_msg.message_id)
    else:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        prompt = f"Şu yükselen hisse listesini teknik analist olarak yorumla ve Ayhan Bey'e yarın için tüyo ver:\n{veriler}"
        
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "system", "content": "Sen bir BIST uzmanısın."}, {"role": "user", "content": prompt}]
        }
        
        try:
            r = requests.post(url, headers=headers, json=data, timeout=20)
            analiz = r.json()['choices'][0]['message']['content']
            bot.send_message(message.chat.id, f"🎯 **ANALİZ RAPORU**\n\n{analiz}")
        except:
            bot.send_message(message.chat.id, f"Veriler çekildi ama analiz motoru (Groq) meşgul. Ham veriler:\n{veriler}")

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
