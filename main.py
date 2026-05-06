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

# 422 HİSSELİK TAM LİSTE (Kısaltıldı, buraya kendi listenizin tamamını koyun)
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
        # Teknik hesaplama için en az 30, EMA200 için 200 satır lazım
        if df.empty or len(df) < 30: return None
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']

        # 1. RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        # 2. MFI (Balina Takibi)
        tp = (high + low + close) / 3
        mf = tp * volume
        pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        mfi = 100 - (100 / (1 + (pos_mf / (neg_mf + 1e-9))))
        
        # 3. ADX (Trend Gücü)
        plus_dm = high.diff().where((high.diff() > low.diff().abs()) & (high.diff() > 0), 0)
        minus_dm = low.diff().abs().where((low.diff().abs() > high.diff()) & (low.diff().abs() > 0), 0)
        tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / (atr + 1e-9))
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / (atr + 1e-9))
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
        adx = dx.rolling(window=14).mean()

        # 4. Bollinger Bantları
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        ust_bant = sma20 + (std20 * 2)
        alt_bant = sma20 - (std20 * 2)

        # 5. Stochastic RSI
        stoch_rsi = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min() + 1e-9)
        stoch_k = stoch_rsi.rolling(3).mean() * 100

        # 6. EMA200
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1] if len(df) >= 200 else None
        
        # 7. Hacim ve Pivotlar
        direnc = high.tail(14).max()
        destek = low.tail(14).min()
        hacim_spike = volume.iloc[-1] > (volume.tail(20).mean() * 1.5)
        
        return {
            "rsi": rsi.iloc[-1], "mfi": mfi.iloc[-1], "adx": adx.iloc[-1],
            "stoch_k": stoch_k.iloc[-1], "ust_bant": ust_bant.iloc[-1],
            "alt_bant": alt_bant.iloc[-1], "ema200": ema200,
            "fiyat": close.iloc[-1], "destek": destek, "direnc": direnc,
            "hacim_spike": hacim_spike, "tarih": df.index[-1].strftime('%d/%m %H:%M')
        }
    except: return None

# --- TEKİL SORGU ---
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    msg = bot.send_message(message.chat.id, f"🔍 {hisse} derin analizi yapılıyor...")
    try:
        data = yf.download(f"{hisse}.IS", period="2y", interval="1d", progress=False)
        t = teknik_hesapla(data)
        if not t:
            bot.edit_message_text(f"❌ {hisse} verisi yetersiz.", msg.chat.id, msg.message_id)
            return

        trend = "⬆️ Pozitif" if t['ema200'] and t['fiyat'] > t['ema200'] else "⬇️ Negatif"
        rapor = (
            f"📊 **{hisse} TEKNİK ANALİZ**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 **Fiyat:** {t['fiyat']:.2f} TL\n"
            f"🛤️ **Trend:** {trend}\n"
            f"📈 **RSI:** {t['rsi']:.0f} | **MFI:** {t['mfi']:.0f}\n"
            f"⚡ **ADX:** {t['adx']:.0f} (Trend Gücü)\n"
            f"🔄 **Stoch:** %{t['stoch_k']:.0f}\n"
            f"📏 **Bollinger Alt:** {t['alt_bant']:.2f}\n"
            f"🚀 **Bollinger Üst:** {t['ust_bant']:.2f}\n"
            f"📉 **EMA200:** {t['ema200']:.2f if t['ema200'] else 'Hesaplanamadı'}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🕒 {t['tarih']}"
        )
        bot.edit_message_text(rapor, msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Hata oluştu.", msg.chat.id, msg.message_id)

# --- TÜM LİSTE TARAMA ---
@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    durum = piyasa_kontrol()
    bot.send_message(message.chat.id, f"🔍 **422 Hisse Taraması Başladı**\nDurum: {durum}")
    
    chunk_size = 30
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        bot.send_chat_action(message.chat.id, 'typing')
        try:
            data = yf.download([s + ".IS" for s in chunk], period="2y", interval="1d", progress=False)
            grup_sonuc = []
            for s in chunk:
                try:
                    h_data = data.xs(s + ".IS", axis=1, level=1) if len(chunk) > 1 else data
                    t = teknik_hesapla(h_data)
                    if not t: continue
                    
                    # Sinyal Simgeleri
                    d = "🟢" if t['rsi'] < 35 else "🔴" if t['rsi'] > 75 else "⚪"
                    trend = "⬆️" if t['ema200'] and t['fiyat'] > t['ema200'] else "⬇️"
                    h_ek = " 🔥" if t['hacim_spike'] else ""
                    
                    grup_sonuc.append(f"{d}{trend} {s}: {t['fiyat']:.2f} (R:{t['rsi']:.0f} A:{t['adx']:.0f}){h_ek}")
                except: continue
            
            if grup_sonuc:
                bot.send_message(message.chat.id, f"📦 **PAKET {int(i/30)+1}**\n\n" + "\n".join(grup_sonuc))
            time.sleep(4) 
        except: continue

    bot.send_message(message.chat.id, "✅ Tam liste taraması bitti.")

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
