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
# Kendi sayısal Telegram ID'nizi buraya tırnak içinde yazın
MY_CHAT_ID = "SİZİN_TELEGRAM_ID_NUMARANIZ" 
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# --- 422 HİSSELİK DEV LİSTE ---
ALL_HISSES = [
    "A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSUE", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGGEN", "ANHYT", "ANSGR", "ARCLK", "ARDYZ", "ARENA", "ARSGR", "ARZUM", "ASCEY", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATATP", "ATEKS", "ATLAS", "AVGYO", "AVHOL", "AVOD", "AVTUR", "AYCES", "AYDEM", "AYEN", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BANVT", "BARMA", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIZIM", "BJKAS", "BLCYT", "BMTKS", "BNTAS", "BOBET", "BORLS", "BRISA", "BRLSM", "BRMEN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "CANTE", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEOAS", "CIMSA", "CLEBI", "CONSE", "COSMO", "CRDFA", "CUSAN", "CVMEK", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DATGATE", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA", "DGATE", "DGGYO", "DIRIT", "DMSAS", "DOAS", "DOBUR", "DOGUB", "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKOS", "ELITE", "EMKEL", "ENERY", "ENJSA", "ENKAI", "ENSRI", "EPLAS", "ERBOS", "EREGL", "ERSU", "ESCAR", "ESCOM", "ESEN", "ETILR", "EUHOL", "EUPWR", "EUREN", "EUROB", "EUYO", "EYGYO", "FADE", "FENER", "FLAP", "FONET", "FORMT", "FRIGO", "FROTO", "FZPLP", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLRYH", "GLYHO", "GMTAS", "GOODY", "GOZDE", "GRNYO", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATAS", "HEKTS", "HKTM", "HOROZ", "HRKET", "HUBVC", "HUNER", "ICBCT", "IDEAS", "IDGYO", "IEYHO", "IHEVA", "IHLAS", "IHLGM", "IHGZT", "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INVES", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISMEN", "ISYAT", "ITTFH", "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARYE", "KATMR", "KAYSE", "KCAER", "KCHOL", "KFEIN", "KIMMR", "KLSYN", "KLYAS", "KMPUR", "KNFRT", "KONKA", "KONTR", "KONYA", "KORDS", "KOTON", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", "KRSTL", "KRVGD", "KSTUR", "KTSKR", "KUTPO", "KUVVA", "KUYAS", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LINK", "LMKDC", "LOGO", "LKMNH", "LUKSK", "MAALT", "MAGEN", "MAKIM", "MAOTK", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEGMT", "MEKAG", "MEPET", "MERCN", "MERKO", "METRO", "METUR", "MHRGY", "MIATK", "MIGRS", "MILPA", "MOGAN", "MOBTL", "MPARK", "MSGYO", "MTRKS", "NATEN", "NETAS", "NIBAS", "NTHOL", "NTTUR", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYLUM", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT", "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRKAB", "PRKME", "PRZMA", "PSDTC", "QNBFL", "QNBFB", "QUAGR", "RALYH", "RAYSG", "REEDR", "RNPOL", "RTALB", "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", "SANFO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK", "SEKUR", "SELEC", "SELGD", "SERVE", "SILVR", "SISE", "SKBNK", "SKTAS", "SKYMD", "SMART", "SMRTG", "SNGYO", "SNICA", "SNKPA", "SOKM", "SONME", "SRVGY", "SUMAS", "SUWEN", "TABGD", "TARKM", "TATEN", "TAVHL", "TBTAS", "TCELL", "TDGYO", "TEKFU", "TERA", "TETMT", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMPOL", "TMSN", "TOASO", "TRCAS", "TRGYO", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YEOTK", "YESIL", "YGGYO", "YKBNK", "YKGYO", "YLBT", "YNSYS", "YONGA", "YUNSA", "YYAPI", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"
]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- AI BEYİN MOTORU ---
def ai_beyin(t):
    skor = 0
    notlar = []
    
    # 1. Trend (EMA200)
    if t['fiyat'] > t['ema200']:
        skor += 2
        notlar.append("✅ EMA200 üstü: Ana yön yukarı.")
    else:
        skor -= 2
        notlar.append("⚠️ EMA200 altı: Baskı sürüyor.")

    # 2. Momentum (RSI)
    if t['rsi'] < 30:
        skor += 3
        notlar.append("🟢 RSI dipte: Tepki alımı yakın.")
    elif t['rsi'] > 70:
        skor -= 3
        notlar.append("🔴 RSI tepede: Kar satışı riski.")
    
    # 3. Trend Gücü (ADX)
    if t['adx'] > 25:
        notlar.append(f"⚡ Güçlü trend (ADX: {t['adx']:.0f}).")
    else:
        notlar.append("💤 Yatay/Zayıf seyir.")

    if skor >= 4: karar = "🔥 GÜÇLÜ AL"
    elif 1 <= skor < 4: karar = "✅ OLUMLU"
    elif -2 <= skor < 1: karar = "🟡 NÖTR"
    else: karar = "⚠️ RİSKLİ"

    return karar, "\n".join(notlar)

