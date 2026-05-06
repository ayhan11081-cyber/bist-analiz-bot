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

# 422 HİSSELİK LİSTE (Kendi tam listenizi buraya yapıştırın)
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
        # EMA200 için en az 200 satır veri lazım
        if df.empty or len(df) < 200: return None
        
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
        
        # 3. EMA Trend Kontrolü (200)
        ema200 = close.ewm(span=200, adjust=False).mean()
        
        # 4. Destek ve Direnç (Son 14 barın en düşük/yükseği)
        direnc = high.tail(14).max()
        destek = low.tail(14).min()
        
        # 5. Hacim Patlaması
        avg_vol = volume.tail(20).mean()
        hacim_patlamasi = volume.iloc[-1] > (avg_vol * 1.5)
        
        return {
            "rsi": rsi.iloc[-1],
            "mfi": mfi.iloc[-1],
            "ema200": ema200.iloc[-1],
            "fiyat": close.iloc[-1],
            "destek": destek,
            "direnc": direnc,
            "hacim_spike": hacim_patlamasi,
            "tarih": df.index[-1].strftime('%d/%m %H:%M')
        }
    except: return None

# --- YENİ: TEKİL HİSSE SORGULAMA ---
@bot.message_handler(func=lambda message: True)
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    
    # Komutları atla
    if hisse.startswith('/'): return

    msg = bot.send_message(message.chat.id, f"🔍 {hisse} inceleniyor...")
    
    try:
        durum = piyasa_kontrol()
        # EMA200 için 'period' 1 yıla çıkarıldı
        data = yf.download(f"{hisse}.IS", period="1y", interval="1d", progress=False)
        
        if data.empty:
            bot.edit_message_text(f"❌ {hisse} kodu bulunamadı.", msg.chat.id, msg.message_id)
            return

        t = teknik_hesapla(data)
        if t:
            trend = "⬆️ ÜSTÜNDE (POZİTİF)" if t['fiyat'] > t['ema200'] else "⬇️ ALTINDA (RİSKLİ)"
            rapor = (
                f"📊 **{hisse} ANALİZ SONUCU**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💰 Fiyat: {t['fiyat']:.2f} TL\n"
                f"📈 RSI: {t['rsi']:.0f} | MFI: {t['mfi']:.0f}\n"
                f"🛡️ Destek: {t['destek']:.2f}\n"
                f"🚀 Direnç: {t['direnc']:.2f}\n"
                f"📏 EMA200: {t['ema200']:.2f}\n"
                f"🛤️ Trend: {trend}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🕒 Veri: {t['tarih']}"
            )
            bot.edit_message_text(rapor, msg.chat.id, msg.message_id)
        else:
            bot.edit_message_text(f"❌ {hisse} için yeterli veri yok.", msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Bir hata oluştu.", msg.chat.id, msg.message_id)

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    durum = piyasa_kontrol()
    bot.send_message(message.chat.id, f"🔍 **Fırsat Taraması Başladı**\nDurum: {durum}")
    
    chunk_size = 30
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        try:
            # Tarama yaparken de 1y veri çekiyoruz ki EMA200 doğru çıksın
            data = yf.download([s + ".IS" for s in chunk], period="1y", interval="1d", progress=False, ignore_tz=True)
            
            grup_sonuc = []
            for s in chunk:
                try:
                    h_data = data.xs(s + ".IS", axis=1, level=1)
                    t = teknik_hesapla(h_data)
                    if not t: continue
                    
                    # Sadece Sinyal Olanlar (RSI < 35 Alım, RSI > 75 Satım, Hacim Patlaması)
                    if t['rsi'] < 35 or t['rsi'] > 75 or t['hacim_spike']:
                        d = "🟢" if t['rsi'] < 35 else "🔴" if t['rsi'] > 75 else "🔵"
                        trend = "⬆️" if t['fiyat'] > t['ema200'] else "⬇️"
                        h_ek = " 🔥" if t['hacim_spike'] else ""
                        grup_sonuc.append(f"{d}{trend} {s}: {t['fiyat']:.2f} (R:{t['rsi']:.0f} M:{t['mfi']:.0f}){h_ek}")
                except: continue
            
            if grup_sonuc:
                bot.send_message(message.chat.id, f"📦 **PAKET {int(i/30)+1} SİNYALLER**\n\n" + "\n".join(grup_sonuc))
            
            time.sleep(12) 
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
