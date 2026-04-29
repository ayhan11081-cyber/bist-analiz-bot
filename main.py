import os
import telebot
from google import genai
from flask import Flask, request

# AYARLAR
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")

if RENDER_URL and not RENDER_URL.startswith("https://"):
    RENDER_URL = f"https://{RENDER_URL}"

bot = telebot.TeleBot(TOKEN, threaded=False)
client = genai.Client(api_key=API_KEY)

app = Flask(__name__)

# WEBHOOK
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_data = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message.text
        )

        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Bir cevap alınamadı.")

    except Exception as e:
        bot.reply_to(
            message,
            f"Hata oluştu Ayhan Bey: {str(e)}"
        )


@app.route("/")
def home():
    return "SİSTEM AKTİF"


# WEBHOOK AYARI
if RENDER_URL:
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
