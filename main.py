import os
import telebot
from google import genai
from flask import Flask, request

# ENV DEĞERLERİ
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")

if RENDER_URL and not RENDER_URL.startswith("https://"):
    RENDER_URL = "https://" + RENDER_URL

# BOT + GEMINI
bot = telebot.TeleBot(TOKEN, threaded=False)
client = genai.Client(api_key=API_KEY)

app = Flask(__name__)

# WEBHOOK ENDPOINT
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    return "ERROR", 403


# MESAJ İŞLEME
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message.text
        )

        bot.reply_to(message, response.text if response.text else "Boş cevap geldi.")

    except Exception as e:
        bot.reply_to(message, f"Hata oluştu: {str(e)}")


# ANA SAYFA
@app.route("/")
def home():
    return "BOT AKTİF"


# WEBHOOK KURULUM
bot.remove_webhook()
if RENDER_URL:
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")


# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
