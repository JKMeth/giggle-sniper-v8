import requests, time, threading
from datetime import datetime
from flask import Flask, render_template_string
import os

app = Flask(__name__)

# Config (usa variables de Render)
API_KEY = os.getenv("API_KEY", "FBVZ6FPYH5AZPM8D6M4617C3N5RM2DXNFJ")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7461003760:AAEL2szEBQ96AtYgo1HlnqFjuQ_VIA33DG4")
CHAT_ID = os.getenv("CHAT_ID", "1063182207")

WALLETS = [
    {"address": "0x61032a6D4D8a18964F4D2885439437F260f58aD6", "name": "Wallet GIGGLE0"},
    {"address": "0xaf25627aC5a3ac2EFC3B18bc4FC4E4E650F803Dc", "name": "GIGGLE wallet"},
    {"address": "0xb95aef34715696bfb80b8df98d3ad75742eb4947", "name": "Trading bot"},
    {"address": "0x11cc110124b2ff755272c1fb8e1dae255bd1626c", "name": "MIJ 26C"},
    {"address": "0x87652e51ef615572c9914cf38c49b7aaad8e61ce", "name": "MIJ 61CE"}
]

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
BSCSCAN_API = "https://api.bscscan.com/api"
BNB_PRICE = 600

dashboard_data = {"last_update": "", "transactions": [], "bnb_price": BNB_PRICE}
last_seen = {w["address"]: 0 for w in WALLETS}

def send_telegram(msg):
    try:
        requests.post(TELEGRAM_API, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=8)
    except: pass

def get_txs(addr, action):
    try:
        params = {"module": "account", "action": action, "address": addr, "page": 1, "offset": 20, "sort": "desc", "apikey": API_KEY}
        r = requests.get(BSCSCAN_API, params=params, timeout=8)
        return r.json().get("result", [])
    except: return []

def monitor():
    send_telegram("GIGGLE SNIPER V8 INICIADO - 24/7")
    while True:
        try:
            for w in WALLETS:
                addr, name = w["address"], w["name"]
                txs = get_txs(addr, "txlist") + get_txs(addr, "tokentx")
                new = [t for t in txs if int(t.get("timeStamp",0)) > last_seen[addr]]
                if not new: continue
                for tx in new[:3]:
                    value = int(tx["value"]) / 1e18
                    usd = value * BNB_PRICE
                    if usd < 5: continue
                    msg = f"*TX NUEVA!*\nWallet: {name}\n{value:.6f} BNB (~${usd:.2f})\n[Ver](https://bscscan.com/tx/{tx['hash']})"
                    send_telegram(msg)
                    dashboard_data["transactions"].insert(0, {
                        "wallet": name, "amount": f"{value:.6f} BNB", "usd": f"${usd:.2f}",
                        "hash": tx["hash"], "time": datetime.fromtimestamp(int(tx["timeStamp"])).strftime("%H:%M")
                    })
                    if len(dashboard_data["transactions"]) > 50:
                        dashboard_data["transactions"] = dashboard_data["transactions"][:50]
                last_seen[addr] = max(int(t["timeStamp"]) for t in new)
            time.sleep(5)
        except: time.sleep(5)

HTML = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta http-equiv="refresh" content="15">
<title>GIGGLE SNIPER</title>
<style>body{background:#000;color:#0f0;font-family:Courier;padding:20px;text-align:center;}
h1{color:#0f0;}table{margin:auto;border:2px solid #0f0;background:#111;}
th,td{padding:10px;border-bottom:1px dashed #0f0;}a{color:#0ff;}</style></head><body>
<h1>GIGGLE SNIPER 24/7</h1>
<p>BNB: ${{ bnb_price }} | {{ last_update }}</p>
<table><tr><th>Wallet</th><th>Amount</th><th>USD</th><th>Time</th><th>TX</th></tr>
{% for t in transactions %}
<tr><td>{{ t.wallet }}</td><td>{{ t.amount }}</td><td>{{ t.usd }}</td><td>{{ t.time }}</td>
<td><a href="https://bscscan.com/tx/{{ t.hash }}" target="_blank">Ver</a></td></tr>
{% endfor %}</table></body></html>'''

@app.route('/')
def home():
    dashboard_data["last_update"] = datetime.now().strftime("%H:%M:%S")
    return render_template_string(HTML, **dashboard_data)

if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
