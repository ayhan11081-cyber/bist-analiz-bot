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
MY_CHAT_ID = "SİZİN_TELEGRAM_ID_NUMARANIZ" # Buraya kendi ID'nizi tırnak içinde yazın
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# 422 hissenin tamamını buraya ekleyebilirsiniz
ALL_HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def detayli_ai_yorum(t):
    puan = 0
    analiz_metni = []
    
    if t['fiyat'] > t['ema200']:
        puan += 2
        analiz_metni.append("✅ Uzun vadeli trend (EMA200) üzerinde, yön yukarı.")
    else:
        puan -= 2
        analiz_metni.append("⚠️ EMA200 altında baskı sürüyor.")

    if t['rsi'] < 30:
        puan += 4
        analiz_metni.append("🟢 RSI aşırı satımda (DİP). Tepki gelebilir.")
    elif t['rsi'] > 70:
        puan -= 4
        analiz_metni.append("🔴 RSI aşırı alımda (TEPE). Riskli bölge.")
    else:
        analiz_metni.append(f"⚪ RSI {t['rsi']:.0f} ile nötr.")

    if t['adx'] > 25:
        analiz_metni.append(f"⚡ Trend gücü yüksek (ADX: {t['adx']:.0f}).")
    
    if puan >= 5: karar = "🔥 GÜÇLÜ AL"
    elif 1 <= puan < 5: karar = "✅ OLUMLU"
    elif -2 <= puan < 1: karar = "🟡 NÖTR"
    else: karar = "⚠️ RİSKLİ / SAT"

    return karar, "\n".join(analiz_metni)

def teknik_hesapla(df):
    try:
        if df is None or len(df) < 30: return None
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        # ADX 14
        tr = pd.concat([high-low, (high-close.shift(1)).abs(), (low-close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        adx = ((high.diff().abs() - low.diff().abs()).abs() / (atr + 1e-9)).rolling(14).mean() * 100
        
        # EMA 200
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        
        return {"rsi": rsi.iloc[-1], "adx": adx.iloc[-1], "ema200": ema200, "fiyat": close.iloc[-1]}
    except: return None

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    ticker = f"{hisse}.IS"
    msg = bot.send_message(message.chat.id, f"🔍 **{hisse}** Analiz Ediliyor...")
    
    try:
        # Tekli sorguda Render'ı yormamak için veri periyodunu 1y yapıyoruz
        data = yf.download(ticker, period="1y", interval="1d", progress=False, timeout=10)
        t = teknik_hesapla(data)
        
        if t:
            karar, yorum = detayli_ai_yorum(t)
            bot.edit_message_text(
                f"🏛️ **HİSSE:** {hisse}\n━━━━━━━━━━━━━━━\n"
                f"📢 **KARAR:** `{karar}`\n\n📝 **ANALİZ:**\n{yorum}\n\n"
                f"🔢 **Fiyat:** {t['fiyat']:.2f} TL\n━━━━━━━━━━━━━━━", 
                msg.chat.id, msg.message_id, parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(f"⚠️ {hisse} verisi eksik veya hatalı.", msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Veri çekme hatası. Lütfen tekrar deneyin.", msg.chat.id, msg.message_id)

def otomatik_sabah_taraması():
    """Hisseleri 10'arlı gruplarla güvenli şekilde tarar."""
    try:
        bot.send_message(MY_CHAT_ID, "☀️ **Günaydın! Sabah piyasa taraması başlıyor...**")
        chunk_size = 10
        for i in range(0, len(ALL_HISSES), chunk_size):
            chunk = ALL_HISSES[i:i + chunk_size]
            sinyaller = []
            for s in chunk:
                try:
                    data = yf.download(f"{s}.IS", period="6mo", interval="1d", progress=False, timeout=5)
                    t = teknik_hesapla(data)
                    if t and t['rsi'] < 35: # Sadece fırsat verenleri raporla
                        sinyaller.append(f"🟢 {s}: {t['fiyat']:.2f} (RSI: {t['rsi']:.0f})")
                except: continue
            
            if sinyaller:
                bot.send_message(MY_CHAT_ID, "\n".join(sinyaller))
            time.sleep(2) # Render'ı dinlendir
    except: pass

scheduler = BackgroundScheduler(timezone=TR_TIMEZONE)
scheduler.add_job(otomatik_sabah_taraması, 'cron', day_of_week='mon-fri', hour=9, minute=0)
scheduler.start()

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
