from flask import Flask, request
import requests
import os
import random
import json
import psycopg2
import sys

app = Flask(__name__)

# --- CONFIGURARE ȘI VERIFICARE ---
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificăm dacă variabilele esențiale sunt setate
if not TOKEN or not DATABASE_URL:
    print("EROARE CRITICĂ: Asigură-te că variabilele de mediu BOT_TOKEN și DATABASE_URL sunt setate.")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
TELEGRAM_API_URL_PHOTO = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"


# --- ÎNCĂRCARE MESAJE DIN FIȘIERUL JSON ---
def load_messages():
    """Încarcă mesajele din fișierul messages.json."""
    try:
        with open('messages.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"AVERTISMENT: Nu s-a putut încărca 'messages.json'. Eroare: {e}")
        return []

MESAJE = load_messages()
if MESAJE:
    random.shuffle(MESAJE)
spam_counter = 0


# --- FUNCȚII BAZĂ DE DATE (CU CONEXIUNI ROBUSTE) ---
def get_db_connection():
    """Stabilește o conexiune cu baza de date PostgreSQL. Returnează None în caz de eroare."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except psycopg2.OperationalError as e:
        print(f"EROARE BAZĂ DE DATE: Conexiunea a eșuat. Detalii: {e}")
        return None

def init_db():
    """Initializează tabelul în baza de date. Se execută o singură dată la pornirea aplicației."""
    conn = get_db_connection()
    if conn is None:
        print("EROARE BAZĂ DE DATE: Inițializarea a eșuat, conexiune invalidă.")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id BIGINT PRIMARY KEY
                )
            """)
        conn.commit()
        print("BAZĂ DE DATE: Conexiune reușită. Tabelul 'chats' este pregătit.")
    except Exception as e:
        print(f"EROARE BAZĂ DE DATE: Crearea tabelului a eșuat. Detalii: {e}")
    finally:
        conn.close()

def load_chats():
    """Încarcă toate ID-urile de chat din baza de date."""
    chats = set()
    conn = get_db_connection()
    if conn is None: return chats
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT chat_id FROM chats")
            chats = set(row[0] for row in cur.fetchall())
        print(f"BAZĂ DE DATE: {len(chats)} utilizatori încărcați.")
    except Exception as e:
        print(f"EROARE BAZĂ DE DATE: Încărcarea chat-urilor a eșuat. Detalii: {e}")
    finally:
        conn.close()
    return chats

def add_chat(chat_id):
    """Adaugă un nou ID de chat în baza de date."""
    conn = get_db_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO chats (chat_id) VALUES (%s) ON CONFLICT (chat_id) DO NOTHING", (chat_id,))
        conn.commit()
        print(f"BAZĂ DE DATE: Utilizator {chat_id} adăugat.")
    except Exception as e:
        print(f"EROARE BAZĂ DE DATE: Adăugarea chat-ului {chat_id} a eșuat. Detalii: {e}")
    finally:
        conn.close()

def remove_chat(chat_id):
    """Șterge un ID de chat din baza de date."""
    conn = get_db_connection()
    if conn is None: return
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chats WHERE chat_id = %s", (chat_id,))
        conn.commit()
        print(f"BAZĂ DE DATE: Utilizator {chat_id} șters.")
    except Exception as e:
        print(f"EROARE BAZĂ DE DATE: Ștergerea chat-ului {chat_id} a eșuat. Detalii: {e}")
    finally:
        conn.close()

# --- RUTE FLASK (Fără modificări aici) ---
@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
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
            reply = "Comandă necunoscută. Folosește /start sau /stop."
            
        requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": reply})
    return "ok", 200

@app.route('/spam')
def spam():
    global spam_counter
    if not MESAJE:
        return "Eroare: Niciun mesaj încărcat.", 500
    
    chats = load_chats()
    if not chats:
        return "Niciun utilizator în baza de date. Trimite /start pentru a te abona.", 200
        
    mesaj_obj = MESAJE[spam_counter % len(MESAJE)]
    spam_counter += 1
    
    cale_imagine = mesaj_obj['imagine']
    if not os.path.exists(cale_imagine):
        return f"Eroare: Fișierul imagine '{cale_imagine}' nu a fost găsit.", 500

    reply_markup = {"inline_keyboard": [[{"text": mesaj_obj.get("button_text", "Apasă"), "url": mesaj_obj.get("button_url", "https://google.com")}]]}

    for chat_id in chats:
        payload = {
            "chat_id": chat_id,
            "caption": mesaj_obj['text'],
            "reply_markup": json.dumps(reply_markup)
        }
        try:
            with open(cale_imagine, 'rb') as photo_file:
                files = {'photo': photo_file}
                requests.post(TELEGRAM_API_URL_PHOTO, data=payload, files=files)
        except Exception as e:
            print(f"EROARE la trimiterea mesajului către {chat_id}. Detalii: {e}")
            
    return f"Mesaj trimis cu succes către {len(chats)} utilizatori.", 200

# --- INIȚIALIZARE ---
# Se execută o singură dată când Render pornește aplicația
init_db()

if __name__ == "__main__":
    # Acest bloc este folosit doar pentru testare locală
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

