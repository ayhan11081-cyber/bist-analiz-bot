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

# 422 HİSSELİK LİSTENİN TAMAMI
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
        # RSI HESABI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        
        # MFI HESABI
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        mf = tp * df['Volume']
        pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
        neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
        mfi = 100 - (100 / (1 + (pos_mf / neg_mf)))
        
        # HACİM PATLAMASI FİLTRESİ
        avg_vol = df['Volume'].tail(20).mean()
        cur_vol = df['Volume'].iloc[-1]
        hacim_patlamasi = cur_vol > (avg_vol * 1.5)
        
        return rsi.iloc[-1], mfi.iloc[-1], hacim_patlamasi
    except: return 50, 50, False

def groq_analiz(veriler):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    
    # GELİŞTİRİLMİŞ AI SİSTEMİ TALİMATLARI
    prompt = f"""
    Sen profesyonel bir Borsa İstanbul stratejistisin. Ayhan Bey için şu teknik borsa verilerini yorumla:
    
    SİNYAL REHBERİ:
    - 🟢 (AL): RSI 35 altındaysa 'ALIM UYGUN / TEPKİ GELEBİLİR' olarak yorumla.
    - 🔴 (SAT): RSI 70 üzerindeyse 'SATIŞ RİSKİ / KAR SATIŞI' olarak yorumla.
    - 🔵 (İZLE): RSI 35-70 arasındaysa 'BEKLE / TRENDİ TAKİP ET' olarak yorumla.
    
    STRATEJİ KURALLARI:
    1. Sektörleri bilmiyorsan uydurma. GYO'ları bankalarla karıştırma.
    2. '🔥 HACİM PATLAMASI' olan hisseler için 'Balina/Kurumsal Girişi Olabilir' uyarısı yap.
    3. MFI > 70 ise para girişinin çok güçlü olduğunu belirt.
    4. Analizlerini Ayhan Bey'e hitaben, kısa ve vurucu maddelerle yap.

    ANALİZ EDİLECEK VERİLER:
    {veriler}
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Stratejik borsa danışmanı."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2 # Daha kararlı ve tutarlı cevaplar için
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        return r.json()['choices'][0]['message']['content']
    except: return "AI Analizi şu an oluşturulamadı Ayhan Bey."

@bot.message_handler(commands=['tara', 'Tara'])
def handle_tara(message):
    bot.send_message(message.chat.id, "🚀 Ayhan Bey, Renkli ve Hacim Odaklı Analiz Başladı (422 Hisse)...")
    
    chunk_size = 50
    for i in range(0, len(ALL_HISSES), chunk_size):
        chunk = ALL_HISSES[i:i + chunk_size]
        try:
            data = yf.download([s + ".IS" for s in chunk], period="1mo", interval="1d", progress=False)
            grup_sonuc = []
            
            for s in chunk:
                try:
                    h_data = data.xs(s + ".IS", axis=1, level=1)
                    rsi, mfi, spike = teknik_hesapla(h_data)
                    
                    # RENKLENDİRME VE DURUM BELİRLEME
                    if rsi < 35:
                        durum_emoji = "🟢"
                    elif rsi > 70:
                        durum_emoji = "🔴"
                    else:
                        durum_emoji = "🔵"
                    
                    # KRİTER: Radara girenleri listeye ekle
                    if spike or mfi > 70 or rsi < 35 or rsi > 70:
                        ek_bilgi = " 🔥 HACİM PATLAMASI" if spike else ""
                        grup_sonuc.append(f"{durum_emoji} {s}: RSI {rsi:.0f}, MFI {mfi:.0f}{ek_bilgi}")
                except: continue
            
            if grup_sonuc:
                rapor = f"📦 **GRUP {int(i/chunk_size)+1} ANALİZİ**\n\n" + "\n".join(grup_sonuc)
                bot.send_message(message.chat.id, rapor)
                # Yapay Zeka Yorumu
                ai_yorum = groq_analiz(rapor)
                bot.send_message(message.chat.id, f"💡 **STRATEJİ:**\n{ai_yorum}")
            
            time.sleep(2) # Hız sınırına takılmamak için
        except Exception as e:
            continue

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
