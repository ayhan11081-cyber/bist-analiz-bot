# Botunuzun TOKEN değişkeninin tam olduğundan emin olun
TOKEN = os.environ.get("TELEGRAM_TOKEN") 

# Route'u şu şekilde kesinleştirin:
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200
