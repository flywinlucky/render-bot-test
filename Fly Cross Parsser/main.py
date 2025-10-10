# telegram_bot_scraper_bot_simple.py
# Telegram bot: preia informații despre produse Puma Moldova și imagini; trimite fiecare secțiune în blocuri monospace

import os
import re
import requests
import io
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import telebot
from telebot import types
from html import escape

# === CONFIGURARE BOT ===
TOKEN = "8423056299:AAEPgP1bsEWx9SFHlAeTu5cHxB0hi4oh_fk"
bot = telebot.TeleBot(TOKEN)

# === HEADERE & URL DE BAZĂ ===
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}
base_url = "https://pumamoldova.md"

# === FUNCȚII UTILE ===

def clean_folder_name(name):
    name = name.replace(' ', '_')
    return re.sub(r'[^\w\-\.]+', '', name)


def detect_gender(url):
    url_lower = url.lower()
    if 'female' in url_lower:
        return 'Femeie'
    elif 'male' in url_lower:
        return 'Bărbat'
    elif 'unisex' in url_lower:
        return 'Unisex'
    elif 'boys' in url_lower:
        return 'Băieți'
    elif 'girls' in url_lower:
        return 'Fete'
    else:
        return 'Unisex'


def progress_bar(bot, chat_id, step, total, message_id=None):
    if total <= 0:
        total = 1
    bar_length = 10
    progress = int((step / total) * bar_length)
    bar = '█' * progress + '░' * (bar_length - progress)
    percent = int((step / total) * 100)
    text = f"Se procesează imaginile... {bar} {percent}%"
    if message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
        except Exception:
            return bot.send_message(chat_id, text)
    else:
        return bot.send_message(chat_id, text)


# === FUNCȚIE DE SCRAPING ===

def scrape_and_send(chat_id, url):
    try:
        bot.send_chat_action(chat_id, 'typing')
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        product_name_tag = soup.find('h1')
        product_name = product_name_tag.get_text(strip=True) if product_name_tag else 'N/A'

        price_value_tag = soup.find('span', class_='styles_prices_base_value__1SsGq')
        price_currency_tag = soup.find('span', class_='styles_prices_base_currency__waD_x')
        price_value = price_value_tag.get_text(strip=True) if price_value_tag else 'N/A'
        price_currency = price_currency_tag.get_text(strip=True) if price_currency_tag else ''
        price = f"{price_value} {price_currency}".strip()

        try:
            size_container = soup.find('div', class_='styles_sizes_items___VYog')
            sizes = [m.get_text(strip=True) for m in size_container.find_all('div', class_='styles_sizes_items_item__X5XFg')]
            size_text = ", ".join(sizes) if sizes else 'N/A'
        except Exception:
            size_text = 'N/A'

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

        description_full_tag = soup.find('div', id='fullDescription')
        description_full = description_full_tag.get_text(separator=' ', strip=True) if description_full_tag else ''

        # Eliminăm textul 'о товаре' și păstrăm doar conținutul
        description_full = re.sub(r'^о товаре\s*', '', description_full, flags=re.IGNORECASE)

        # Separăm textul descriptiv de caracteristici și materiale
        desc_parts = re.split(r'Характеристики:|Материалы:', description_full)
        desc_main = ' '.join(desc_parts[0].split()) if len(desc_parts) >= 1 else ''  # toate liniile la un loc
        features = ' '.join(desc_parts[1].split()) if len(desc_parts) > 1 else ''
        materials = ' '.join(desc_parts[2].split()) if len(desc_parts) > 2 else ''

        gender = detect_gender(url)

        summary_lines = [f"Preț: {price}", f"Mărimi: {size_text}", f"Gen: {gender}"]
        if len(color_data) > 1 or color_data[0]['name'] != 'default':
            summary_lines.append(f"Culori: {', '.join([c['name'] for c in color_data])}")
        summary_text = "\n".join(summary_lines)
        bot.send_message(chat_id, f"<pre>{escape(summary_text)}</pre>", parse_mode='HTML')

        if desc_main:
            desc_block = f"Descriere produs:\n\n{desc_main}"
            bot.send_message(chat_id, f"<pre>{escape(desc_block)}</pre>", parse_mode='HTML')

        if features:
            features_block = f"Caracteristici:\n\n{features}"
            bot.send_message(chat_id, f"<pre>{escape(features_block)}</pre>", parse_mode='HTML')

        if materials:
            materials_block = f"Materiale:\n\n{materials}"
            bot.send_message(chat_id, f"<pre>{escape(materials_block)}</pre>", parse_mode='HTML')

        total_colors = len(color_data)
        progress_msg = progress_bar(bot, chat_id, 0, total_colors)

        for i, color_info in enumerate(color_data, start=1):
            color_name = color_info['name']
            color_url = color_info['url']
            try:
                color_response = requests.get(color_url, headers=headers, timeout=15)
                color_response.raise_for_status()
                soup_color = BeautifulSoup(color_response.text, 'html.parser')
                image_elements = soup_color.find_all('a', attrs={'data-fancybox': 'gallery'})
                if not image_elements:
                    continue

                media = []
                for idx, element in enumerate(image_elements[:10], start=1):
                    link_image = element.get('href')
                    if not link_image:
                        continue
                    img_bytes = requests.get(link_image, headers=headers, timeout=15).content
                    bio = io.BytesIO(img_bytes)
                    bio.name = f"imagine_{idx}.jpg"
                    media.append(telebot.types.InputMediaPhoto(bio))

                if media:
                    bot.send_media_group(chat_id, media)

            except Exception as e:
                bot.send_message(chat_id, f"Eroare la încărcarea culorii {color_name}: {e}")

            progress_bar(bot, chat_id, i, total_colors, progress_msg.message_id if progress_msg else None)

        bot.send_message(chat_id, f"Produsul '{product_name}' a fost procesat cu succes. ✅")

    except Exception as e:
        bot.send_message(chat_id, f"Eroare: {e}")


# === HANDLERE TELEGRAM ===
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('Trimite link produs')
    btn2 = types.KeyboardButton('Informații')
    markup.add(btn1, btn2)
    bot.send_message(
        message.chat.id,
        "Bun venit la Bot-ul Puma Moldova!\n\nFolosește butoanele de mai jos pentru a începe.",
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: m.text == 'Informații')
def help_message(message):
    help_text = (
        "Cum se folosește:\n\n"
        "1. Apasă 'Trimite link produs' și trimite URL-ul unui produs Puma Moldova.\n"
        "2. Așteaptă să preiau detaliile și imaginile.\n"
        "3. Urmărește bara de progres.\n"
        "4. Fiecare secțiune (descriere, caracteristici, materiale) este trimisă separat în format monospace."
    )
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(func=lambda m: m.text == 'Trimite link produs')
def request_link(message):
    bot.send_message(message.chat.id, "Te rog trimite link-ul produsului Puma (ex: https://pumamoldova.md/...)\n\nGenul va fi detectat automat din link (Bărbat, Femeie, Unisex, Băieți sau Fete).")


@bot.message_handler(func=lambda m: m.text.startswith('http'))
def process_link(message):
    url = message.text.strip()
    bot.reply_to(message, "Se procesează cererea ta, te rog așteaptă...")
    scrape_and_send(message.chat.id, url)


if __name__ == '__main__':
    print("Bot-ul Puma Moldova rulează local. Apasă Ctrl+C pentru a opri.")
    bot.infinity_polling()