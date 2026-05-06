import os
import telebot
import yfinance as yf
import time
import datetime
import pytz
import pandas as pd
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
# Kendi Telegram ID'nizi buraya yazın (Sabah raporu için şart)
MY_CHAT_ID = "SİZİN_TELEGRAM_ID_NUMARANIZ" 
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

ALL_HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- TEKNİK ANALİZ VE AI YORUM FONKSİYONLARI (Aynı Kalacak) ---
def ai_yorumla(t):
    puan = 0
    notlar = []
    if t['fiyat'] > t['ema200']:
        puan += 2
        notlar.append("📈 Uzun vadeli trend pozitif.")
    else:
        puan -= 2
        notlar.append("📉 Uzun vadeli trend zayıf.")
    
    if t['rsi'] < 35:
        puan += 3
        notlar.append("🟢 Aşırı satım bölgesi (Tepki bekliyor).")
    elif t['rsi'] > 75:
        puan -= 3
        notlar.append("🔴 Aşırı alım bölgesi (Doygunluk).")
    
    if puan >= 4: sonuc = "🔥 GÜÇLÜ AL"
    elif 1 <= puan < 4: sonuc = "✅ OLUMLU"
    elif -1 <= puan < 1: sonuc = "🟡 NÖTR"
    else: sonuc = "⚠️ RİSKLİ"
    
    return sonuc, "\n".join(notlar)

def teknik_hesapla(df):
    try:
        if df.empty or len(df) < 20: return None
        close = df['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1] if len(df) >= 200 else close.mean()
        
        return {"rsi": rsi.iloc[-1], "ema200": ema200, "fiyat": close.iloc[-1]}
    except: return None

# --- YENİ: SABAH OTOMATİK RAPOR GÖREVİ ---
def sabah_raporu_gonder():
    """Hafta içi her sabah dün geceki verilerle analiz yapar."""
    simdi = datetime.datetime.now(TR_TIMEZONE)
    if simdi.weekday() >= 5: return # Hafta sonu çalışma

    bot.send_message(MY_CHAT_ID, "☀️ **Günaydın Ayhan Bey!**\nDünkü kapanış verileriyle hazırlanan piyasa raporu:")
    
    chunk_size = 30
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        try:
            data = yf.download([s + ".IS" for s in chunk], period="1y", interval="1d", progress=False)
            sinyaller = []
            for s in chunk:
                h_data = data.xs(s + ".IS", axis=1, level=1) if len(chunk) > 1 else data
                t = teknik_hesapla(h_data)
                if t:
                    karar, _ = ai_yorumla(t)
                    if "AL" in karar or "OLUMLU" in karar: # Sadece önemli olanları at
                        sinyaller.append(f"✅ {s}: {t['fiyat']:.2f} -> {karar}")
            
            if sinyaller:
                bot.send_message(MY_CHAT_ID, "\n".join(sinyaller))
            time.sleep(3)
        except: continue

# --- ZAMANLAYICIYI BAŞLAT ---
scheduler = BackgroundScheduler(timezone=TR_TIMEZONE)
# Her sabah 09:00'da rapor gönderir
scheduler.add_job(sabah_raporu_gonder, 'cron', day_of_week='mon-fri', hour=9, minute=0)
scheduler.start()

# --- WEBHOOK VE DİĞER KOMUTLAR (Mevcut haliyle kalacak) ---
@bot.message_handler(commands=['tara'])
def handle_tara(message):
    # Mevcut tara fonksiyonunuz
    pass

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
