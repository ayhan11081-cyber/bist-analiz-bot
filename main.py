import os
import telebot
import yfinance as yf
import time
import datetime
import pytz
import pandas as pd
import numpy as np
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
MY_CHAT_ID = "SİZİN_TELEGRAM_ID_NUMARANIZ" # Buraya kendi ID'nizi yazmayı unutmayın
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# --- 422 HİSSELİK KATILIM ODAKLI TAM LİSTE ---
KATILIM_HISSES = [
    "A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSUE", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGGEN", "ANHYT", "ANSGR", "ARCLK", "ARDYZ", "ARENA", "ARSGR", "ARZUM", "ASCEY", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATATP", "ATEKS", "ATLAS", "AVGYO", "AVHOL", "AVOD", "AVTUR", "AYCES", "AYDEM", "AYEN", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BANVT", "BARMA", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIZIM", "BJKAS", "BLCYT", "BMTKS", "BNTAS", "BOBET", "BORLS", "BRISA", "BRLSM", "BRMEN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "CANTE", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEOAS", "CIMSA", "CLEBI", "CONSE", "COSMO", "CRDFA", "CUSAN", "CVMEK", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DATGATE", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA", "DGATE", "DGGYO", "DIRIT", "DMSAS", "DOAS", "DOBUR", "DOGUB", "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKOS", "ELITE", "EMKEL", "ENERY", "ENJSA", "ENKAI", "ENSRI", "EPLAS", "ERBOS", "EREGL", "ERSU", "ESCAR", "ESCOM", "ESEN", "ETILR", "EUHOL", "EUPWR", "EUREN", "EUROB", "EUYO", "EYGYO", "FADE", "FENER", "FLAP", "FONET", "FORMT", "FRIGO", "FROTO", "FZPLP", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLRYH", "GLYHO", "GMTAS", "GOODY", "GOZDE", "GRNYO", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATAS", "HEKTS", "HKTM", "HOROZ", "HRKET", "HUBVC", "HUNER", "ICBCT", "IDEAS", "IDGYO", "IEYHO", "IHEVA", "IHLAS", "IHLGM", "IHGZT", "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INVES", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISMEN", "ISYAT", "ITTFH", "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARYE", "KATMR", "KAYSE", "KCAER", "KCHOL", "KFEIN", "KIMMR", "KLSYN", "KLYAS", "KMPUR", "KNFRT", "KONKA", "KONTR", "KONYA", "KORDS", "KOTON", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", "KRSTL", "KRVGD", "KSTUR", "KTSKR", "KUTPO", "KUVVA", "KUYAS", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LINK", "LMKDC", "LOGO", "LKMNH", "LUKSK", "MAALT", "MAGEN", "MAKIM", "MAOTK", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEGMT", "MEKAG", "MEPET", "MERCN", "MERKO", "METRO", "METUR", "MHRGY", "MIATK", "MIGRS", "MILPA", "MOGAN", "MOBTL", "MPARK", "MSGYO", "MTRKS", "NATEN", "NETAS", "NIBAS", "NTHOL", "NTTUR", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYLUM", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT", "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRKAB", "PRKME", "PRZMA", "PSDTC", "QNBFL", "QNBFB", "QUAGR", "RALYH", "RAYSG", "REEDR", "RNPOL", "RTALB", "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", "SANFO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK", "SEKUR", "SELEC", "SELGD", "SERVE", "SILVR", "SISE", "SKBNK", "SKTAS", "SKYMD", "SMART", "SMRTG", "SNGYO", "SNICA", "SNKPA", "SOKM", "SONME", "SRVGY", "SUMAS", "SUWEN", "TABGD", "TARKM", "TATEN", "TAVHL", "TBTAS", "TCELL", "TDGYO", "TEKFU", "TERA", "TETMT", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMPOL", "TMSN", "TOASO", "TRCAS", "TRGYO", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YEOTK", "YESIL", "YGGYO", "YKBNK", "YKGYO", "YLBT", "YNSYS", "YONGA", "YUNSA", "YYAPI", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"
]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- KATILIM ENDEKSİ KAHİNİ ---
def katilim_kahini():
    try:
        ktum = yf.download("XTKUA.IS", period="2d", interval="1d", progress=False)
        if len(ktum) < 2: return "🔮 **Kahin:** Veri bekleniyor."
        degisim = ((ktum['Close'].iloc[-1] - ktum['Close'].iloc[-2]) / ktum['Close'].iloc[-2]) * 100
        if degisim > 1.0:
            return f"🚀 **KAHİN:** Katılım Endeksi dün %{degisim:.2f} yükseldi. Bugün POZİTİF bir başlangıç muhtemel."
        elif degisim < -1.0:
            return f"📉 **KAHİN:** Katılım Endeksi dün %{degisim:.2f} düştü. Bugün TEMKİNLİ olunmalı."
        else:
            return f"🟡 **KAHİN:** Katılım Endeksi dün %{degisim:.2f} ile yatay kapattı. Sakin bir açılış bekliyorum."
    except:
        return "🔮 Kahin şu an endeks verisine ulaşamıyor."

