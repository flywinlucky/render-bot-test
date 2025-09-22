from flask import Flask, request
import requests
import os
import sqlite3
import random

app = Flask(__name__)

# --- CONFIGURARE ---
TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
DB_FILE = "active_chats.db"

# --- LISTA DE MESAJE ---
# Lista cu 10 mesaje diferite care vor fi trimise utilizatorilor.
MESAJE = [
    "Salut! Acesta este un mesaj automat de la botul tău prietenos.",
    "Bună! Sper că ai o zi productivă și plină de succes.",
    "Notificare: A trecut încă un minut. Timpul zboară când te distrezi!",
    "Acesta este un memento automat pentru a-ți aminti să faci o pauză.",
    "Ce mai faci? Botul tău se gândește la tine.",
    "Ping! Doar verificam dacă ești pe fază. O zi bună!",
    "O mică notificare pentru a-ți aduce un zâmbet pe buze.",
    "Mesaj automat: Sistemele funcționează în parametri normali.",
    "Știai că roboții nu dorm niciodată? Sunt mereu aici pentru tine!",
    "Acesta este ultimul mesaj unic din ciclu. Următorul o va lua de la capăt!"
]

# Amestecăm lista o singură dată la pornirea aplicației.
# Astfel, ordinea va fi aleatorie, dar se va păstra pe parcursul unui ciclu.
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
    """Trimite un mesaj tuturor utilizatorilor activi, în mod ciclic."""
    global spam_counter
    init_db()
    
    # Selectează un mesaj din lista amestecată folosind contorul global
    # Operatorul modulo (%) asigură că indexul rămâne în limitele listei.
    mesaj_index = spam_counter % len(MESAJE)
    mesaj_de_trimis = MESAJE[mesaj_index]
    
    # Incrementăm contorul pentru următoarea cerere
    spam_counter += 1
    
    chats = load_chats()
    for chat_id in chats:
        payload = {
            "chat_id": chat_id,
            "text": mesaj_de_trimis
        }
        requests.post(TELEGRAM_API_URL, json=payload)
        
    return f"Sent message '{mesaj_de_trimis}' to {len(chats)} users.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

