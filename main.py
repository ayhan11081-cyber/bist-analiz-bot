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

# Radara girecek ana hisse havuzu (Tam performans için optimize edildi)
HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK","ENKAI","EKGYO","PGSUS","FROTO","TOASO","ARCLK","PETKM","KRDMD","ASTOR","SASA","HEKTS","KONTR","SMRTG","EUPWR","ALARK","KOZAL","ODAS","TCELL","MIATK","REEDR","GUBRF"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def analiz_motoru(df):
    # RSI (Güç Endeksi)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    
    # MFI (Para Akışı Endeksi) - Para girişi burada belli olur
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
    neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
    mfi = 100 - (100 / (1 + (pos_mf / neg_mf)))
    
    return rsi.iloc[-1], mfi.iloc[-1]

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "🎯 Ayhan Bey, sistem teknik verileri topluyor ve Groq AI ile makro analize geçiyor...")
    
    teknik_ozet = []
    try:
        data = yf.download([s + ".IS" for s in HISSES], period="1mo", interval="1d", progress=False)
        
        for s in HISSES:
            try:
                h_data = data.xs(s + ".IS", axis=1, level=1)
                rsi, mfi = analiz_motoru(h_data)
                degisim = ((h_data['Close'].iloc[-1] - h_data['Close'].iloc[-2]) / h_data['Close'].iloc[-2]) * 100
                
                # Sadece teknik olarak "önemli" olanları AI'ya gönder (Para akışı veya momentum olanlar)
                if mfi > 60 or rsi > 60 or rsi < 35:
                    teknik_ozet.append(f"{s}: Değişim %{degisim:.2f}, RSI: {rsi:.1f}, MFI: {mfi:.1f}")
            except: continue

        # --- GROQ AI DEVREYE GİRİYOR ---
        if not teknik_ozet:
            bot.send_message(message.chat.id, "Şu an teknik radara takılan bir hisse yok.")
            return

        prompt = (
            f"Sen Ayhan Bey'in uzman borsa danışmanısın. Aşağıdaki teknik verileri (RSI, MFI, Değişim) al. "
            f"Buna Türkiye'deki makroekonomik durumu, faiz beklentilerini ve güncel piyasa haberlerini ekleyerek yorumla. "
            f"Para girişi olan (yüksek MFI) hisseleri vurgula. Hangi hisseler kazandırabilir? "
            f"Hangi durumlarda 'bekle' demeliyiz? Net, mühendisçe ve kar odaklı bir rapor sun."
        )
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-70b-versatile", # Daha akıllı model
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Teknik Veri Listesi:\n" + "\n".join(teknik_ozet)}
            ],
            "temperature": 0.5
        }

        r = requests.post(url, headers=headers, json=payload, timeout=40)
        ai_cevap = r.json()['choices'][0]['message']['content']
        bot.send_message(message.chat.id, f"📈 **STRATEJİK PİYASA RAPORU**\n\n{ai_cevap}")

    except Exception as e:
        bot.send_message(message.chat.id, f"Sistemde bir aksama oldu Ayhan Bey: {str(e)}")

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