# --- TEKNİK HESAPLAMA ---
def teknik_hesapla(df):
    try:
        if df is None or len(df) < 30: return None
        close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        tr = pd.concat([high-low, (high-close.shift(1)).abs(), (low-close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        adx = ((high.diff().abs() - low.diff().abs()).abs() / (atr + 1e-9)).rolling(14).mean() * 100
        
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        
        return {"rsi": rsi.iloc[-1], "adx": adx.iloc[-1], "ema200": ema200, "fiyat": close.iloc[-1]}
    except: return None

# --- BOT KOMUTLARI ---
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    msg = bot.send_message(message.chat.id, f"🔍 **{hisse}** Analiz Ediliyor...")
    try:
        data = yf.download(f"{hisse}.IS", period="2y", interval="1d", progress=False, timeout=15)
        t = teknik_hesapla(data)
        if t:
            karar, detay = ai_beyin(t)
            bot.edit_message_text(
                f"🏛️ **HİSSE:** {hisse}\n━━━━━━━━━━━━━━━\n"
                f"📢 **AI KARARI:** `{karar}`\n\n📝 **NOTLAR:**\n{detay}\n\n"
                f"🔢 **Fiyat:** {t['fiyat']:.2f} TL\n━━━━━━━━━━━━━━━",
                msg.chat.id, msg.message_id, parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(f"⚠️ {hisse} bulunamadı.", msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Veri hatası.", msg.chat.id, msg.message_id)

@bot.message_handler(commands=['tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "🔎 **422 Hisse taranıyor...** Sinyal verenleri atıyorum.")
    chunk_size = 15
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        sinyaller = []
        for s in chunk:
            try:
                h_data = yf.download(f"{s}.IS", period="6mo", interval="1d", progress=False, timeout=5)
                t = teknik_hesapla(h_data)
                if t and (t['rsi'] < 35 or t['rsi'] > 75):
                    karar, _ = ai_beyin(t)
                    sinyaller.append(f"🔹 **{s}**: {t['fiyat']:.2f} -> {karar}")
            except: continue
        if sinyaller:
            bot.send_message(message.chat.id, "\n".join(sinyaller))
        time.sleep(2)

# --- SABAH RAPORU ---
def sabah_taraması():
    try:
        # Sabah sadece en kritik 50 hisseye odaklanıyoruz (Kilitlenmeyi önler)
        chunk = ALL_HISSES[:50]
        firsatlar = []
        for s in chunk:
            data = yf.download(f"{s}.IS", period="6mo", interval="1d", progress=False, timeout=5)
            t = teknik_hesapla(data)
            if t and t['rsi'] < 35:
                firsatlar.append(f"🟢 {s}: {t['fiyat']:.2f} TL (RSI: {t['rsi']:.0f})")
            time.sleep(0.5)
        if firsatlar:
            bot.send_message(MY_CHAT_ID, "☀️ **GÜNAYDIN! Sabah Fırsatları:**\n\n" + "\n".join(firsatlar))
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
