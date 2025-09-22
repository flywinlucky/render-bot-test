from flask import Flask, request
import requests
import os
import random
import json
import psycopg2
from psycopg2 import sql

app = Flask(__name__)

# --- CONFIGURARE ---
# Citim variabilele de mediu
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL") # Variabilă nouă pentru baza de date PostgreSQL

# Construim URL-urile pentru API-ul Telegram
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
TELEGRAM_API_URL_PHOTO = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"


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

# Amestecăm lista o singură dată la pornirea aplicației
if MESAJE:
    random.shuffle(MESAJE)

# Contor global pentru a urmări ciclul de mesaje
spam_counter = 0


# --- FUNCȚII BAZĂ DE DATE (MODIFICATE PENTRU POSTGRESQL) ---
def get_db_connection():
    """Stabilește o conexiune cu baza de date PostgreSQL."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Initializează baza de date și creează tabelul dacă nu există."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Folosim BIGINT pentru chat_id pentru a fi compatibil cu ID-urile Telegram
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id BIGINT PRIMARY KEY
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def load_chats():
    """Încarcă toate ID-urile de chat active din baza de date."""
    chats = set()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM chats")
        rows = cur.fetchall()
        chats = set(row[0] for row in rows)
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Eroare la încărcarea chat-urilor: {e}")
    return chats

def add_chat(chat_id):
    """Adaugă un nou ID de chat în baza de date."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # ON CONFLICT previne erorile dacă chat_id-ul există deja
        cur.execute("INSERT INTO chats (chat_id) VALUES (%s) ON CONFLICT (chat_id) DO NOTHING", (chat_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Eroare la adăugarea chat-ului: {e}")

def remove_chat(chat_id):
    """Șterge un ID de chat din baza de date."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM chats WHERE chat_id = %s", (chat_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Eroare la ștergerea chat-ului: {e}")

# --- RUTE FLASK ---
@app.route('/')
def home():
    """Pagină principală pentru a verifica dacă botul rulează."""
    return "Bot is running!"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    """Gestionează mesajele primite de la utilizatori (prin webhook Telegram)."""
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
            
        payload = { "chat_id": chat_id, "text": reply }
        requests.post(TELEGRAM_API_URL, json=payload)
    return "ok", 200

@app.route('/spam')
def spam():
    """Trimite un mesaj cu imagine și buton tuturor utilizatorilor activi, în mod ciclic."""
    global spam_counter

    if not MESAJE:
        return "Eroare: Niciun mesaj încărcat. Verifică fișierul messages.json.", 500
    
    # Selectează mesajul curent din ciclu
    mesaj_index = spam_counter % len(MESAJE)
    mesaj_obj = MESAJE[mesaj_index]
    
    # Extrage datele din obiectul JSON
    mesaj_text = mesaj_obj['text']
    cale_imagine = mesaj_obj['imagine']
    button_text = mesaj_obj.get("button_text", "Apasă aici")
    button_url = mesaj_obj.get("button_url", "https://www.google.com/")
    
    # Incrementăm contorul pentru următoarea cerere
    spam_counter += 1
    
    chats = load_chats()

    if not os.path.exists(cale_imagine):
        return f"Eroare: Fișierul imagine nu a fost găsit la calea {cale_imagine}", 500

    # Construim butonul inline
    reply_markup = { "inline_keyboard": [[ { "text": button_text, "url": button_url } ]] }

    # Trimitem mesajul fiecărui utilizator din baza de date
    for chat_id in chats:
        payload = {
            "chat_id": chat_id,
            "caption": mesaj_text,
            "reply_markup": json.dumps(reply_markup)
        }
        with open(cale_imagine, 'rb') as photo_file:
            files = {'photo': photo_file}
            requests.post(TELEGRAM_API_URL_PHOTO, data=payload, files=files)
            
    return f"Mesaj trimis către {len(chats)} utilizatori.", 200

if __name__ == "__main__":
    # Inițializează tabelul în baza de date la pornirea aplicației
    init_db() 
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

