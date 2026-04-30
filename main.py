import os
import telebot
import requests
import yfinance as yf
import time
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# 420 HİSSELİK LİSTENİN TAMAMI (Buraya listenizin tamamını ekleyebilirsiniz)
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

def teknik_hesapla(df):
    try:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        mf = tp * df['Volume']
        pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        mfi = 100 - (100 / (1 + (pos_mf / neg_mf)))
        return rsi.iloc[-1], mfi.iloc[-1]
    except: return 50, 50

def groq_analiz(veriler):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    prompt = f"Ayhan Bey için şu teknik hisse grubunu analiz et ve para akışına (MFI) göre strateji ver:\n{veriler}"
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        return r.json()['choices'][0]['message']['content']
    except: return "AI bu grup için şu an yanıt veremedi."

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "🚀 420 Hisse Tarama Başladı. Veriler 50'şerli gruplar halinde gelecek Ayhan Bey...")
    
    # Listeyi 50'şerli gruplara böl
    chunk_size = 50
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        try:
            data = yf.download([s + ".IS" for s in chunk], period="1mo", interval="1d", progress=False)
            grup_sonuc = []
            
            for s in chunk:
                try:
                    h_data = data.xs(s + ".IS", axis=1, level=1)
                    rsi, mfi = teknik_hesapla(h_data)
                    if mfi > 70 or rsi < 35 or rsi > 70:
                        grup_sonuc.append(f"{s}: RSI {rsi:.0f}, MFI {mfi:.0f}")
                except: continue
            
            if grup_sonuc:
                rapor = f"📦 **GRUP {int(i/chunk_size)+1} ANALİZİ**\n\n" + "\n".join(grup_sonuc)
                bot.send_message(message.chat.id, rapor)
                # AI yorumu
                ai_yorum = groq_analiz("\n".join(grup_sonuc))
                bot.send_message(message.chat.id, f"💡 **AI STRATEJİSİ:**\n{ai_yorum}")
            
            time.sleep(2) # Sunucuyu yormamak için kısa bekleme
        except: continue

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
