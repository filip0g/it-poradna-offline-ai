from flask import Flask, request, jsonify, render_template
import requests
import datetime
import os
import redis  # NOVÉ: Import databáze

app = Flask(__name__)

# NOVÉ: Připojení k databázi Redis (obaleno v try-except, aby to nespadlo, když DB zrovna neběží)
try:
    db = redis.Redis(host='redis', port=6379, decode_responses=True)
    db.ping() # Rychlý test spojení
except:
    db = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ai', methods=['POST'])
def ask_ai():
    data = request.json
    user_prompt = data.get('prompt', '')
    
    # Hlídání tématu
    system_instruction = (
        "Jsi striktní IT specialista. "
        "Tvým úkolem je odpovídat POUZE na technické otázky z oboru IT... "
        "Odpovídej česky, stručně a odborně."
    )

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    
    # NOVÉ: Zápis a čtení z databáze (počítadlo dotazů)
    query_count = "Neznámý"
    if db:
        try:
            # Zvýší počítadlo o 1 (ZÁPIS) a rovnou ho vrátí (ČTENÍ)
            query_count = db.incr('total_queries')
        except:
            pass

    try:
        if api_key and base_url:
            # REŽIM UČITEL (Cloud)
            url = "https://kurim.ithope.eu/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gemma3:27b",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2, "max_tokens": 150
            }
            response = requests.post(url, headers=headers, json=payload, verify=False)
            if response.status_code == 200:
                answer = response.json().get('choices', [{}])[0].get('message', {}).get('content', 'Chyba AI')
                # Vracíme i číslo z databáze
                return jsonify({"answer": answer, "db_count": query_count})
            else:
                return jsonify({"error": f"API error: {response.text}"}), response.status_code

        else:
            # REŽIM OFFLINE (Tvůj noťas)
            url = 'http://ollama:11434/api/generate'
            payload = {
                "model": "qwen2.5:3b",
                "prompt": f"{system_instruction} Uživatel: {user_prompt}",
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 150}
            }
            response = requests.post(url, json=payload, verify=False)
            if response.status_code == 200:
                return jsonify({"answer": response.json().get('response', 'Chyba AI'), "db_count": query_count})
            else:
                return jsonify({"error": f"Ollama error: {response.text}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "running",
        "time": datetime.datetime.now().isoformat(),
        "author": "Filip Turon"
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8081))
    app.run(host='0.0.0.0', port=port)
