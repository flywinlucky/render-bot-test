from flask import Flask, request
import requests
import os
import sqlite3
import random

app = Flask(__name__)

# --- CONFIGURARE ---
TOKEN = os.getenv("BOT_TOKEN")
# Am adăugat un URL specific pentru trimiterea de fotografii
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
TELEGRAM_API_URL_PHOTO = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
DB_FILE = "active_chats.db"

# --- LISTA DE MESAJE ȘI IMAGINI ---
# Fiecare element este acum un dicționar cu text și calea către imaginea corespunzătoare.
MESAJE = [
    {'text': "Salut! Acesta este un mesaj automat de la botul tău prietenos.", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "Bună! Sper că ai o zi productivă și plină de succes.", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "Notificare: A trecut încă un minut. Timpul zboară când te distrezi!", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "Acesta este un memento automat pentru a-ți aminti să faci o pauză.", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "Ce mai faci? Botul tău se gândește la tine.", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "Ping! Doar verificam dacă ești pe fază. O zi bună!", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "O mică notificare pentru a-ți aduce un zâmbet pe buze.", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "Mesaj automat: Sistemele funcționează în parametri normali.", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "Știai că roboții nu dorm niciodată? Sunt mereu aici pentru tine!", 'imagine': "Creatives/Creo_1.jpg"},
    {'text': "Acesta este ultimul mesaj unic din ciclu. Următorul o va lua de la capăt!", 'imagine': "Creatives/Creo_1.jpg"}
]

# Amestecăm lista o singură dată la pornirea aplicației.
random.shuffle(MESAJE)

# Contor global pentru a urmări ce mesaj a fost trimis
spam_counter = 0


# --- FUNCȚII BAZĂ DE DATE ---
def init_db():
    """Initializează baza de date și creează tabelul dacă nu există."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def load_chats():
    """Încarcă toate ID-urile de chat active din baza de date."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT chat_id FROM chats")
    rows = c.fetchall()
    conn.close()
    return set(row[0] for row in rows)

def add_chat(chat_id):
    """Adaugă un nou ID de chat în baza de date."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO chats (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def remove_chat(chat_id):
    """Șterge un ID de chat din baza de date."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

# --- RUTE FLASK ---
@app.route('/')
def home():
    """Pagină principală pentru a verifica dacă botul rulează."""
    init_db()
    return "Bot is running!"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """Gestionează mesajele primite de la utilizatori (prin webhook Telegram)."""
    init_db()
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        if text.lower() == "/start":
            add_chat(chat_id)
            reply = "Ai pornit notificările automate! Vei primi mesaje periodice."
        elif text.lower() == "/stop":
            remove_chat(chat_id)
            reply = "Ai oprit notificările automate!"
        else:
            reply = f"Comandă necunoscută. Folosește /start sau /stop."
            
        payload = {
            "chat_id": chat_id,
            "text": reply
        }
        requests.post(TELEGRAM_API_URL, json=payload)
    return "ok", 200

@app.route('/spam')
def spam():
    """Trimite un mesaj cu imagine tuturor utilizatorilor activi, în mod ciclic."""
    global spam_counter
    init_db()
    
    # Selectează perechea de mesaj și imagine folosind contorul global
    mesaj_index = spam_counter % len(MESAJE)
    mesaj_obj = MESAJE[mesaj_index]
    mesaj_text = mesaj_obj['text']
    cale_imagine = mesaj_obj['imagine']
    
    # Incrementăm contorul pentru următoarea cerere
    spam_counter += 1
    
    chats = load_chats()

    # Verificăm dacă fișierul imagine există
    if not os.path.exists(cale_imagine):
        return f"Error: Image file not found at {cale_imagine}", 500

    for chat_id in chats:
        payload = {
            "chat_id": chat_id,
            "caption": mesaj_text  # Pentru poze, textul se trimite ca 'caption'
        }
        # Deschidem fișierul imagine în mod binar și îl trimitem
        with open(cale_imagine, 'rb') as photo_file:
            files = {'photo': photo_file}
            requests.post(TELEGRAM_API_URL_PHOTO, data=payload, files=files)
            
    return f"Sent message '{mesaj_text}' with image '{cale_imagine}' to {len(chats)} users.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

