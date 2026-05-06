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

# 422 Hisse Listesi (A'dan Z'ye Eksiksiz)
KATILIM_HISSES = ["A1CAP", "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSUE", "ALARK", "ALBRK", "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALTNY", "ALVES", "ANELE", "ANGGEN", "ANHYT", "ANSGR", "ARCLK", "ARDYZ", "ARENA", "ARSGR", "ARZUM", "ASCEY", "ASELS", "ASGYO", "ASTOR", "ASUZU", "ATAGY", "ATATP", "ATEKS", "ATLAS", "AVGYO", "AVHOL", "AVOD", "AVTUR", "AYCES", "AYDEM", "AYEN", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BANVT", "BARMA", "BASGZ", "BAYRK", "BEGYO", "BERA", "BEYAZ", "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIZIM", "BJKAS", "BLCYT", "BMTKS", "BNTAS", "BOBET", "BORLS", "BRISA", "BRLSM", "BRMEN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "CANTE", "CCOLA", "CELHA", "CEMAS", "CEMTS", "CEOAS", "CIMSA", "CLEBI", "CONSE", "COSMO", "CRDFA", "CUSAN", "CVMEK", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DATGATE", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA", "DGATE", "DGGYO", "DIRIT", "DMSAS", "DOAS", "DOBUR", "DOGUB", "DOHOL", "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKOS", "ELITE", "EMKEL", "ENERY", "ENJSA", "ENKAI", "ENSRI", "EPLAS", "ERBOS", "EREGL", "ERSU", "ESCAR", "ESCOM", "ESEN", "ETILR", "EUHOL", "EUPWR", "EUREN", "EUROB", "EUYO", "EYGYO", "FADE", "FENER", "FLAP", "FONET", "FORMT", "FRIGO", "FROTO", "FZPLP", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLRYH", "GLYHO", "GMTAS", "GOODY", "GOZDE", "GRNYO", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATAS", "HEKTS", "HKTM", "HOROZ", "HRKET", "HUBVC", "HUNER", "ICBCT", "IDEAS", "IDGYO", "IEYHO", "IHEVA", "IHLAS", "IHLGM", "IHGZT", "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INVES", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", "ISKPL", "ISMEN", "ISYAT", "ITTFH", "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARYE", "KATMR", "KAYSE", "KCAER", "KCHOL", "KFEIN", "KIMMR", "KLSYN", "KLYAS", "KMPUR", "KNFRT", "KONKA", "KONTR", "KONYA", "KORDS", "KOTON", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLS", "KRSTL", "KRVGD", "KSTUR", "KTSKR", "KUTPO", "KUVVA", "KUYAS", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LINK", "LMKDC", "LOGO", "LKMNH", "LUKSK", "MAALT", "MAGEN", "MAKIM", "MAOTK", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEGMT", "MEKAG", "MEPET", "MERCN", "MERKO", "METRO", "METUR", "MHRGY", "MIATK", "MIGRS", "MILPA", "MOGAN", "MOBTL", "MPARK", "MSGYO", "MTRKS", "NATEN", "NETAS", "NIBAS", "NTHOL", "NTTUR", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYLUM", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT", "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRKAB", "PRKME", "PRZMA", "PSDTC", "QNBFL", "QNBFB", "QUAGR", "RALYH", "RAYSG", "REEDR", "RNPOL", "RTALB", "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", "SANFO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK", "SEKUR", "SELEC", "SELGD", "SERVE", "SILVR", "SISE", "SKBNK", "SKTAS", "SKYMD", "SMART", "SMRTG", "SNGYO", "SNICA", "SNKPA", "SOKM", "SONME", "SRVGY", "SUMAS", "SUWEN", "TABGD", "TARKM", "TATEN", "TAVHL", "TBTAS", "TCELL", "TDGYO", "TEKFU", "TERA", "TETMT", "TGSAS", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMPOL", "TMSN", "TOASO", "TRCAS", "TRGYO", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YEOTK", "YESIL", "YGGYO", "YKBNK", "YKGYO", "YLBT", "YNSYS", "YONGA", "YUNSA", "YYAPI", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- GROK AI YORUMU ---
def grok_yorumla(hisse, t):
    if not GROK_API_KEY: return "AI yorumu devre dışı (Key yok)."
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"BIST hissesi {hisse} verileri: Fiyat:{t['fiyat']}, RSI:{t['rsi']:.0f}, Skor:{t['skor']}/10. Teknik görünümü uzman gözüyle tek cümle özetle."
    payload = {"model": "grok-beta", "messages": [{"role": "user", "content": prompt}], "max_tokens": 100}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        return res.json()['choices'][0]['message']['content']
    except: return "Grok yorumu şu an alınamadı."

# --- TEKNİK ANALİZ BEYNİ ---
def derin_analiz(df, hisse_adi):
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
        
        # EMA
        ema200 = close.ewm(span=200, adjust=False).mean()
        
        # SKORLAMA (Esnetildi)
        skor = 5
        if rsi.iloc[-1] < 40: skor += 2 # Alım yönlü
        if rsi.iloc[-1] > 65: skor -= 2 # Satım yönlü
        if close.iloc[-1] > ema200.iloc[-1]: skor += 2
        if vol.iloc[-1] > vol.rolling(10).mean().iloc[-1]: skor += 1
        
        fiyat = close.iloc[-1]
        return {
            "hisse": hisse_adi,
            "fiyat": round(fiyat, 2),
            "rsi": rsi.iloc[-1],
            "skor": min(max(skor, 1), 10),
            "tp": round(fiyat * 1.05, 2), # %5 Kar Al
            "sl": round(fiyat * 0.97, 2), # %3 Stop Loss
            "hacim": "🔥" if vol.iloc[-1] > vol.rolling(10).mean().iloc[-1] * 1.2 else "⚪"
        }
    except: return None

# --- BOT KOMUTLARI ---
@bot.message_handler(commands=['tara'])
def handle_tara(message):
    status_msg = bot.send_message(message.chat.id, "🚀 **Tarama Başladı...**\n(A harfinden başlanıyor, lütfen bekleyin...)")
    
    tum_sinyaller = []
    
    # 422 Hisseyi 15'erli paketlerle tara (A harfini kaçırmamak için)
    chunk_size = 15
    for i in range(0, len(KATILIM_HISSES), chunk_size):
        chunk = KATILIM_HISSES[i:i+chunk_size]
        tickers = [f"{s}.IS" for s in chunk]
        
        try:
            # Veri indirirken hata ayıklama ekledik
            data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', progress=False, timeout=20)
            
            for s in chunk:
                ticker_data = data[f"{s}.IS"]
                # Bar verisi boş mu kontrolü
                if ticker_data.empty: continue
                
                res = derin_analiz(ticker_data, s)
                if res:
                    tum_sinyaller.append(res)
            
            # Botun yaşadığını kullanıcıya hissettir
            if i % 60 == 0:
                bot.edit_message_text(f"🔄 Tarama devam ediyor: **{s}** noktasına gelindi...", status_msg.chat.id, status_msg.message_id)
            
            time.sleep(2) # Render kilitlenmesin
        except:
            continue

    # EN İYİ 5'İ SEÇ
    en_iyiler = sorted(tum_sinyaller, key=lambda x: x['skor'], reverse=True)[:5]
    
    if not en_iyiler:
        bot.send_message(message.chat.id, "❌ Kriterlere uygun hisse bulunamadı. Lütfen daha sonra tekrar deneyin.")
        return

    rapor = "🔥 **BIST TOP 5 SİNYAL (AI)**\n━━━━━━━━━━━━━━━\n"
    for idx, item in enumerate(en_iyiler, 1):
        yorum = grok_yorumla(item['hisse'], item)
        rapor += (
            f"{idx}️⃣ **{item['hisse']}** | Skor: {item['skor']}/10 🟢\n"
            f"💰 **Giriş:** {item['fiyat']}₺\n"
            f"🎯 **TP:** {item['tp']}₺ | 🛑 **SL:** {item['sl']}₺\n"
            f"📊 **Hacim:** {item['hacim']}\n"
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
