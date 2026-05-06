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
# Lütfen buraya kendi ID'nizi yazın (Örn: "12345678")
MY_CHAT_ID = "SİZİN_TELEGRAM_ID_NUMARANIZ" 
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# Tam 422 hisselik listenizi buraya yapıştırın
ALL_HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def detayli_ai_yorum(t):
    """Verileri borsa dilinde anlamlı bir yoruma dönüştürür."""
    puan = 0
    analiz_metni = []
    
    # 1. Trend Analizi (EMA200)
    if t['fiyat'] > t['ema200']:
        puan += 2
        analiz_metni.append("✅ Kağıt uzun vadeli ortalamasının (EMA200) üzerinde, ana yön yukarı.")
    else:
        puan -= 2
        analiz_metni.append("⚠️ Fiyat ana ortalamanın altında seyrediyor, baskı devam edebilir.")

    # 2. RSI Analizi
    if t['rsi'] < 30:
        puan += 4
        analiz_metni.append("🟢 RSI aşırı satım bölgesinde (DİP). Buradan güçlü bir tepki alımı beklenebilir.")
    elif t['rsi'] > 70:
        puan -= 4
        analiz_metni.append("🔴 RSI aşırı alım bölgesinde (TEPE). Kar satışları için dikkatli olunmalı.")
    else:
        analiz_metni.append(f"⚪ RSI {t['rsi']:.0f} ile nötr bölgede, yatay seyir hakim.")

    # 3. ADX (Trend Gücü)
    if t['adx'] > 25:
        analiz_metni.append(f"⚡ Trend oldukça güçlü (ADX: {t['adx']:.0f}). Hareketin devamı beklenebilir.")
    else:
        analiz_metni.append("💤 Trend gücü zayıf, hisse bir süre daha dinlenebilir.")

    # Sonuç Belirleme
    if puan >= 5: karar = "🔥 GÜÇLÜ AL"
    elif 1 <= puan < 5: karar = "✅ OLUMLU"
    elif -2 <= puan < 1: karar = "🟡 BEKLE / İZLE"
    else: karar = "⚠️ RİSKLİ / SAT"

    return karar, "\n".join(analiz_metni)

def teknik_hesapla(df):
    try:
        # En az 20 günlük veri varsa çalış, yoksa hata verme None döndür
        if df is None or len(df) < 20: return None
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        # ADX
        tr = pd.concat([high-low, (high-close.shift(1)).abs(), (low-close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        adx = ((high.diff().abs() - low.diff().abs()).abs() / (atr + 1e-9)).rolling(14).mean() * 100
        
        # EMA200
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1] if len(df) >= 200 else close.mean()
        
        return {"rsi": rsi.iloc[-1], "adx": adx.iloc[-1], "ema200": ema200, "fiyat": close.iloc[-1]}
    except: return None

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    msg = bot.send_message(message.chat.id, f"🔍 **{hisse}** Analiz Ediliyor...")
    try:
        # Render hatasını önlemek için '1y' yerine '2y' ve daha stabil veri çekimi
        data = yf.download(f"{hisse}.IS", period="2y", interval="1d", progress=False, timeout=20)
        t = teknik_hesapla(data)
        
        if t:
            karar, yorum = detayli_ai_yorum(t)
            rapor = (
                f"🏛️ **HİSSE:** {hisse}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📢 **KARAR:** `{karar}`\n\n"
                f"📝 **ANALİZ:**\n{yorum}\n\n"
                f"🔢 **VERİLER:**\n"
                f"• Fiyat: {t['fiyat']:.2f} TL\n"
                f"• RSI: {t['rsi']:.0f} | ADX: {t['adx']:.0f}\n"
                f"━━━━━━━━━━━━━━━"
            )
            bot.edit_message_text(rapor, msg.chat.id, msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"⚠️ {hisse} için veri çekilemedi. Kodun doğru olduğundan emin olun.", msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Sistem yoğunluğu nedeniyle hata oluştu, lütfen az sonra tekrar deneyin.", msg.chat.id, msg.message_id)

def otomatik_sabah_taraması():
    """Her sabah 09:00'da en iyi 10 fırsatı gönderir."""
    try:
        firsatlar = []
        # Render yorulmasın diye sadece ilk 100 hisseyi hızlıca tara
        for s in ALL_HISSES[:100]:
            data = yf.download(f"{s}.IS", period="1y", interval="1d", progress=False, timeout=10)
            t = teknik_hesapla(data)
            if t and t['rsi'] < 35:
                firsatlar.append(f"🟢 {s}: {t['fiyat']:.2f} (RSI: {t['rsi']:.0f})")
        
        if firsatlar:
            bot.send_message(MY_CHAT_ID, "☀️ **GÜNAYDIN! Sabah Fırsatları:**\n\n" + "\n".join(firsatlar))
    except: pass

# --- ZAMANLAYICI ---
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
