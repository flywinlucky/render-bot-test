import telebot

# Inițializare bot cu token-ul tău
bot = telebot.TeleBot("8398943601:AAEzb3okZXiN6QRVgfsYk3e6dMCB-ybBlcY")

# Handler pentru comanda /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salut!'")

# Handler pentru orice mesaj text
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Hello!")

# Pornire bot
print("Botul rulează...")
bot.polling()