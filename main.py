import os
import telebot
import yfinance as yf
import time
import pandas as pd
import numpy as np
import requests
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROK_API_KEY = os.environ.get("GROK_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# 422 Hisse Listesi (Kısaltmadan Tam Liste Kullanılacak)
KATILIM_HISSES = ["A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSUE", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGGEN", "ANHYT", "ANSGR", "ARCLK", "ARDYZ", "ARENA", "ARSGR", "ARZUM", "ASCEY", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATATP", "ATEKS", "ATLAS", "AVGYO", "AVHOL", "AVOD", "AVTUR", "AYCES", "AYDEM", "AYEN", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BANVT", "BARMA", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIZIM", "BJKAS", "BLCYT", "BMTKS", "BNTAS", "BOBET", "BORLS", "BRISA", "BRLSM", "BRMEN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "CANTE", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEOAS", "CIMSA", "CLEBI", "CONSE", "COSMO", "CRDFA", "CUSAN", "CVMEK", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DATGATE", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA", "DGATE", "DGGYO", "DIRIT", "DMSAS", "DOAS", "DOBUR", "DOGUB", "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKOS", "ELITE", "EMKEL", "ENERY", "ENJSA", "ENKAI", "ENSRI", "EPLAS", "ERBOS", "EREGL", "ERSU", "ESCAR", "ESCOM", "ESEN", "ETILR", "EUHOL", "EUPWR", "EUREN", "EUROB", "EUYO", "EYGYO", "FADE", "FENER", "FLAP", "FONET", "FORMT", "FRIGO", "FROTO", "FZPLP", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLRYH", "GLYHO", "GMTAS", "GOODY", "GOZDE", "GRNYO", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATAS", "HEKTS", "HKTM", "HOROZ", "HRKET", "HUBVC", "HUNER", "ICBCT", "IDEAS", "IDGYO", "IEYHO", "IHEVA", "IHLAS", "IHLGM", "IHGZT", "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INVES", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISMEN", "ISYAT", "ITTFH", "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARYE", "KATMR", "KAYSE", "KCAER", "KCHOL", "KFEIN", "KIMMR", "KLSYN", "KLYAS", "KMPUR", "KNFRT", "KONKA", "KONTR", "KONYA", "KORDS", "KOTON", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", "KRSTL", "KRVGD", "KSTUR", "KTSKR", "KUTPO", "KUVVA", "KUYAS", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LINK", "LMKDC", "LOGO", "LKMNH", "LUKSK", "MAALT", "MAGEN", "MAKIM", "MAOTK", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEGMT", "MEKAG", "MEPET", "MERCN", "MERKO", "METRO", "METUR", "MHRGY", "MIATK", "MIGRS", "MILPA", "MOGAN", "MOBTL", "MPARK", "MSGYO", "MTRKS", "NATEN", "NETAS", "NIBAS", "NTHOL", "NTTUR", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYLUM", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT", "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRKAB", "PRKME", "PRZMA", "PSDTC", "QNBFL", "QNBFB", "QUAGR", "RALYH", "RAYSG", "REEDR", "RNPOL", "RTALB", "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", "SANFO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK", "SEKUR", "SELEC", "SELGD", "SERVE", "SILVR", "SISE", "SKBNK", "SKTAS", "SKYMD", "SMART", "SMRTG", "SNGYO", "SNICA", "SNKPA", "SOKM", "SONME", "SRVGY", "SUMAS", "SUWEN", "TABGD", "TARKM", "TATEN", "TAVHL", "TBTAS", "TCELL", "TDGYO", "TEKFU", "TERA", "TETMT", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMPOL", "TMSN", "TOASO", "TRCAS", "TRGYO", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YEOTK", "YESIL", "YGGYO", "YKBNK", "YKGYO", "YLBT", "YNSYS", "YONGA", "YUNSA", "YYAPI", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- GROK ANALİZ (Hızlı Özet) ---
def grok_ozetle(hisse, t):
    if not GROK_API_KEY: return "AI yorumu kapalı."
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"{hisse} ({t['fiyat']:.2f}TL), RSI:{t['rsi']:.0f}, Hacim Artışı:{t['hacim_artis']}. Kısa bir teknik yorum yap."
    payload = {"model": "grok-beta", "messages": [{"role": "user", "content": prompt}], "max_tokens": 50}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        return res.json()['choices'][0]['message']['content']
    except: return "Analiz yapılamadı."

# --- TEKNİK ANALİZ ---
def teknik_analiz_yap(df):
    try:
        df = df.dropna()
        if len(df) < 30: return None
        
        close = df['Close']
        vol = df['Volume']
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        # Hacim (Son hacim vs 10 günlük ortalama)
        avg_vol = vol.rolling(10).mean().iloc[-2]
        curr_vol = vol.iloc[-1]
        hacim_artis = "VAR" if curr_vol > avg_vol * 1.5 else "YOK"
        
        ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
        
        return {
            "fiyat": close.iloc[-1],
            "rsi": rsi.iloc[-1],
            "ema200": ema200,
            "hacim_artis": hacim_artis,
            "hacim_ikon": "🔥" if hacim_artis == "VAR" else "⚪"
        }
    except: return None

# --- BOT KOMUTLARI ---
@bot.message_handler(commands=['tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "⚡ **422 Hisse İçin Derin Tarama Başladı...**\n(Hacim ve AI yorumları dahil ediliyor. Bu işlem birkaç dakika sürebilir.)")
    
    chunk_size = 10 
    found_count = 0
    
    for i in range(0, len(KATILIM_HISSES), chunk_size):
        chunk = KATILIM_HISSES[i:i+chunk_size]
        tickers = [f"{s}.IS" for s in chunk]
        
        try:
            data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', progress=False)
            mesaj_paketi = []
            
            for s in chunk:
                t = teknik_analiz_yap(data[f"{s}.IS"])
                if t:
                    # Karar Mekanizması
                    if t['rsi'] < 35: dot = "🟢"; karar = "ALIM BÖLGESİ"
                    elif t['rsi'] > 70: dot = "🔴"; karar = "DOYUM BÖLGESİ"
                    else: dot = "🟡"; karar = "NÖTR"
                    
                    # Sinyal kriteri (Hacim artışı olanlar veya RSI uçlarda olanlar)
                    if t['rsi'] < 38 or t['rsi'] > 65 or t['hacim_artis'] == "VAR":
                        grok_vurgu = grok_ozetle(s, t)
                        mesaj_paketi.append(
                            f"{dot} **{s}**: {t['fiyat']:.2f} TL\n"
                            f"📊 RSI: {t['rsi']:.0f} | Hacim: {t['hacim_ikon']}\n"
                            f"🤖 **Grok:** {grok_vurgu}\n"
                            f"------------------------"
                        )
                        found_count += 1
            
            if mesaj_paketi:
                bot.send_message(message.chat.id, "\n".join(mesaj_paketi))
            
            time.sleep(3) # Render'ın "Dur sen çok işlem yaptın" dememesi için bekleme
            
        except Exception as e:
            continue

    bot.send_message(message.chat.id, f"🏁 **Tarama Tamamlandı.** {found_count} önemli sinyal raporlandı.")

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
