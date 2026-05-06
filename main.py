import os
import telebot
import yfinance as yf
import time
import datetime
import pytz
import pandas as pd
from flask import Flask, request

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# Listenizdeki hisse sayısını 422'ye kadar buraya ekleyebilirsiniz.
ALL_HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def ai_yorumla(t):
    """İndikatör verilerini mantıksal bir analize dönüştürür."""
    puan = 0
    notlar = []

    # Trend Analizi
    if t['fiyat'] > t['ema200']:
        puan += 2
        notlar.append("📈 Uzun vadeli trend pozitif (EMA200 üstü).")
    else:
        puan -= 2
        notlar.append("📉 Uzun vadeli trend zayıf (EMA200 altı).")

    # RSI & Stoch Analizi
    if t['rsi'] < 35:
        puan += 3
        notlar.append("🟢 RSI aşırı satım bölgesinde, tepki alımı gelebilir.")
    elif t['rsi'] > 75:
        puan -= 3
        notlar.append("🔴 RSI aşırı alım bölgesinde, kar satışı riski var.")

    # ADX (Trend Gücü)
    if t['adx'] > 25:
        notlar.append(f"⚡ Güçlü bir trend hakim (ADX: {t['adx']:.0f}).")
    else:
        notlar.append("💤 Yatay piyasa/kararsız seyir hakim.")

    # Karar Belirleme
    if puan >= 4: sonuc = "🔥 GÜÇLÜ AL SİNYALİ"
    elif 1 <= puan < 4: sonuc = "✅ OLUMLU / İZLE"
    elif -1 <= puan < 1: sonuc = "🟡 NÖTR / BEKLE"
    else: sonuc = "⚠️ RİSKLİ / DİKKAT"

    return sonuc, "\n".join(notlar)

def teknik_hesapla(df):
    try:
        # Hata önleme: Veri derinliği kontrolü
        if df.empty or len(df) < 30: return None
        
        close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        # MFI
        tp = (high + low + close) / 3
        mf = tp * volume
        pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        mfi = 100 - (100 / (1 + (pos_mf / (neg_mf + 1e-9))))
        
        # ADX
        plus_dm = high.diff().where((high.diff() > low.diff().abs()) & (high.diff() > 0), 0)
        minus_dm = low.diff().abs().where((low.diff().abs() > high.diff()) & (low.diff().abs() > 0), 0)
        tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / (atr + 1e-9))
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / (atr + 1e-9))
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
        adx = dx.rolling(window=14).mean()

        # EMA200
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1] if len(df) >= 200 else close.mean()
        
        return {
            "rsi": rsi.iloc[-1], "mfi": mfi.iloc[-1], "adx": adx.iloc[-1],
            "ema200": ema200, "fiyat": close.iloc[-1], 
            "tarih": df.index[-1].strftime('%d/%m %H:%M')
        }
    except: return None

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    msg = bot.send_message(message.chat.id, f"🤖 **{hisse}** için yapay zeka analizi hazırlanıyor...")
    try:
        data = yf.download(f"{hisse}.IS", period="1y", interval="1d", progress=False)
        t = teknik_hesapla(data)
        if not t:
            bot.edit_message_text(f"⚠️ {hisse} için yeterli teknik veri yok.", msg.chat.id, msg.message_id)
            return

        karar, detay = ai_yorumla(t)
        
        rapor = (
            f"🏛️ **HİSSE:** {hisse}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📢 **YAPAY ZEKA KARARI:**\n**{karar}**\n\n"
            f"📝 **ANALİZ NOTLARI:**\n{detay}\n\n"
            f"🔢 **TEKNİK VERİLER:**\n"
            f"• Fiyat: {t['fiyat']:.2f} TL\n"
            f"• RSI: {t['rsi']:.0f} | MFI: {t['mfi']:.0f}\n"
            f"• Trend Gücü (ADX): {t['adx']:.0f}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🕒 {t['tarih']}"
        )
        bot.edit_message_text(rapor, msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Bir hata oluştu, lütfen kodu kontrol edin.", msg.chat.id, msg.message_id)

@bot.message_handler(commands=['tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "🔎 **Piyasa taranıyor, sadece sinyal verenler listelenecek...**")
    chunk_size = 30
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        try:
            data = yf.download([s + ".IS" for s in chunk], period="1y", interval="1d", progress=False)
            sinyaller = []
            for s in chunk:
                try:
                    h_data = data.xs(s + ".IS", axis=1, level=1) if len(chunk) > 1 else data
                    t = teknik_hesapla(h_data)
                    if t and (t['rsi'] < 35 or t['rsi'] > 75):
                        karar, _ = ai_yorumla(t)
                        sinyaller.append(f"🔹 **{s}**: {t['fiyat']:.2f} -> {karar}")
                except: continue
            if sinyaller:
                bot.send_message(message.chat.id, "\n".join(sinyaller))
            time.sleep(3)
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