# --- AI ANALİZ MOTORU ---
def ai_beyin(t):
    skor = 0
    notlar = []
    if t['fiyat'] > t['ema200']:
        skor += 2
        notlar.append("✅ Trend üstü.")
    else:
        skor -= 2
        notlar.append("⚠️ Trend altı.")
    if t['rsi'] < 30:
        skor += 4
        notlar.append("🟢 RSI: Dip.")
    elif t['rsi'] > 70:
        skor -= 4
        notlar.append("🔴 RSI: Tepe.")
    
    if skor >= 5: karar = "🔥 GÜÇLÜ AL"
    elif 1 <= skor < 5: karar = "✅ OLUMLU"
    elif -2 <= skor < 1: karar = "🟡 NÖTR"
    else: karar = "⚠️ RİSKLİ"
    return karar, "\n".join(notlar)

def teknik_hesapla(df):
    try:
        if df is None or len(df) < 15: return None
        # DataFrame MultiIndex ise temizle
        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'].iloc[:, 0]
        else:
            close = df['Close']
            
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        return {"rsi": rsi.iloc[-1], "ema200": ema200, "fiyat": close.iloc[-1]}
    except: return None

# --- BOT İŞLEMLERİ ---
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    msg = bot.send_message(message.chat.id, f"🔍 **Katılım Analiz:** {hisse}...")
    try:
        data = yf.download(f"{hisse}.IS", period="1y", interval="1d", progress=False, timeout=15)
        t = teknik_hesapla(data)
        if t:
            karar, detay = ai_beyin(t)
            bot.edit_message_text(f"🏛️ **KATILIM HİSSE:** {hisse}\n━━━━━━━━━━━━━━━\n📢 **KARAR:** `{karar}`\n\n📝 **AI NOTU:**\n{detay}\n\n🔢 **Fiyat:** {t['fiyat']:.2f} TL\n━━━━━━━━━━━━━━━", msg.chat.id, msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"⚠️ {hisse} verisi alınamadı.", msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ İşlem hatası.", msg.chat.id, msg.message_id)

@bot.message_handler(commands=['tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "🔎 **422 Katılım Hissesi Taranıyor...**\n(Sinyaller 20'şerli gruplar halinde gelecek)")
    
    chunk_size = 20
    found_any = False
    
    for i in range(0, len(KATILIM_HISSES), chunk_size):
        chunk = KATILIM_HISSES[i:i + chunk_size]
        tickers = [f"{s}.IS" for s in chunk]
        
        try:
            # Grup grup indirerek RAM'i koruyoruz
            data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False, timeout=30)
            
            sinyaller = []
            for s in chunk:
                ticker_df = data[f"{s}.IS"]
                if not ticker_df.empty and len(ticker_df) > 14:
                    t = teknik_hesapla(ticker_df)
                    if t and (t['rsi'] < 35 or t['rsi'] > 75):
                        karar, _ = ai_beyin(t)
                        sinyaller.append(f"🔹 **{s}**: {t['fiyat']:.2f} TL -> {karar} (RSI: {t['rsi']:.0f})")
                        found_any = True
            
            if sinyaller:
                bot.send_message(message.chat.id, "\n".join(sinyaller))
            
            time.sleep(1) # Render kilitlenmesin diye kısa mola
            
        except:
            continue

    if not found_any:
        bot.send_message(message.chat.id, "✅ Tarama tamamlandı. Ekstrem sinyal bulunamadı.")

def sabah_taraması():
    tahmin = katilim_kahini()
    bot.send_message(MY_CHAT_ID, f"{tahmin}\n\n☀️ **GÜNAYDIN! Bugünkü Katılım Fırsatları:**")
    # Sabah sadece ilk 40 hisseye hızlıca bak
    try:
        tickers = [f"{s}.IS" for s in KATILIM_HISSES[:40]]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        for s in KATILIM_HISSES[:40]:
            t = teknik_hesapla(data[f"{s}.IS"])
            if t and t['rsi'] < 35:
                bot.send_message(MY_CHAT_ID, f"🟢 **Fırsat:** {s} ({t['fiyat']:.2f} TL) - RSI Dipte!")
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
