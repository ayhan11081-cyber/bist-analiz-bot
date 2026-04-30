import os
import telebot
import yfinance as yf
import pandas as pd
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# Seans başında en kritik 40-50 hisse (Hız için daralttık, her şeyi göreceksiniz)
HISSES = ["THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK","ENKAI","EKGYO","PGSUS","FROTO","TOASO","ARCLK","PETKM","KRDMD","ASTOR","SASA","HEKTS","KONTR","SMRTG","EUPWR","ALARK","KOZAL","ODAS","TCELL","VESTL","MIATK","REEDR","GUBRF"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def teknik_hesapla(df):
    # RSI Hesaplama (14 Günlük)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1+rs))
    
    # MFI Hesaplama (Tipik Fiyat üzerinden)
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
    neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
    mfr = pos_mf / neg_mf
    mfi = 100 - (100 / (1+mfr))
    
    return rsi.iloc[-1], mfi.iloc[-1]

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    status_msg = bot.reply_to(message, "🚀 Seans öncesi RSI, MFI ve Hacim verileri çekiliyor...")
    
    rapor = "📊 **SEANS ÖNCESİ KRİTİK RAPOR**\n\n"
    rapor += "HİSSE | RSI | MFI | HACİM (M)\n"
    rapor += "------------------------------\n"
    
    try:
        # Hız için son 30 günlük veri yeterli
        data = yf.download([s + ".IS" for s in HISSES], period="1mo", interval="1d", progress=False)
        
        found_count = 0
        for s in HISSES:
            try:
                ticker_data = data.xs(s + ".IS", axis=1, level=1)
                rsi_val, mfi_val = teknik_hesapla(ticker_data)
                vol_m = ticker_data['Volume'].iloc[-1] / 1_000_000
                
                # Sadece aşırı alım/satım veya yüksek hacimli olanları raporla (Hızlı filtre)
                if rsi_val > 65 or rsi_val < 35 or mfi_val > 70:
                    rapor += f"**{s}** | {rsi_val:.1f} | {mfi_val:.1f} | {vol_m:.1f}M\n"
                    found_count += 1
            except: continue
        
        if found_count == 0:
            rapor += "Sıradışı bir teknik veri bulunamadı."
            
        bot.edit_message_text(rapor, message.chat.id, status_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"Hata: {str(e)}", message.chat.id, status_msg.message_id)

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
