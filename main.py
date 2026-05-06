import os
import telebot
import yfinance as yf
import time
import pandas as pd
import numpy as np
import requests
from flask import Flask, request

# --- AYARLAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROK_API_KEY = os.environ.get("GROK_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# Hisseler (Ayhan Bey'in 422'lik Listesi)
KATILIM_HISSES = ["A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSUE", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGGEN", "ANHYT", "ANSGR", "ARCLK", "ARDYZ", "ARENA", "ARSGR", "ARZUM", "ASCEY", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATATP", "ATEKS", "ATLAS", "AVGYO", "AVHOL", "AVOD", "AVTUR", "AYCES", "AYDEM", "AYEN", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BANVT", "BARMA", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIZIM", "BJKAS", "BLCYT", "BMTKS", "BNTAS", "BOBET", "BORLS", "BRISA", "BRLSM", "BRMEN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "CANTE", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEOAS", "CIMSA", "CLEBI", "CONSE", "COSMO", "CRDFA", "CUSAN", "CVMEK", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DATGATE", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA", "DGATE", "DGGYO", "DIRIT", "DMSAS", "DOAS", "DOBUR", "DOGUB", "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKOS", "ELITE", "EMKEL", "ENERY", "ENJSA", "ENKAI", "ENSRI", "EPLAS", "ERBOS", "EREGL", "ERSU", "ESCAR", "ESCOM", "ESEN", "ETILR", "EUHOL", "EUPWR", "EUREN", "EUROB", "EUYO", "EYGYO", "FADE", "FENER", "FLAP", "FONET", "FORMT", "FRIGO", "FROTO", "FZPLP", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLRYH", "GLYHO", "GMTAS", "GOODY", "GOZDE", "GRNYO", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATAS", "HEKTS", "HKTM", "HOROZ", "HRKET", "HUBVC", "HUNER", "ICBCT", "IDEAS", "IDGYO", "IEYHO", "IHEVA", "IHLAS", "IHLGM", "IHGZT", "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INVES", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISMEN", "ISYAT", "ITTFH", "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARYE", "KATMR", "KAYSE", "KCAER", "KCHOL", "KFEIN", "KIMMR", "KLSYN", "KLYAS", "KMPUR", "KNFRT", "KONKA", "KONTR", "KONYA", "KORDS", "KOTON", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", "KRSTL", "KRVGD", "KSTUR", "KTSKR", "KUTPO", "KUVVA", "KUYAS", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LINK", "LMKDC", "LOGO", "LKMNH", "LUKSK", "MAALT", "MAGEN", "MAKIM", "MAOTK", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEGMT", "MEKAG", "MEPET", "MERCN", "MERKO", "METRO", "METUR", "MHRGY", "MIATK", "MIGRS", "MILPA", "MOGAN", "MOBTL", "MPARK", "MSGYO", "MTRKS", "NATEN", "NETAS", "NIBAS", "NTHOL", "NTTUR", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYLUM", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT", "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRKAB", "PRKME", "PRZMA", "PSDTC", "QNBFL", "QNBFB", "QUAGR", "RALYH", "RAYSG", "REEDR", "RNPOL", "RTALB", "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", "SANFO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK", "SEKUR", "SELEC", "SELGD", "SERVE", "SILVR", "SISE", "SKBNK", "SKTAS", "SKYMD", "SMART", "SMRTG", "SNGYO", "SNICA", "SNKPA", "SOKM", "SONME", "SRVGY", "SUMAS", "SUWEN", "TABGD", "TARKM", "TATEN", "TAVHL", "TBTAS", "TCELL", "TDGYO", "TEKFU", "TERA", "TETMT", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMPOL", "TMSN", "TOASO", "TRCAS", "TRGYO", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YEOTK", "YESIL", "YGGYO", "YKBNK", "YKGYO", "YLBT", "YNSYS", "YONGA", "YUNSA", "YYAPI", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- GROK AI MOTORU ---
def grok_yorumla(hisse, t):
    if not GROK_API_KEY: return "AI yorumu kapalı."
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"BIST100 hissesi {hisse} için veriler: Fiyat:{t['fiyat']}, RSI:{t['rsi']:.0f}, Skor:{t['skor']}/10. Teknik görünümü katılım endeksi hassasiyetiyle tek cümle yorumla."
    payload = {"model": "grok-beta", "messages": [{"role": "user", "content": prompt}], "max_tokens": 60}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        return res.json()['choices'][0]['message']['content']
    except: return "Analiz bekleniyor..."

# --- GELİŞMİŞ TEKNİK ANALİZ ---
def derin_analiz(df):
    try:
        df = df.dropna()
        if len(df) < 50: return None
        
        close = df['Close']
        vol = df['Volume']
        
        # RSI & EMA
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        ema200 = close.ewm(span=200, adjust=False).mean()
        
        # Skorlama Mantığı (10 üzerinden)
        skor = 5 # Nötr başlangıç
        if rsi.iloc[-1] < 35: skor += 3
        if rsi.iloc[-1] > 70: skor -= 3
        if close.iloc[-1] > ema200.iloc[-1]: skor += 2
        else: skor -= 1
        if vol.iloc[-1] > vol.rolling(10).mean().iloc[-1] * 1.3: skor += 2
        
        fiyat = close.iloc[-1]
        tp = fiyat * 1.05 # %5 Hedef
        sl = fiyat * 0.97 # %3 Stop
        
        return {
            "fiyat": round(fiyat, 2),
            "rsi": rsi.iloc[-1],
            "skor": min(max(skor, 1), 10),
            "tp": round(tp, 2),
            "sl": round(sl, 2),
            "hacim_ikon": "🔥" if vol.iloc[-1] > vol.rolling(10).mean().iloc[-1] else "⚪"
        }
    except: return None

# --- BOT İŞLEMLERİ ---
@bot.message_handler(commands=['tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "🎯 **Yapay Zeka En İyi 5 Fırsatı Seçiyor...**")
    
    tum_sinyaller = []
    chunk_size = 20
    
    for i in range(0, len(KATILIM_HISSES), chunk_size):
        chunk = KATILIM_HISSES[i:i+chunk_size]
        tickers = [f"{s}.IS" for s in chunk]
        try:
            data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', progress=False)
            for s in chunk:
                t = derin_analiz(data[f"{s}.IS"])
                if t and t['skor'] >= 7: # Sadece 7/10 ve üzeri skorları listeye al
                    t['hisse'] = s
                    tum_sinyaller.append(t)
            time.sleep(1)
        except: continue

    # Skorlara göre sırala ve ilk 5'i al
    en_iyiler = sorted(tum_sinyaller, key=lambda x: x['skor'], reverse=True)[:5]
    
    if not en_iyiler:
        bot.send_message(message.chat.id, "⚠️ Şu an kriterlere uygun 'Güçlü' sinyal bulunamadı.")
        return

    rapor = "🔥 **BIST TOP 5 SİNYAL (AI)**\n━━━━━━━━━━━━━━━\n"
    for idx, item in enumerate(en_iyiler, 1):
        yorum = grok_yorumla(item['hisse'], item)
        rapor += (
            f"{idx}️⃣ **{item['hisse']}** → Skor: {item['skor']}/10 🟢\n"
            f"💰 Giriş: {item['fiyat']}₺\n"
            f"🎯 Hedef: {item['tp']}₺ | 🛑 Stop: {item['sl']}₺\n"
            f"📊 Hacim: {item['hacim_ikon']}\n"
            f"🤖 **Grok:** {yorum}\n"
            f"━━━━━━━━━━━━━━━\n"
        )
    
    bot.send_message(message.chat.id, rapor, parse_mode="Markdown")

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return "OK", 200
    return "Forbidden", 403

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
