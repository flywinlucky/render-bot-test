import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get("BOT_TOKEN", "8398943601:AAEzb3okZXiN6QRVgfsYk3e6dMCB-ybBlcY")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Comandă /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salut!")

# Orice mesaj
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Hello!")

# Endpoint-ul pentru webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# Endpoint de test
@app.route("/", methods=['GET'])
def home():
    return "Botul este online!"

if __name__ == "__main__":
    ENV = os.environ.get("ENV", "prod")  # local sau prod
    if ENV == "prod":
        # Setează webhook-ul (modifică <adresa-ta-publica> cu domeniul/serverul tău)
        WEBHOOK_URL = os.environ.get("WEBHOOK_URL", f"https://render-bot-test-eq72.onrender.com/{TOKEN}")
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        port = int(os.environ.get('PORT', 5000))
        app.run(host="0.0.0.0", port=port)
    else:
        # Rulează local cu polling
        bot.remove_webhook()
        bot.polling()