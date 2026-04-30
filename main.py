import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# GitHub Linkleri - Sizin deponuz için optimize edildi
HİSSE_DOSYA_URL = "https://raw.githubusercontent.com/ayhan11081-cyber/bist-analiz-bot/main/hisseler.txt"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def get_hisse_listesi():
    try:
        r = requests.get(HİSSE_DOSYA_URL, timeout=15)
        if r.status_code == 200:
            lines = r.text.splitlines()
            # 422 hisseyi temizle ve sonuna .IS ekle
            return [line.strip().upper() + ".IS" for line in lines if len(line.strip()) > 0]
        else:
            return []
    except:
        return []

def borsa_taramasi():
    semboller = get_hisse_listesi()
    if not semboller:
        return "ERROR: GitHub dosyasına hala ulaşılamıyor. Lütfen deponun PUBLIC olduğundan emin olun."

    try:
        # HIZLI TARAMA: 422 hisseyi tek seferde indiriyoruz
        data = yf.download(semboller, period="2d", interval="1d", progress=False, threads=True)
        
        bulgular = []
        # MultiIndex veri yapısını kontrol ederek tara
        for s in semboller:
            try:
                # Verinin varlığını kontrol et
                if s not in data['Close']: continue
                hisse_c = data['Close'][s]
                if hisse_c.isnull().values.any(): continue
                
                degisim = ((hisse_c.iloc[-1] - hisse_c.iloc[-2]) / hisse_c.iloc[-2]) * 100
                
                # SİNYAL: %2 ve üzeri artanlar
                if degisim > 2.0:
                    bulgular.append(f"{s.replace('.IS','')}: %{degisim:.2f}")
            except:
                continue
        
        return "\n".join(bulgular[:15]) if bulgular else "Bugün listede %2 üzeri yükselen hisse bulunamadı."
    except Exception as e:
        return f"Tarama Hatası: Veriler işlenirken bir sorun oluştu."

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.reply_to(message, "🚀 Optima Robot 422 hisseyi süzüyor... Ayhan Bey, analiz birazdan hazır olacak.")
    veriler = borsa_taramasi()
    
    if "ERROR" in veriler:
        bot.send_message(message.chat.id, veriler)
    else:
        # Groq Analizi (Güncel Model)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        
        # Sizi yatırım konusunda eğitecek olan kısım burası
        prompt = (
            f"Aşağıdaki yükselen hisseleri bir uzman gibi yorumla: \n{veriler}\n\n"
            "Ayhan Bey'e yarın için stratejik bir tavsiye ver ve teknik bir borsa tüyosu ekle."
        )
        
        data = {
            "model": "llama-3.1-8b-instant", # En sağlam ve güncel model
            "messages": [
                {"role": "system", "content": "Sen Ayhan Bey'in özel borsa eğitmenisin. Analizlerin kısa, öz ve mühendis titizliğinde olsun."},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            r = requests.post(url, headers=headers, json=data, timeout=30)
            analiz = r.json()['choices'][0]['message']['content']
            bot.send_message(message.chat.id, f"📊 **OPTIMA ROBOT ANALİZİ**\n\n{analiz}")
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
