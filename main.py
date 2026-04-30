import os
import telebot
import requests
import yfinance as yf
import pandas as pd
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# Radara girecek en likit ve hareketli hisseler
HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK","ENKAI","EKGYO","PGSUS","FROTO","TOASO","ARCLK","PETKM","KRDMD","ASTOR","SASA","HEKTS","KONTR","SMRTG","EUPWR","ALARK","KOZAL","ODAS","TCELL","MIATK","REEDR","GUBRF"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def teknik_verileri_topla(df):
    try:
        # RSI (14 Günlük)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        
        # MFI (Para Akışı Endeksi)
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        mf = tp * df['Volume']
        pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        mfi = 100 - (100 / (1 + (pos_mf / neg_mf)))
        
        return rsi.iloc[-1], mfi.iloc[-1]
    except:
        return 50.0, 50.0

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    status_msg = bot.send_message(message.chat.id, "🎯 Ayhan Bey, teknik veriler ve para akışı süzülüyor...")
    
    try:
        # 1- Veri Çekme
        data = yf.download([s + ".IS" for s in HISSES], period="1mo", interval="1d", progress=False)
        
        teknik_rapor_metni = "📊 **TEKNİK RADAR (RSI | MFI | HACİM)**\n"
        ai_input_list = []

        for s in HISSES:
            try:
                h_data = data.xs(s + ".IS", axis=1, level=1)
                rsi, mfi = teknik_verileri_topla(h_data)
                vol_m = h_data['Volume'].iloc[-1] / 1_000_000
                degisim = ((h_data['Close'].iloc[-1] - h_data['Close'].iloc[-2]) / h_data['Close'].iloc[-2]) * 100
                
                # Sadece dikkat çekenleri listele
                if mfi > 60 or rsi > 60 or rsi < 35:
                    line = f"**{s}**: %{degisim:.1f} | RSI: {rsi:.0f} | MFI: {mfi:.0f} | {vol_m:.1f}M"
                    teknik_rapor_metni += line + "\n"
                    ai_input_list.append(line)
            except: continue

        # 2- Groq AI Analizi
        if ai_input_list:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
            prompt = (
                "Sen kıdemli bir borsa analistisin. Ayhan Bey için şu teknik listeyi yorumla. "
                "Para akışı (MFI) yüksek olanlara dikkat çek. Makro verilerle (faiz, enflasyon, haberler) "
                "harmanlayıp 'Al/Bekle' stratejisi oluştur. Çok teknik ve sonuç odaklı konuş."
            )
            payload = {
                "model": "llama-3.1-70b-versatile",
                "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": "\n".join(ai_input_list)}]
            }
            
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=25)
                res_json = r.json()
                # 'choices' hatasını önlemek için kontrol
                if 'choices' in res_json:
                    ai_analiz = res_json['choices'][0]['message']['content']
                    final_msg = f"{teknik_rapor_metni}\n\n💡 **STRATEJİ RAPORU:**\n{ai_analiz}"
                else:
                    final_msg = f"{teknik_rapor_metni}\n\n⚠️ AI şu an meşgul, teknik tablo yukarıdadır."
            except:
                final_msg = f"{teknik_rapor_metni}\n\n⚠️ AI bağlantı hatası."
        else:
            final_msg = "Şu an radara takılan kritik bir değişim yok Ayhan Bey."

        bot.edit_message_text(final_msg, message.chat.id, status_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(message.chat.id, f"Sistem hatası: {str(e)}")

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
