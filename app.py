import requests
import time
import threading
import json
import os
from flask import Flask, request

TOKEN = "8398943601:AAEzb3okZXiN6QRVgfsYk3e6dMCB-ybBlcY"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
CHATS_FILE = "active_chats.json"

app = Flask(__name__)

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_chats(chats):
    with open(CHATS_FILE, "w") as f:
        json.dump(list(chats), f)

active_chats = load_chats()

def process_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    if text.lower() == "/start":
        active_chats.add(chat_id)
        save_chats(active_chats)
        reply = "Ai pornit notificările automate! Vei primi mesaje la fiecare minut."
    else:
        reply = f"You said: {text}"
    payload = {
        "chat_id": chat_id,
        "text": reply
    }
    requests.post(TELEGRAM_API_URL, json=payload)

def send_auto_messages():
    msg_count = 1
    while True:
        chats = load_chats()
        for chat_id in chats:
            payload = {
                "chat_id": chat_id,
                "text": f"Automat mesaj {msg_count}"
            }
            requests.post(TELEGRAM_API_URL, json=payload)
        msg_count += 1
        time.sleep(5)

def delete_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
    resp = requests.get(url)
    print("Webhook delete response:", resp.text)

@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data:
        process_message(data["message"])
    return "ok", 200

def run_local_bot():
    delete_webhook()
    threading.Thread(target=send_auto_messages, daemon=True).start()
    TELEGRAM_GET_UPDATES_URL = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    last_update_id = None
    print("Local bot polling started.")
    while True:
        params = {"timeout": 5}
        if last_update_id:
            params["offset"] = last_update_id + 1
        try:
            resp = requests.get(TELEGRAM_GET_UPDATES_URL, params=params)
            if resp.status_code == 200:
                updates = resp.json().get("result", [])
                for update in updates:
                    if "message" in update:
                        process_message(update["message"])
                    last_update_id = update["update_id"]
            else:
                print("Error:", resp.text)
        except Exception as e:
            print("Exception:", e)
        time.sleep(1)

if __name__ == "__main__":
    import sys
    threading.Thread(target=send_auto_messages, daemon=True).start()
    if len(sys.argv) > 1 and sys.argv[1] == "local":
        run_local_bot()
    else:
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))