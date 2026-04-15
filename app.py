# =====================================================================
# 1. IMPORTY - NATAHÁNÍ NÁSTROJŮ, KTERÉ KÓD POTŘEBUJE
# =====================================================================
from flask import Flask, request, jsonify, render_template  # Flask je náš webový server. Řeší příchozí dotazy a posílá HTML.
import requests  # Knihovna requests umí posílat data po internetu (tzv. HTTP požadavky na AI).
import datetime  # Nástroj pro práci s časem (používáme to dole v /status endpointu).
import os        # Nástroj pro čtení systémových proměnných (např. abychom zjistili tajné klíče nebo port).
import redis     # Knihovna pro komunikaci s naší novou databází.

# =====================================================================
# 2. ZALOŽENÍ APLIKACE A DATABÁZE
# =====================================================================
# Vytvoříme samotnou aplikaci Flask. "__name__" jí říká, kde přesně se nachází.
app = Flask(__name__)

# Pokusíme se připojit k Redis databázi (Varianta A).
# Používáme try-except (Zkus-Chyť). Kdyby databáze náhodou spadla, aplikace nespadne s ní,
# ale prostě si do proměnné 'db' uloží None (nic) a pojede dál bez ní.
try:
    # Připojíme se na kontejner jménem 'redis' na standardním portu 6379.
    db = redis.Redis(host='redis', port=6379, decode_responses=True)
    db.ping() # Pošleme rychlý "ping", abychom si ověřili, že spojení reálně funguje.
except:
    db = None

# =====================================================================
# 3. HLAVNÍ STRÁNKA (FRONTEND)
# =====================================================================
# @app.route určuje URL cestu. Když uživatel přijde na hlavní stránku ("/"),
# spustí se tato funkce a pošle mu náš grafický frontend (index.html).
@app.route('/')
def home():
    return render_template('index.html')

# =====================================================================
# 4. MOZEK APLIKACE - KOMUNIKACE S AI A DATABÁZÍ
# =====================================================================
# Endpoint "/ai" přijímá pouze metodu POST (uživatel nám posílá nějaká data/dotaz).
@app.route('/ai', methods=['POST'])
def ask_ai():
    data = request.json                  # Přečteme si data, co nám poslal frontend (JavaScript) ve formátu JSON.
    user_prompt = data.get('prompt', '') # Vytáhneme z nich ten samotný textový dotaz od uživatele.
    
    # SYSTEM PROMPT: Tohle je tvrdý mantinel pro AI. Říkáme jí, kým je.
    # Tím zamezíme tomu, aby odpovídala na otázky mimo téma IT.
    system_instruction = (
        "Jsi striktní IT specialista. "
        "Tvým úkolem je odpovídat POUZE na technické otázky z oboru IT... "
        "Odpovídej česky, stručně a odborně."
    )

    # Pokusíme se načíst klíče z učitelova serveru. 
    # os.environ se podívá do systému, jestli tam tyto proměnné existují.
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    
    # --- PRÁCE S DATABÁZÍ (SPLNĚNÍ VARIANTY A) ---
    query_count = "Neznámý"
    if db:  # Pokud se nám nahoře podařilo připojit k databázi...
        try:
            # db.incr udělá dvě věci naráz: 
            # 1. ZÁPIS: Přičte číslo 1 k hodnotě 'total_queries'.
            # 2. ČTENÍ: Rovnou to nové číslo vrátí a my si ho uložíme do query_count.
            query_count = db.incr('total_queries')
        except:
            pass

    # =====================================================================
    # 5. CHYTRÁ VÝHYBKA (CLOUD VS. LOKÁL)
    # =====================================================================
    try:
        # Pokud jsme našli učitelovy klíče, jsme na CLOUDU a použijeme jeho AI.
        if api_key and base_url:
            url = "https://kurim.ithope.eu/v1/chat/completions" # Učitelova API adresa
            
            # Hlavička požadavku - tady se prokazujeme tajným klíčem (Authorization).
            headers = {
                "Authorization": f"Bearer {api_key}", 
                "Content-Type": "application/json"
            }
            
            # Tělo požadavku (payload) ve formátu, který vyžaduje OpenAI API.
            payload = {
                "model": "gemma3:27b", # Požadovaný velký model
                "messages": [
                    {"role": "system", "content": system_instruction}, # Naše ochrana
                    {"role": "user", "content": user_prompt}           # Dotaz od uživatele
                ],
                "temperature": 0.2, # Určuje kreativitu AI (0.2 = drží se faktů, nevymýšlí si).
                "max_tokens": 150   # Omezení délky odpovědi.
            }
            
            # Odešleme požadavek. verify=False používáme k ignorování chyb certifikátů na proxy serveru.
            response = requests.post(url, headers=headers, json=payload, verify=False)
            
            # Pokud server vrátil kód 200 (Vše OK), složitě vybalíme text odpovědi ze struktury JSONu.
            if response.status_code == 200:
                answer = response.json().get('choices', [{}])[0].get('message', {}).get('content', 'Chyba AI')
                # Pošleme frontendu odpověď od AI a zároveň číslo z naší Redis databáze.
                return jsonify({"answer": answer, "db_count": query_count})
            else:
                return jsonify({"error": f"API error: {response.text}"}), response.status_code

        # Pokud jsme klíče nenašli, jedeme v OFFLINE režimu přes náš VirtualBox.
        else:
            url = 'http://ollama:11434/api/generate' # Lokální adresa kontejneru Ollama
            
            # Ollama používá jiný formát tělíčka (payload) než OpenAI, takže ho musíme složit jinak.
            payload = {
                "model": "qwen2.5:3b",
                "prompt": f"{system_instruction} Uživatel: {user_prompt}",
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 150}
            }
            
            response = requests.post(url, json=payload, verify=False)
            if response.status_code == 200:
                # Obalíme odpověď od lokální AI a přidáme číslo z databáze a pošleme zpět.
                return jsonify({"answer": response.json().get('response', 'Chyba AI'), "db_count": query_count})
            else:
                return jsonify({"error": f"Ollama error: {response.text}"}), response.status_code

    # Pokud spojení s AI vůbec neklapne (např. spadne internet), chytíme to zde,
    # aby nehavaroval celý náš server (Chyba 500 = Internal Server Error).
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================================
# 6. POVINNÉ ENDPOINTY (Dle PDF zadání pro Variantu A)
# =====================================================================
# Učitelův testovací robot si pípne na cestu "/ping", aby zjistil, jestli appka žije.
@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

# Další povinný endpoint. Vrací informace o stavu, čase a autorovi ve formátu JSON.
@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "running",
        "time": datetime.datetime.now().isoformat(), # Získáme aktuální systémový čas.
        "author": "Filip Turon"
    }), 200

# =====================================================================
# 7. SPUŠTĚNÍ SERVERU
# =====================================================================
# Tento kód se spustí jen tehdy, když tento soubor přímo zapneme příkazem "python app.py".
if __name__ == '__main__':
    # Dynamicky si vezmeme port, který nám přidělil cloud. Kdyby tam žádný nebyl (lokál), použijeme 8081.
    port = int(os.environ.get("PORT", 8081))
    # Spustíme Flask server. host='0.0.0.0' znamená, že server bude poslouchat
    # provoz ze všech sítí a rozhraní (aby byl dostupný zvenku z internetu).
    app.run(host='0.0.0.0', port=port)
