# telegram_bot_scraper_bot.py
# Telegram bot that extracts and displays Puma product details beautifully in chat with progress indicators and UI elements.

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import telebot

# === BOT CONFIGURATION ===
TOKEN = "8423056299:AAEPgP1bsEWx9SFHlAeTu5cHxB0hi4oh_fk"
bot = telebot.TeleBot(TOKEN)

# === HEADERS & BASE URL ===
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}
base_url = "https://pumamoldova.md"

# === UTILITY FUNCTIONS ===
def clean_folder_name(name):
    name = name.replace(' ', '_')
    return re.sub(r'[^\w\-\.]+', '', name)

def progress_bar(bot, chat_id, step, total, message_id=None):
    bar_length = 10
    progress = int((step / total) * bar_length)
    bar = '█' * progress + '░' * (bar_length - progress)
    percent = int((step / total) * 100)
    text = f"⏳ Processing images... {bar} {percent}%"
    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
    else:
        return bot.send_message(chat_id, text)

def scrape_and_send(chat_id, url):
    try:
        bot.send_chat_action(chat_id, 'typing')
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        product_name = soup.find('h1').get_text(strip=True)
        price_value = soup.find('span', class_='styles_prices_base_value__1SsGq').get_text(strip=True)
        price_currency = soup.find('span', class_='styles_prices_base_currency__waD_x').get_text(strip=True)
        price = f"{price_value} {price_currency}"

        try:
            size_container = soup.find('div', class_='styles_sizes_items___VYog')
            sizes = [m.get_text(strip=True) for m in size_container.find_all('div', class_='styles_sizes_items_item__X5XFg')]
            size_text = ", ".join(sizes)
        except:
            size_text = "N/A"

        color_data = []
        color_container = soup.find('div', class_='styles_colors__xzK99')
        if color_container:
            color_links = color_container.find_all('a', class_='styles_colors_item__ugdmF')
            for link in color_links:
                color_name_tag = link.find('span', class_='styles_colors_item_name__5MA9U')
                if link.has_attr('href') and color_name_tag:
                    color_name = color_name_tag.get_text(strip=True)
                    color_url = urljoin(base_url, link['href'])
                    color_data.append({'name': color_name, 'url': color_url})
        if not color_data:
            color_data.append({'name': 'default', 'url': url})

        description_full = soup.find('div', id='fullDescription').get_text(separator='\n', strip=True)
        description_full = re.sub(r'(Характеристики:)', '\n\n\\1', description_full)
        description_full = re.sub(r'(Материалы:)', '\n\n\\1', description_full)

        # === STRUCTURED TEXT ===
        text_msg = (
            f"*{product_name}*\n\n"
            f"*Price:* {price}\n"
            f"*Sizes:* {size_text}\n"
        )
        if len(color_data) > 1 or color_data[0]['name'] != 'default':
            text_msg += f"🎨 *Colors:* {', '.join([c['name'] for c in color_data])}\n"

        text_msg += f"\n📖 *Description:*\n\n{description_full}"

        bot.send_message(chat_id, text_msg, parse_mode='Markdown')

        total_colors = len(color_data)
        progress_msg = progress_bar(bot, chat_id, 0, total_colors)

        for i, color_info in enumerate(color_data, start=1):
            color_name = color_info['name']
            color_url = color_info['url']

            try:
                color_response = requests.get(color_url, headers=headers)
                soup_color = BeautifulSoup(color_response.text, 'html.parser')
                image_elements = soup_color.find_all('a', attrs={'data-fancybox': 'gallery'})
                if not image_elements:
                    continue

                bot.send_message(chat_id, f"📸 *{color_name}* images:", parse_mode='Markdown')
                media = []
                for element in image_elements[:10]:
                    link_image = element['href']
                    img_data = requests.get(link_image, headers=headers).content
                    media.append(telebot.types.InputMediaPhoto(img_data))
                if media:
                    bot.send_media_group(chat_id, media)

            except Exception as e:
                bot.send_message(chat_id, f"⚠️ Error loading color {color_name}: {e}")

            progress_bar(bot, chat_id, i, total_colors, progress_msg.message_id)

        bot.send_message(chat_id, f"✅ *Product '{product_name}' processed successfully!*", parse_mode='Markdown')

    except Exception as e:
        bot.send_message(chat_id, f"❌ General error: {e}")

# === TELEGRAM HANDLERS ===
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(
        message,
        "👋 Welcome! Send me a Puma Moldova product link and I’ll fetch all details and images for you, nicely formatted.",
    )

@bot.message_handler(func=lambda m: True)
def process_message(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ Please send a valid product link (e.g., https://pumamoldova.md/...)")
        return

    bot.reply_to(message, "⏳ Processing your request, please wait...")
    scrape_and_send(message.chat.id, url)

# === MAIN ENTRY ===
if __name__ == '__main__':
    print("PUMA Product Info Bot is now running locally. Press Ctrl+C to stop.")
    bot.infinity_polling()
