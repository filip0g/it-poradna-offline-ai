from flask import Flask, request, jsonify, render_template
import requests
import datetime
import os  # PRIDANO: pro cteni ucitelskych promennych a portu

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ai', methods=['POST'])
def ask_ai():
    data = request.json
    user_prompt = data.get('prompt', '')
    
    # --- TOTO JE TO HLIDANI TEMATU ---
    system_instruction = (
        "Jsi striktní IT specialista. "
        "Tvým úkolem je odpovídat POUZE na technické otázky z oboru IT "
        "(počítače, sítě, programování, hardware, bezpečnost). "
        "Pokud se uživatel zeptá na cokoliv jiného (např. počasí, vaření, jak se máš, vtipy), "
        "odmítni odpovědět touto větou: 'Jsem IT asistent, na netechnické dotazy neodpovídám.' "
        "Odpovídej česky, stručně a odborně."
    )

    # Nacteni tajnych klicu od ucitele (pokud existuji)
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")

    try:
        # ---------------------------------------------------------
        # VÝHYBKA 1: REŽIM UČITEL (Jsme nasazeni na jeho serveru)
        # ---------------------------------------------------------
        if api_key and base_url:
            # Ujistime se, ze adresa konci spravne pro chat
            if not base_url.endswith("/chat/completions"):
                url = f"{base_url}/chat/completions"
            else:
                url = base_url

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gemma3:27b",  # Uctiteluv obri model
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 150
            }
            
            response = requests.post(url, headers=headers, json=payload, verify=False)
            if response.status_code == 200:
                answer = response.json().get('choices', [{}])[0].get('message', {}).get('content', 'Chyba AI')
                return jsonify({"answer": answer})
            else:
                return jsonify({"error": f"OpenAI API error: {response.text}"}), response.status_code

        # ---------------------------------------------------------
        # VÝHYBKA 2: REŽIM OFFLINE (Jsme u tebe doma / ve VirtualBoxu)
        # ---------------------------------------------------------
        else:
            url = 'http://ollama:11434/api/generate'
            
            payload = {
                "model": "qwen2.5:3b",   # Tady necham 3b (klidne zmen na 0.5b pro noťas)
                "prompt": f"{system_instruction} Uživatel: {user_prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 150
                }
            }

            response = requests.post(url, json=payload, verify=False)
            if response.status_code == 200:
                return jsonify({"answer": response.json().get('response', 'Chyba AI')})
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
    # ZMENA: Port se ted bere automaticky od ucitele. Kdyz tam neni (jsi doma), pouzije 8081.
    port = int(os.environ.get("PORT", 8081))
    app.run(host='0.0.0.0', port=port)
