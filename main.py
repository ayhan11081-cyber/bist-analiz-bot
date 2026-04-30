import os
import telebot
import requests
import yfinance as yf
from flask import Flask, request

# AYARLAR
TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
RENDER_URL = "https://bist-analiz-bot-3z19.onrender.com"

# TÜM BIST LİSTESİ (Sizin için ekledim Ayhan Bey)
HISSES = [
    "A1CAP","ACSEL","ADEL","ADESE","ADGYO","AEFES","AFYON","AGESA","AGHOL","AGROT","AHGAZ","AKBNK","AKCNS","AKENR","AKFGY","AKFYE","AKGRT","AKMGY","AKSA","AKSEN","AKSGY","AKYHO","ALARK","ALBRK","ALCAR","ALCTL","ALFAS","ALGYO","ALKA","ALKIM","ALLE","ALMAD","ALTNY","ALTIN","ANELE","ANGEN","ANHYT","ANSGR","ANTUR","APRE","ARASE","ARCLK","ARDYZ","ARENA","ARSAN","ARTMS","ASCEG","ASELS","ASGYO","ASTOR","ASUZU","ATAGY","ATAKP","ATATP","ATEKS","ATLAS","ATSGH","AVGYO","AVHOL","AVOD","AVTUR","AYCES","AYDEM","AYEN","AYGAZ","AZTEK",
    "BAGFS","BAKAB","BALAT","BANVT","BARMA","BASGZ","BASCM","BAYRK","BEGYO","BERA","BEYAZ","BFREN","BIENP","BIGCH","BIMAS","BINHO","BIOEN","BIZIM","BJKAS","BLCYT","BMSCH","BMSTL","BNTAS","BOBET","BORLS","BORSK","BOSSA","BRISA","BRKSN","BRKVY","BRLSM","BRMEN","BRYAT","BSOKE","BTCIM","BUCIM","BURCE","BURVA","BVSAN","BYDNR",
    "CANTE","CASA","CATES","CCOLA","CELHA","CEMAS","CEMTS","CEVNR","CIMSA","CLEBI","CONSE","COSMO","CRDFA","CUSAN","CVKMD","CWENE",
    "DAGHL","DAGI","DAPGM","DARDL","DATATE","DGGYO","DGNMO","DIRIT","DITAS","DMSAS","DNISI","DOAS","DOCO","DOGUB","DOHOL","DOKTA","DURDO","DYOBY","DZGYO",
    "EBEBK","ECILC","ECZYT","EDATA","EDIP","EGEEN","EGEPO","EGERV","EGPRO","EGSER","EKGYO","EKSUN","ELITE","EMKEL","ENERY","ENJSA","ENKAI","ENTRA","ERBOS","EREGL","ERSU","ESCAR","ESCOM","ESEN","ETILR","EUPWR","EUREN","EYGYO",
    "FADE","FENER","FLAP","FMIZP","FONET","FORMT","FORTE","FRIGO","FROTO","FZLGY",
    "GARAN","GARFA","GDUY","GEDIK","GEDZA","GENTS","GEREL","GESAN","GIPTA","GLBMD","GLCVY","GLRYH","GLYHO","GOKNR","GOLTS","GOODY","GOZDE","GRNYO","GRSEL","GSDDE","GSDHO","GUHRE","GUBRF","GWIND","GZNMI",
    "HALKB","HATEK","HDFGS","HEDEF","HEKTS","HKTM","HLGYO","HRKET","HTTBT","HUBVC","HUNER","HURGZ",
    "ICBCT","IDGYO","IEYHO","IHAAS","IHEVA","IHGZT","IHLAS","IHLGM","IHYAY","IMASM","INDES","INFO","INGRM","INTEM","INVEO","INVES","IPEKE","ISATR","ISBTR","ISCTR","ISFIN","ISGSY","ISGYO","ISMEN","ISSEN","ISYAT","ITTFH","IZENR","IZFAS","IZINV","IZMDC",
    "JANTS",
    "KAPLM","KARYE","KATMR","KAYSE","KCAER","KCHOL","KENT","KERVT","KFEIN","KGYO","KIMMR","KLGYO","KLMSN","KLRHO","KLSYN","KLYAS","KMEPU","KMPUR","KNFRT","KONTR","KONYA","KORDS","KOTON","KOZAL","KOZAA","KRDMA","KRDMB","KRDMD","KRGYO","KRONT","KRPLS","KRSTL","KRTEK","KSTUR","KTSKR","KUTPO","KUVVA","KUYAS","KZBGY","KZGYO",
    "LIDFA","LIDER","LMKDC","LOGAS","LOGO","LUKSK",
    "MAALT","MAGEN","MAKIM","MAKTK","MANAS","MARKA","MARTI","MAVI","MEDTR","MEGAP","MEGMT","MEPET","MERCN","MERKO","METRO","METUR","MHRGY","MIATK","MIPAZ","MNDRS","MNDTR","MOBTL","MOGAN","MPARK","MSGYO","MTRKS","MTRYO","MZHLD",
    "NATEN","NETAS","NIBAS","NTHOL","NUGYO","NUHCM",
    "OBAMS","ODAS","ONCSM","ORCAY","ORGE","ORMA","OSMEN","OSTIM","OTKAR","OYAKC","OYAYO","OYLUM",
    "PAGYO","PAMEL","PAPIL","PARSN","PASEU","PATEK","PCILT","PEGYO","PEKGY","PENTA","PETKM","PETUN","PGSUS","PINSU","PKART","PKENT","PNLSN","PNSUT","POLHO","POLTK","PRDGS","PRKAB","PRKME","PRZMA","PSDTC","PSGYO",
    "QUAGR",
    "RALYH","RAYYS","REEDR","RNPOL","RODRG","RTALB","RUBNS","RYGYO","RYSAS",
    "SAFKR","SAHOL","SAMAT","SANEL","SANFO","SANKO","SARKY","SASA","SAYAS","SDTTR","SEGYO","SEKFK","SEKUR","SELEC","SELGD","SELVA","SEYKM","SILVR","SISE","SKBNK","SKTAS","SMART","SMRTG","SNGYO","SNICA","SNKPA","SOKE","SOKM","SONME","SRVGY","SUMAS","SUNTK","SURGY","SUWEN",
    "TABGD","TARKM","TATEN","TATGD","TAVHL","TCELL","TDGYO","TEKTU","TERA","TETMT","TEZOL","THYAO","TKFEN","TKNSA","TMPOL","TMSN","TNZTP","TOASO","TRCAS","TRGYO","TRILC","TSKB","TSPOR","TTKOM","TTRAK","TUCLK","TUKAS","TUPRS","TURSG","TUREX",
    "UFUK","ULAS","ULKER","ULLAS","ULUFA","ULUSE","ULUUN","UMPAS","UNLU","USAK",
    "VAKBN","VAKFN","VAKKO","VANGD","VBTYO","VERTU","VERUS","VESBE","VESTL","VKGYO","VKING",
    "YAPRK","YAYLA","YBTAS","YEOTK","YESIL","YGGYO","YGYO","YIGIT","YKBNK","YONGA","YOTAS","YUNSA","YYLGD","YYAPI",
    "ZEDUR","ZOREN","ZRGYO"
]

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def borsa_taramasi():
    # Suffix kontrolü: .IS yoksa ekle
    semboller = [s if s.endswith(".IS") else s + ".IS" for s in HISSES]
    try:
        data = yf.download(semboller, period="2d", interval="1d", progress=False, threads=True)
        bulgular = []
        for s in semboller:
            try:
                if s not in data['Close']: continue
                h_c = data['Close'][s]
                if h_c.isnull().values.any(): continue
                degisim = ((h_c.iloc[-1] - h_c.iloc[-2]) / h_c.iloc[-2]) * 100
                if degisim > 2.0:
                    bulgular.append(f"{s.replace('.IS','')}: %{degisim:.2f}")
            except: continue
        return "\n".join(bulgular[:25]) if bulgular else "Hareketli hisse bulunamadı."
    except Exception as e:
        return f"Tarama hatası: {str(e)}"

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.reply_to(message, "🔍 Optima Robot Ayhan Bey için 450+ hisseyi süzüyor...")
    veriler = borsa_taramasi()
    
    # GROQ - SOHBET MODU
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    prompt = (
        "Sen borsa uzmanı ve Ayhan Bey'in dostusun. Verileri analiz et. "
        "Samimi bir akşam sohbeti tadında yorumla, nedenlerini açıkla ve Ayhan Bey'e teknik bir tüyo ver."
    )
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Hisse verileri:\n{veriler}"}
        ]
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        analiz = r.json()['choices'][0]['message']['content']
        bot.send_message(message.chat.id, f"🎯 **OPTIMA AKŞAM SOHBETİ**\n\n{analiz}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Hisseler:\n{veriler}\n\n(AI şu an cevap veremedi: {str(e)})")

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
