import os
import telebot
import yfinance as yf
import time
import pandas as pd
import numpy as np
import requests # Grok API çağrısı için eklendi
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
# xAI (Grok) API Key - Bunu Render'da Environment Variables kısmına ekle
GROK_API_KEY = os.environ.get("GROK_API_KEY", "").strip() 
MY_CHAT_ID = "SİZİN_TELEGRAM_ID_NUMARANIZ" 
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# --- 422 HİSSELİK KATILIM LİSTESİ ---
KATILIM_HISSES = ["A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSUE", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGGEN", "ANHYT", "ANSGR", "ARCLK", "ARDYZ", "ARENA", "ARSGR", "ARZUM", "ASCEY", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATATP", "ATEKS", "ATLAS", "AVGYO", "AVHOL", "AVOD", "AVTUR", "AYCES", "AYDEM", "AYEN", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BANVT", "BARMA", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIZIM", "BJKAS", "BLCYT", "BMTKS", "BNTAS", "BOBET", "BORLS", "BRISA", "BRLSM", "BRMEN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "CANTE", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEOAS", "CIMSA", "CLEBI", "CONSE", "COSMO", "CRDFA", "CUSAN", "CVMEK", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DATGATE", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA", "DGATE", "DGGYO", "DIRIT", "DMSAS", "DOAS", "DOBUR", "DOGUB", "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKOS", "ELITE", "EMKEL", "ENERY", "ENJSA", "ENKAI", "ENSRI", "EPLAS", "ERBOS", "EREGL", "ERSU", "ESCAR", "ESCOM", "ESEN", "ETILR", "EUHOL", "EUPWR", "EUREN", "EUROB", "EUYO", "EYGYO", "FADE", "FENER", "FLAP", "FONET", "FORMT", "FRIGO", "FROTO", "FZPLP", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLRYH", "GLYHO", "GMTAS", "GOODY", "GOZDE", "GRNYO", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATAS", "HEKTS", "HKTM", "HOROZ", "HRKET", "HUBVC", "HUNER", "ICBCT", "IDEAS", "IDGYO", "IEYHO", "IHEVA", "IHLAS", "IHLGM", "IHGZT", "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INVES", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISMEN", "ISYAT", "ITTFH", "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARYE", "KATMR", "KAYSE", "KCAER", "KCHOL", "KFEIN", "KIMMR", "KLSYN", "KLYAS", "KMPUR", "KNFRT", "KONKA", "KONTR", "KONYA", "KORDS", "KOTON", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", "KRSTL", "KRVGD", "KSTUR", "KTSKR", "KUTPO", "KUVVA", "KUYAS", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LINK", "LMKDC", "LOGO", "LKMNH", "LUKSK", "MAALT", "MAGEN", "MAKIM", "MAOTK", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEGMT", "MEKAG", "MEPET", "MERCN", "MERKO", "METRO", "METUR", "MHRGY", "MIATK", "MIGRS", "MILPA", "MOGAN", "MOBTL", "MPARK", "MSGYO", "MTRKS", "NATEN", "NETAS", "NIBAS", "NTHOL", "NTTUR", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYLUM", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT", "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRKAB", "PRKME", "PRZMA", "PSDTC", "QNBFL", "QNBFB", "QUAGR", "RALYH", "RAYSG", "REEDR", "RNPOL", "RTALB", "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", "SANFO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK", "SEKUR", "SELEC", "SELGD", "SERVE", "SILVR", "SISE", "SKBNK", "SKTAS", "SKYMD", "SMART", "SMRTG", "SNGYO", "SNICA", "SNKPA", "SOKM", "SONME", "SRVGY", "SUMAS", "SUWEN", "TABGD", "TARKM", "TATEN", "TAVHL", "TBTAS", "TCELL", "TDGYO", "TEKFU", "TERA", "TETMT", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMPOL", "TMSN", "TOASO", "TRCAS", "TRGYO", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YEOTK", "YESIL", "YGGYO", "YKBNK", "YKGYO", "YLBT", "YNSYS", "YONGA", "YUNSA", "YYAPI", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- GROK (xAI) MOTORU ---
def grok_analiz_yap(hisse, t):
    """Teknik verileri Grok'a gönderir ve profesyonel yorum alır."""
    if not GROK_API_KEY: return "Grok API Key eksik, yorum yapılamıyor."
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
    Sen bir borsa uzmanısın. {hisse} hissesi için şu teknik veriler elimde:
    Fiyat: {t['fiyat']:.2f} TL
    RSI: {t['rsi']:.0f}
    EMA 200: {t['ema200']:.2f} TL
    Durum: {'Trend Üstü' if t['fiyat'] > t['ema200'] else 'Trend Altı'}
    
    Bu verileri kullanarak kısa, keskin ve teknik bir yorum yap. 
    Yatırım tavsiyesi olmadığını belirt. Katılım endeksi kurallarına uygun bir dil kullan.
    """
    
    payload = {
        "model": "grok-beta",
        "messages": [{"role": "system", "content": "Profesyonel bir borsa analistisin."}, {"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.json()['choices'][0]['message']['content']
    except:
        return "Grok şu an meşgul, teknik verilere odaklanın."

# --- MATEMATİKSEL ANALİZ MOTORU ---
def ai_beyin_hizli(t):
    """Tarama sırasında hızlı sonuç için (Grok kullanmaz)"""
    skor = 0
    if t['rsi'] < 30: dot = "🟢"; skor += 4
    elif t['rsi'] > 70: dot = "🔴"; skor -= 4
    else: dot = "🟡"
    
    if t['fiyat'] > t['ema200']: skor += 2
    else: skor -= 2

    if skor >= 4: karar = "GÜÇLÜ AL"
    elif 1 <= skor < 4: karar = "OLUMLU"
    elif -2 <= skor < 1: karar = "NÖTR"
    else: karar = "RİSKLİ"
    return dot, karar

def teknik_hesapla(df):
    try:
        df = df.dropna(subset=['Close'])
        if len(df) < 20: return None
        close = df['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        fiyat = close.iloc[-1]
        if np.isnan(fiyat) or np.isnan(rsi.iloc[-1]): return None
        return {"rsi": rsi.iloc[-1], "ema200": ema200, "fiyat": fiyat}
    except: return None

# --- BOT KOMUTLARI ---
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def tekil_sorgu(message):
    hisse = message.text.upper().strip()
    msg = bot.send_message(message.chat.id, f"🔍 **Grok ile {hisse} Analiz Ediliyor...**")
    try:
        data = yf.download(f"{hisse}.IS", period="1y", interval="1d", progress=False, timeout=15)
        t = teknik_hesapla(data)
        if t:
            dot, karar = ai_beyin_hizli(t)
            # Grok'tan gerçek AI yorumu alıyoruz
            grok_yorum = grok_analiz_yap(hisse, t)
            
            sablon = (
                f"🏛️ **HİSSE:** {hisse}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📢 **KARAR:** {dot} {karar}\n\n"
                f"🔢 **Fiyat:** {t['fiyat']:.2f} TL\n"
                f"📊 **RSI:** {t['rsi']:.0f}\n"
                f"📈 **EMA 200:** {t['ema200']:.2f}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🤖 **GROK YORUMU:**\n{grok_yorum}"
            )
            bot.edit_message_text(sablon, msg.chat.id, msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"⚠️ {hisse} verisi alınamadı.", msg.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ İşlem hatası.", msg.chat.id, msg.message_id)

@bot.message_handler(commands=['tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "🔎 **Tarama Başladı...** (Noktalı ve Temiz Veri)")
    chunk_size = 25
    for i in range(0, len(KATILIM_HISSES), chunk_size):
        chunk = KATILIM_HISSES[i:i + chunk_size]
        tickers = [f"{s}.IS" for s in chunk]
        try:
            data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', progress=False, timeout=30)
            sinyaller = []
            for s in chunk:
                t = teknik_hesapla(data[f"{s}.IS"])
                if t and (t['rsi'] < 35 or t['rsi'] > 65):
                    dot, karar = ai_beyin_hizli(t)
                    sinyaller.append(f"{dot} | **{s}**: {t['fiyat']:.2f} TL (RSI: {t['rsi']:.0f})")
            if sinyaller: bot.send_message(message.chat.id, "\n".join(sinyaller))
            time.sleep(1)
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
