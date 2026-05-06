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
MY_CHAT_ID = "SİZİN_TELEGRAM_ID_NUMARANIZ" # Buraya kendi ID'nizi yazmayı unutmayın
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# Listeniz (422 hisseye kadar uzatabilirsiniz)
ALL_HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def ai_beyin(t):
    """Sayıları alıp profesyonel bir borsa yorumuna dönüştüren AI Motoru"""
    skor = 0
    yorumlar = []
    
    # 1. Trend ve Güven Analizi
    if t['fiyat'] > t['ema200']:
        skor += 2
        yorumlar.append("✅ Fiyat uzun vadeli güven bölgesinde (EMA200 üstü).")
    else:
        skor -= 2
        yorumlar.append("⚠️ Dikkat: Uzun vadeli trend zayıf, baskı sürüyor.")

    # 2. Momentum ve Hacim (RSI & MFI)
    if t['rsi'] < 30:
        skor += 3
        yorumlar.append("🟢 RSI 'Aşırı Satım' diyor; buralar teknik dip olabilir.")
    elif t['rsi'] > 70:
        skor -= 3
        yorumlar.append("🔴 RSI 'Aşırı Alım' diyor; kar satışı her an gelebilir.")
    
    if t['mfi'] > 80:
        yorumlar.append("💰 Para girişi çok güçlü, ancak doygunluk sınırında.")
    elif t['mfi'] < 20:
        yorumlar.append("💸 Para çıkışı durma noktasında, mal toplama başlayabilir.")

    # 3. Hareketin Gücü (ADX)
    if t['adx'] > 25:
        yorumlar.append(f"⚡ Mevcut hareket çok güçlü (ADX: {t['adx']:.0f}).")
    else:
        yorumlar.append("💤 Piyasa kararsız, yatay bantta testere hareketi yapabilir.")

    # Final Karar Mekanizması
    if skor >= 5: karar = "🔥 GÜÇLÜ AL / FIRSAT"
    elif 1 <= skor < 5: karar = "✅ OLUMLU / İZLE"
    elif -2 <= skor < 1: karar = "🟡 NÖTR / BEKLE"
    else: karar = "⚠️ RİSKLİ / SATIŞ BASKISI"

    return karar, "\n".join(yorumlar)

def teknik_hesapla(df):
    try:
        if df is None or len(df) < 30: return None
        close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        # MFI
        tp = (high + low + close) / 3
        mf = tp * volume
        pos_mf = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
        neg_mf = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
        mfi = 100 - (100 / (1 + (pos_mf / (neg_mf + 1e-9))))

        # ADX
        tr = pd.concat([high-low, (high-close.shift(1)).abs(), (low-close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        adx = ((high.diff().abs() - low.diff().abs()).abs() / (atr + 1e-9)).rolling(14).mean() * 100
        
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        
        return {"rsi": rsi.iloc[-1], "mfi": mfi.iloc[-1], "adx": adx.iloc[-1], "ema200": ema200, "fiyat": close.iloc[-1]}
    except: return None

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    msg = bot.send_message(message.chat.id, f"🤖 **AI Analiz Birimi:** {hisse} inceleniyor...")
    try:
        # Stabilite için 2 yıllık veri
        data = yf.download(f"{hisse}.IS", period="2y", interval="1d", progress=False, timeout=15)
        t = teknik_hesapla(data)
        
        if t:
            karar, detay = ai_beyin(t)
            rapor = (
                f"🏛️ **HİSSE:** {hisse}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📢 **AI KARARI:** `{karar}`\n\n"
                f"📝 **STRATEJİ NOTLARI:**\n{detay}\n\n"
                f"🔢 **TEKNİK DEĞERLER:**\n"
                f"• Fiyat: {t['fiyat']:.2f} TL\n"
                f"• RSI: {t['rsi']:.0f} | MFI: {t['mfi']:.0f} | ADX: {t['adx']:.0f}\n"
                f"━━━━━━━━━━━━━━━"
            )
            bot.edit_message_text(rapor, msg.chat.id, msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"⚠️ {hisse} için veri yetersiz.", msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Sunucu hatası. Lütfen biraz bekleyip tekrar deneyin.", msg.chat.id, msg.message_id)

def sabah_taraması():
    """Hafta içi sabahları en sıcak 5 fırsatı belirler ve gönderir."""
    try:
        firsatlar = []
        # Render'ı yormamak için parça parça tarama
        for s in ALL_HISSES[:50]: # İlk etapta en popüler 50
            data = yf.download(f"{s}.IS", period="1y", interval="1d", progress=False, timeout=5)
            t = teknik_hesapla(data)
            if t and (t['rsi'] < 35 or t['rsi'] > 75):
                karar, _ = ai_beyin(t)
                firsatlar.append(f"🔹 {s}: {t['fiyat']:.2f} TL -> {karar}")
            time.sleep(1) # Yahoo engellemesin diye
        
        if firsatlar:
            bot.send_message(MY_CHAT_ID, "☀️ **GÜNAYDIN! Sabah Fırsat/Risk Raporu:**\n\n" + "\n".join(firsatlar))
    except: pass

scheduler = BackgroundScheduler(timezone=TR_TIMEZONE)
scheduler.add_job(sabah_taraması, 'cron', day_of_week='mon-fri', hour=9, minute=0)
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
