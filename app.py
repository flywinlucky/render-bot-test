from flask import Flask, request
import requests
import os
import sqlite3

app = Flask(__name__)

TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
DB_FILE = "active_chats.db"

def init_db():
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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT chat_id FROM chats")
    rows = c.fetchall()
    conn.close()
    return set(row[0] for row in rows)

def add_chat(chat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO chats (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def remove_chat(chat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

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
            reply = "Ai pornit notificările automate! Vei primi mesaje la fiecare minut."
        elif text.lower() == "/stop":
            remove_chat(chat_id)
            reply = "Ai oprit notificările automate!"
        else:
            reply = f"You said: {text}"
        payload = {
            "chat_id": chat_id,
            "text": reply
        }
        requests.post(TELEGRAM_API_URL, json=payload)
    return "ok", 200

@app.route('/spam')
def spam():
    msg_count = int(request.args.get("count", 1))
    chats = load_chats()
    for chat_id in chats:
        payload = {
            "chat_id": chat_id,
            "text": f"Automat mesaj {msg_count}"
        }
        requests.post(TELEGRAM_API_URL, json=payload)
    return f"Sent spam message {msg_count} to {len(chats)} users.", 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))