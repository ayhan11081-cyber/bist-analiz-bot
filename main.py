import os
import telebot
import requests
import yfinance as yf
import time
import datetime
import pytz
from flask import Flask, request

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# 422 HİSSELİK LİSTE (Kısaltılmadan tam liste burada olmalı)
ALL_HISSES = [
    "THYAO","ASELS","EREGL","KCHOL","TUPRS","SISE","AKBNK","BIMAS","GARAN","SAHOL","ISCTR","YKBNK","ENKAI","EKGYO","PGSUS","FROTO","TOASO","ARCLK","PETKM","KRDMD","ASTOR","SASA","HEKTS","KONTR","SMRTG","EUPWR","ALARK","KOZAL","KOZAA","IPEKE","ODAS","ZOREN","CANTE","DOHOL","TKFEN",
    "MGROS","SOKM","AEFES","CCOLA","DOAS","TTKOM","TCELL","VESTL","VESBE","OTKAR","TMSN","KORDS","BRISA","GUBRF","BAGFS","EGEEN","BFREN","ASUZU","KARSN","CEMTS","PARSN","BUCIM","AKCNS","NUHCM","AFYON","OYAKC","KONYA","GOLTS","ASLAN","BOBET","QUAGR","BIENP","KAYSE","CWENE","ALFAS",
    "YEOTK","GESAN","SAYAS","HUNER","ENJSA","GWIND","AYDEM","AKSEN","AKFYE","BIOEN","TURSG","ANSGR","HALKB","VAKBN","TSKB","SKBNK","ALBRK","QNBFB","ICBCT","PAGYO","TRGYO","SNGYO","OZKGY","AKFGY","MSGYO","KLGYO","PSGYO","ASGYO","VKGYO","HLGYO","ZRGYO","IDGYO","PEGYO","NTHOL",
    "NETAS","KFEIN","ARDYZ","ESCOM","ARENA","INDES","DESPC","DGATE","PENTA","MIATK","REEDR","SDTTR","FORMT","KATMR","KMPUR","TARKM","HKTM","MHRGY","KUVVA","KOPOL","KCAER","GRSEL","GOKNR","MTRKS","LINK","LOGO","AZTEK","MOBTL","FONET","KRVGD","TATGD","SELGD","KNFRT","ULUFA",
    "ULUSE","ADESE","SELEC","RTALB","ANGEN","TRILC","GENIL","MEDTR","EBEBK","MAVI","VAKKO","YATAS","BRYAT","ALCAR","ALCTL","KAREL","KRONT","PKENT","AYGAZ","TRCAS","TURGG","BRKO","DIRIT","SNPAM","KUYAS","PRZMA","DERIM","DESA","HURGZ","IHLAS","IHEVA","IHLGM","IHGZT","IHYAY",
    "METRO","AVGYO","ATLAS","ETYAT","AVHOL","GLRYH","A1CAP","INFO","OSMEN","TERA","PLTER","SKYMD","EFORC","BYDNR","TABGD","HRKET","DCTTR","LILAK","KOTON","ALVES","ENTRA","MOGAN","ARTMS","ODINE","ICUGS","ALMAD","PRKME","IEYHO","ISYHO","USA K","NIBAS","EMKEL","GEREL",
    "GOODY","JANTS","GEDIK","INVEO","ECILC","ECZYT","DEVA","MPARK","LKMNH","TNZTP","AHLCI","ENERY","PASEU","TUKAS","VANGD","ELITE","SUNTK","ISSEN","TEZOL","ALKA","ALKIM","EGGUB","KUTPO","NGYO","AKMGY","EGSER","IZMDC","DITAS","FMIZP","MAKTK","YAYLA","ORCAY","PINSU","PNSUT",
    "PETUN","BANVT","MERKO","AVOD","KEREV","OBASE","PAPIL","PKART","BVSAN","IMASM","OZSUB","SMART","EDATA","ESEN","MAGEN","NATEN","CRDFA","LIDFA","VAKFN","PAMEL","BRKVY","ISGSY","GOZDE","VERUS","VERTU","GLBMD","TAVHL","RYSAS","RYGYO","DERHL","DAGHL","YESIL","YGYO","YYAPI","BJKAS","FENER","GSRAY","TSPOR","HUBVC"
]

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
        if df.empty or len(df) < 14: return 50, 50, False, 0, "-"
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        mf = tp * df['Volume']
        pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        mfi = 100 - (100 / (1 + (pos_mf / (neg_mf + 1e-9))))
        
        avg_vol = df['Volume'].tail(20).mean()
        cur_vol = df['Volume'].iloc[-1]
        hacim_patlamasi = cur_vol > (avg_vol * 1.5)
        
        return rsi.iloc[-1], mfi.iloc[-1], hacim_patlamasi, df['Close'].iloc[-1], df.index[-1].strftime('%d/%m %H:%M')
    except: return 50, 50, False, 0, "-"

def groq_analiz(veriler, durum):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": f"Piyasa {durum}. Ayhan Bey için şu kritik sinyalleri yorumla:\n{veriler}"}],
        "temperature": 0.1
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code == 200: return r.json()['choices'][0]['message']['content']
        return f"⚠️ AI Hatası: Kod {r.status_code} - (Limit Aşımı)"
    except: return "⚠️ Bağlantı Hatası."

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    durum = piyasa_kontrol()
    bot.send_message(message.chat.id, f"{durum}\n🚀 Kota koruma modu aktif. Tarama başlatıldı...")
    
    chunk_size = 30
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        try:
            aralik = "1h" if "AÇIK" in durum else "1d"
            data = yf.download([s + ".IS" for s in chunk], period="1mo", interval=aralik, progress=False, ignore_tz=True)
            
            grup_sonuc = []
            kritik_sinyaller = []
            
            for s in chunk:
                try:
                    h_data = data.xs(s + ".IS", axis=1, level=1)
                    rsi, mfi, spike, fiyat, tarih = teknik_hesapla(h_data)
                    
                    # Dinamik Durum Belirleme
                    if rsi < 35: d = "🟢"
                    elif rsi > 70: d = "🔴"
                    else: d = "🔵"
                    
                    if spike or mfi > 70 or rsi < 35 or rsi > 75:
                        ek = " 🔥 HACİM PATLAMASI" if spike else ""
                        satir = f"{d} {s}: {fiyat:.2f} TL | RSI {rsi:.0f}{ek}"
                        grup_sonuc.append(satir)
                        # Sadece AL/SAT ve Hacim Patlamalarını AI'ya gönder
                        if d in ["🟢", "🔴"] or spike:
                            kritik_sinyaller.append(satir)
                except: continue
            
            if grup_sonuc:
                rapor = f"📦 **PAKET {int(i/30)+1}**\n\n" + "\n".join(grup_sonuc)
                bot.send_message(message.chat.id, rapor)
                
                if kritik_sinyaller:
                    time.sleep(2) # AI öncesi küçük nefes
                    bot.send_message(message.chat.id, f"💡 **STRATEJİ:**\n{groq_analiz(chr(10).join(kritik_sinyaller), durum)}")
                else:
                    bot.send_message(message.chat.id, "💡 **STRATEJİ:** Bu grupta ekstrem bir durum yok, takibe devam.")
            
            # --- 429 KORUMASI: 10 saniye bekleme ---
            time.sleep(10)
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
