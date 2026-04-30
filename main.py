import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# AYHAN BEY'İN TAM LİSTESİ (Sorgu anında canlı kontrol edilecek)
HISSES = [
    "THYAO", "ASELS", "EREGL", "KCHOL", "TUPRS", "SISE", "AKBNK", "BIMAS", "GARAN", "SAHOL",
    "ISCTR", "YKBNK", "ENKAI", "EKGYO", "PGSUS", "FROTO", "TOASO", "ARCLK", "PETKM", "KRDMD",
    "ASTOR", "SASA", "HEKTS", "KONTR", "SMRTG", "EUPWR", "ALARK", "KOZAL", "KOZAA", "IPEKE",
    "ODAS", "ZOREN", "CANTE", "DOHOL", "TKFEN", "MGROS", "SOKM", "AEFES", "CCOLA", "DOAS",
    "TTKOM", "TCELL", "VESTL", "VESBE", "OTKAR", "TMSN", "KORDS", "BRISA", "GUBRF", "BAGFS",
    "EGEEN", "BFREN", "ASUZU", "KARSN", "CEMTS", "PARSN", "BUCIM", "AKCNS", "NUHCM", "AFYON",
    "OYAKC", "KONYA", "GOLTS", "ASLAN", "BOBET", "QUAGR", "BIENP", "KAYSE", "CWENE", "ALFAS",
    "YEOTK", "GESAN", "SAYAS", "HUNER", "ENJSA", "GWIND", "AYDEM", "AKSEN", "AKFYE", "BIOEN",
    "TURSG", "ANSGR", "HALKB", "VAKBN", "TSKB", "SKBNK", "ALBRK", "QNBFB", "ICBCT", "PAGYO",
    "TRGYO", "SNGYO", "OZKGY", "AKFGY", "MSGYO", "KLGYO", "PSGYO", "ASGYO", "VKGYO", "HLGYO",
    "ZRGYO", "IDGYO", "PEGYO", "NTHOL", "NETAS", "KFEIN", "ARDYZ", "ESCOM", "ARENA", "INDES",
    "DESPC", "DGATE", "PENTA", "MIATK", "REEDR", "SDTTR", "FORMT", "KATMR", "KMPUR", "TARKM",
    "HKTM", "MHRGY", "KUVVA", "KOPOL", "KCAER", "GRSEL", "GOKNR", "MTRKS", "LINK", "LOGO",
    "AZTEK", "MOBTL", "FONET", "KRVGD", "TATGD", "SELGD", "KNFRT", "ULUFA", "ULUSE", "ADESE",
    "SELEC", "RTALB", "ANGEN", "TRILC", "GENIL", "MEDTR", "EBEBK", "MAVI", "VAKKO", "YATAS",
    "BRYAT", "ALCAR", "ALCTL", "KAREL", "KRONT", "PKENT", "AYGAZ", "TRCAS", "TURGG", "BRKO",
    "DIRIT", "SNPAM", "KUYAS", "PRZMA", "DERIM", "DESA", "HURGZ", "IHLAS", "IHEVA", "IHLGM",
    "IHGZT", "IHYAY", "METRO", "AVGYO", "ATLAS", "ETYAT", "AVHOL", "GLRYH", "A1CAP", "INFO",
    "OSMEN", "TERA", "PLTER", "SKYMD", "EFORC", "BYDNR", "TABGD", "HRKET", "DCTTR", "LILAK",
    "KOTON", "ALVES", "ENTRA", "MOGAN", "ARTMS", "ODINE", "ICUGS", "ALMAD", "PRKME", "IEYHO",
    "ISYHO", "USA K", "NIBAS", "EMKEL", "GEREL", "GOODY", "JANTS", "GEDIK", "INVEO", "ECILC",
    "ECZYT", "DEVA", "MPARK", "LKMNH", "TNZTP", "AHLCI", "ENERY", "PASEU", "TUKAS", "VANGD",
    "ELITE", "SUNTK", "ISSEN", "TEZOL", "ALKA", "ALKIM", "EGGUB", "KUTPO", "NGYO", "AKMGY",
    "EGSER", "IZMDC", "DITAS", "FMIZP", "MAKTK", "YAYLA", "ORCAY", "PINSU", "PNSUT", "PETUN",
    "BANVT", "MERKO", "AVOD", "KEREV", "OBASE", "PAPIL", "PKART", "BVSAN", "IMASM", "OZSUB",
    "SMART", "EDATA", "ESEN", "MAGEN", "NATEN", "CRDFA", "LIDFA", "VAKFN", "PAMEL", "BRKVY",
    "ISGSY", "GOZDE", "VERUS", "VERTU", "GLBMD", "TAVHL", "RYSAS", "RYGYO", "DERHL", "DAGHL",
    "YESIL", "YGYO", "YYAPI", "BJKAS", "FENER", "GSRAY", "TSPOR", "HUBVC"
]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def borsa_taramasi_anlik():
    semboller = [s + ".IS" for s in HISSES]
    try:
        # 1 günlük veri üzerinden anlık momentum
        data = yf.download(semboller, period="1d", interval="1m", progress=False, threads=True)
        bulgular = []
        
        for s in semboller:
            try:
                if s not in data['Close']: continue
                h_c = data['Close'][s].dropna()
                if len(h_c) < 5: continue # Yeterli anlık veri olmalı
                
                # Açılıştan beri değişim
                ilk_fiyat = h_c.iloc[0]
                son_fiyat = h_c.iloc[-1]
                degisim = ((son_fiyat - ilk_fiyat) / ilk_fiyat) * 100
                
                if abs(degisim) > 1.0: # %1 ve üzeri hareket eden her şeyi yakala
                    bulgular.append(f"{s.replace('.IS','')}: %{degisim:.2f}")
            except: continue
            
        return "\n".join(bulgular[:30]) if bulgular else "Şu an piyasada büyük bir dalgalanma yok Ayhan Bey."
    except Exception as e:
        return f"Veri hatası: {str(e)}"

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.reply_to(message, "⚡ Ayhan Bey, piyasa şu an süzülüyor, canlı verileri Groq AI uzmanına aktarıyorum...")
    veriler = borsa_taramasi_anlik()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    prompt = (
        "Sen Ayhan Bey'in 7/24 piyasa danışmanısın. Şu anki canlı verileri analiz et. "
        "Kısa, öz ve teknik konuş. Mühendis Ayhan Bey'e şu anki piyasa havasını, "
        "hisselerin neden hareketlendiğini anlık bir raporla sun. Bekleme yok, tam gaz analiz!"
    )
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Canlı BIST Verileri:\n{veriler}"}
        ]
    }
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        analiz = r.json()['choices'][0]['message']['content']
        bot.send_message(message.chat.id, f"🚀 **ANLIK OPTİMA ANALİZİ**\n\n{analiz}")
    except:
        bot.send_message(message.chat.id, f"AI bağlantısı yoğun ama sıcak veriler şunlar:\n\n{veriler}")

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
