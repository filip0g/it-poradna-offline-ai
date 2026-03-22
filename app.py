from flask import Flask, request, jsonify, render_template
import requests
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ai', methods=['POST'])
def ask_ai():
    data = request.json
    user_prompt = data.get('prompt', '')
    
    # Tady je adresa AI (v siti 'mojesit' se jmenuje 'ollama')
    url = 'http://ollama:11434/api/generate'
    
    # --- TOTO JE TO HLIDANI TEMATU ---
    system_instruction = (
        "Jsi striktní IT specialista. "
        "Tvým úkolem je odpovídat POUZE na technické otázky z oboru IT "
        "(počítače, sítě, programování, hardware, bezpečnost). "
        "Pokud se uživatel zeptá na cokoliv jiného (např. počasí, vaření, jak se máš, vtipy), "
        "odmítni odpovědět touto větou: 'Jsem IT asistent, na netechnické dotazy neodpovídám.' "
        "Odpovídej česky, stručně a odborně."
    )
    
    payload = {
        "model": "qwen2.5:3b",   # ZMENA: Pouzivame novy model Qwen
        "prompt": f"{system_instruction} Uživatel: {user_prompt}",
        "stream": False,
        "options": {
            "temperature": 0.2,  # Nizka teplota = bud presny, nevymyslej si
            "num_predict": 150   # Povolime mu delsi odpoved, je chytrejsi
        }
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return jsonify({"answer": response.json().get('response', 'Chyba AI')})
        else:
            return jsonify({"error": f"Ollama error: {response.text}"}), 500
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
        "author": "Student"
   }), 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
