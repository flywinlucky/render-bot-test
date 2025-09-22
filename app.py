from flask import Flask, request
import requests
import os
import sqlite3
import random
import json

app = Flask(__name__)

# --- CONFIGURARE ---
TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
TELEGRAM_API_URL_PHOTO = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
DB_FILE = "active_chats.db"

# --- ÎNCĂRCARE MESAJE DIN FIȘIERUL JSON ---
def load_messages():
    """Încarcă mesajele din fișierul messages.json."""
    try:
        with open('messages.json', 'r', encoding='utf-8') as f:
            messages = json.load(f)
        return messages
    except FileNotFoundError:
        print("Eroare: Fișierul 'messages.json' nu a fost găsit.")
        return []
    except json.JSONDecodeError:
        print("Eroare: Fișierul 'messages.json' nu este un JSON valid.")
        return []

MESAJE = load_messages()

# Amestecăm lista o singură dată la pornirea aplicației, dacă a fost încărcată corect.
if MESAJE:
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
    """Trimite un mesaj cu imagine și buton tuturor utilizatorilor activi, în mod ciclic."""
    global spam_counter
    init_db()

    if not MESAJE:
        return "Error: No messages loaded. Check messages.json file.", 500
    
    # Selectează perechea de mesaj și imagine folosind contorul global
    mesaj_index = spam_counter % len(MESAJE)
    mesaj_obj = MESAJE[mesaj_index]
    mesaj_text = mesaj_obj['text']
    cale_imagine = mesaj_obj['imagine']
    
    # Extragem textul și URL-ul butonului din obiectul mesajului
    # Folosim valori implicite în caz că nu sunt definite în JSON
    button_text = mesaj_obj.get("button_text", "Apasă aici")
    button_url = mesaj_obj.get("button_url", "https://www.google.com/")
    
    # Incrementăm contorul pentru următoarea cerere
    spam_counter += 1
    
    chats = load_chats()

    # Verificăm dacă fișierul imagine există
    if not os.path.exists(cale_imagine):
        return f"Error: Image file not found at {cale_imagine}", 500

    # Creăm structura pentru butonul de tip inline folosind datele dinamice
    reply_markup = {
        "inline_keyboard": [[
            {"text": button_text, "url": button_url}
        ]]
    }

    for chat_id in chats:
        payload = {
            "chat_id": chat_id,
            "caption": mesaj_text,
            "reply_markup": json.dumps(reply_markup)
        }
        # Deschidem fișierul imagine în mod binar și îl trimitem
        with open(cale_imagine, 'rb') as photo_file:
            files = {'photo': photo_file}
            requests.post(TELEGRAM_API_URL_PHOTO, data=payload, files=files)
            
    return f"Sent message '{mesaj_text}' with image '{cale_imagine}' and a button to {len(chats)} users.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

