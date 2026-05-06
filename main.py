import os
import telebot
import requests
import yfinance as yf
import time
import datetime
import pytz
import pandas as pd
from flask import Flask, request

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# 422 HİSSELİK LİSTE (Buraya listenizin tamamını koyun)
ALL_HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK"] 

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def piyasa_kontrol():
    simdi = datetime.datetime.now(TR_TIMEZONE)
    if simdi.weekday() >= 5: return "🌙 KAPALI (Hafta Sonu)"
    saat_dk = simdi.hour * 100 + simdi.minute
    if 955 <= saat_dk <= 1815: return "🚀 AÇIK (Canlı Seans)"
    return "🌙 KAPALI (Gece Hazırlığı)"

def teknik_hesapla(df):
    try:
        if df.empty or len(df) < 20: return None
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']

        # 1. RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        # 2. MFI (Para Akışı - Balina Takibi)
        tp = (high + low + close) / 3
        mf = tp * volume
        pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        mfi = 100 - (100 / (1 + (pos_mf / (neg_mf + 1e-9))))
        
        # 3. EMA Trend Kontrolü (20 ve 200)
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()
        
        # 4. Destek ve Direnç (Pivot Noktaları)
        son_kapanis = close.iloc[-1]
        direnc = high.tail(14).max()
        destek = low.tail(14).min()
        
        # 5. Hacim Patlaması
        avg_vol = volume.tail(20).mean()
        hacim_patlamasi = volume.iloc[-1] > (avg_vol * 1.5)
        
        return {
            "rsi": rsi.iloc[-1],
            "mfi": mfi.iloc[-1],
            "ema20": ema20.iloc[-1],
            "ema200": ema200.iloc[-1],
            "fiyat": son_kapanis,
            "destek": destek,
            "direnc": direnc,
            "hacim_spike": hacim_patlamasi,
            "tarih": df.index[-1].strftime('%d/%m %H:%M')
        }
    except: return None

def groq_analiz(veriler, durum):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
    Sen usta bir borsa stratejistisin. Piyasa {durum}.
    Şu teknik verileri yorumla:
    - Fiyat EMA200 üzerindeyse TREND YUKARI, altındaysa RİSKLİ de.
    - MFI ve RSI aynı anda 35 altındaysa 'BALİNA TOPLAMA BÖLGESİ' uyarısı yap.
    - Destek/Direnç mesafelerine göre hedef belirt.
    
    VERİLER:
    {veriler}
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        return r.json()['choices'][0]['message']['content']
    except: return "AI şu an analiz yapamıyor."

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    durum = piyasa_kontrol()
    bot.send_message(message.chat.id, f"🔍 **Gelişmiş Analiz Başlatıldı** (RSI+MFI+EMA+Pivot)\nDurum: {durum}")
    
    chunk_size = 30
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        try:
            aralik = "1h" if "AÇIK" in durum else "1d"
            data = yf.download([s + ".IS" for s in chunk], period="1mo", interval=aralik, progress=False, ignore_tz=True)
            
            grup_sonuc = []
            ai_icin = []
            
            for s in chunk:
                try:
                    h_data = data.xs(s + ".IS", axis=1, level=1)
                    t = teknik_hesapla(h_data)
                    if not t: continue
                    
                    # Trend Belirleme
                    trend_icon = "⬆️" if t['fiyat'] > t['ema200'] else "⬇️"
                    
                    # Sinyal Mantığı (RSI + MFI + Hacim)
                    if t['rsi'] < 35 and t['mfi'] < 35: d = "🟢"
                    elif t['rsi'] > 75: d = "🔴"
                    else: d = "🔵"
                    
                    if t['hacim_spike'] or t['rsi'] < 35 or t['rsi'] > 75 or t['mfi'] > 80:
                        h_ek = " 🔥 BALİNA GİRİŞİ" if t['hacim_spike'] else ""
                        satir = f"{d}{trend_icon} {s}: {t['fiyat']:.2f} TL | R:{t['rsi']:.0f} M:{t['mfi']:.0f}\n   ∟ Destek: {t['destek']:.2f} | Direnç: {t['direnc']:.2f}{h_ek}"
                        grup_sonuc.append(satir)
                        
                        if d in ["🟢", "🔴"] or t['hacim_spike']:
                            ai_icin.append(satir)
                except: continue
            
            if grup_sonuc:
                rapor = f"📦 **PAKET {int(i/30)+1}**\n\n" + "\n".join(grup_sonuc)
                bot.send_message(message.chat.id, rapor)
                
                if ai_icin:
                    time.sleep(2)
                    bot.send_message(message.chat.id, f"💡 **STRATEJİ:**\n{groq_analiz(chr(10).join(ai_icin), durum)}")
            
            time.sleep(10) # 429 Hata koruması
        except: continue

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return "OK", 200
    return "Forbidden", 403

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
