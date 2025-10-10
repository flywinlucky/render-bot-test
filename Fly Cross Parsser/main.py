# telegram_bot_scraper_bot.py
# Bot Telegram care răspunde la comenzi și descarcă detalii + imagini de produs de pe pumamoldova.md
# și trimite conținutul (imagini + text) direct în chatul utilizatorului.

import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import telebot

# === CONFIGURARE BOT ===
TOKEN = "8423056299:AAEPgP1bsEWx9SFHlAeTu5cHxB0hi4oh_fk"
bot = telebot.TeleBot(TOKEN)

# === FUNCȚII AUXILIARE ===
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

base_url = "https://pumamoldova.md"

def clean_folder_name(name):
    name = name.replace(' ', '_')
    return re.sub(r'[^\w\-\.]+', '', name)

def scrape_and_send(chat_id, url):
    try:
        raspuns_initial = requests.get(url, headers=headers)
        raspuns_initial.raise_for_status()
        soup_initial = BeautifulSoup(raspuns_initial.text, 'html.parser')

        culori_de_procesat = []
        container_culori = soup_initial.find('div', class_='styles_colors__xzK99')
        if container_culori:
            linkuri_culori = container_culori.find_all('a', class_='styles_colors_item__ugdmF')
            for link in linkuri_culori:
                nume_culoare_tag = link.find('span', class_='styles_colors_item_name__5MA9U')
                if link.has_attr('href') and nume_culoare_tag:
                    nume_culoare = nume_culoare_tag.get_text(strip=True)
                    url_complet = urljoin(base_url, link['href'])
                    culori_de_procesat.append({'nume': nume_culoare, 'url': url_complet})

        if not culori_de_procesat:
            culori_de_procesat.append({'nume': 'imagini', 'url': url})

        nume_produs = soup_initial.find('h1').get_text(strip=True)
        pret_complet = f"{soup_initial.find('span', class_='styles_prices_base_value__1SsGq').get_text(strip=True)} {soup_initial.find('span', class_='styles_prices_base_currency__waD_x').get_text(strip=True)}"
        try:
            container_marimi = soup_initial.find('div', class_='styles_sizes_items___VYog')
            lista_marimi = [m.get_text(strip=True) for m in container_marimi.find_all('div', class_='styles_sizes_items_item__X5XFg')]
            marimi_text = ", ".join(lista_marimi)
        except:
            marimi_text = "N/A"

        descriere_completa = soup_initial.find('div', id='fullDescription').get_text(separator='\n', strip=True)

        text_final = (
            f"🛍️ *{nume_produs}*\n"
            f"💰 Preț: {pret_complet}\n"
            f"📏 Mărimi disponibile: {marimi_text}\n"
        )
        if len(culori_de_procesat) > 1 or culori_de_procesat[0]['nume'] != 'imagini':
            text_final += f"🎨 Culori: {', '.join([c['nume'] for c in culori_de_procesat])}\n"

        text_final += f"\n📖 *Descriere:*\n{descriere_completa}"
        bot.send_message(chat_id, text_final, parse_mode='Markdown')

        for culoare_info in culori_de_procesat:
            nume_culoare = culoare_info['nume']
            url_culoare = culoare_info['url']
            try:
                raspuns = requests.get(url_culoare, headers=headers)
                soup = BeautifulSoup(raspuns.text, 'html.parser')
                elemente_imagini = soup.find_all('a', attrs={'data-fancybox': 'gallery'})
                if not elemente_imagini:
                    continue
                media = []
                for element in elemente_imagini[:10]:  # max 10 imagini per culoare
                    link_imagine = element['href']
                    imagine_data = requests.get(link_imagine, headers=headers).content
                    media.append(telebot.types.InputMediaPhoto(imagine_data, caption=f"{nume_culoare}"))
                if media:
                    bot.send_media_group(chat_id, media)
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ Eroare la imaginile pentru {nume_culoare}: {e}")

        bot.send_message(chat_id, f"✅ Produsul '{nume_produs}' a fost procesat complet!")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Eroare generală: {e}")

# === HANDLER TELEGRAM ===
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Trimite un link de produs de pe pumamoldova.md pentru a vedea pozele și detaliile direct aici.")

@bot.message_handler(func=lambda m: True)
def process_message(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "Te rog trimite un link valid (ex: https://pumamoldova.md/...)")
        return

    bot.reply_to(message, "⏳ Se procesează linkul, te rog așteaptă...")
    scrape_and_send(message.chat.id, url)

# === MAIN ===
if __name__ == '__main__':
    print("Botul PUMA cu trimitere imagini este activ local. Apasă Ctrl+C pentru oprire.")
    bot.infinity_polling()
