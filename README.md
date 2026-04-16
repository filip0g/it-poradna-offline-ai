
 IT Poradna AI (Závěrečný projekt)
Autor: Filip Turoň (IT4A)

Tohle je moje webová aplikace, která slouží jako chytrý IT helpdesk. Uživatel se zeptá na cokoliv z IT (sítě, kód, hardware) a AI mu odpoví. Aplikace je "obojživelník" – umí běžet buď u mě v notebooku úplně offline, nebo na učitelově cloudu.

 Co to vlastně dělá?
Odpovídá na IT dotazy: AI je nastavená tak, aby byla striktní. Když se jí někdo zeptá na recept na svíčkovou, neodpoví a napíše že je IT asistent.

Má vlastní databázi: Používám Redis. Aplikace si do něj ukládá, kolik dotazů už celkově zodpověděla (zápis) a pak to číslo ukazuje uživatelům na webu (čtení).

Chytrá výhybka: Kód v Pythonu sám pozná, kde zrovna běží.

Na cloudu používá učitelovu velkou AI (Gemma 3).

U mě v noťasu používá lokální AI (Qwen 2.5 přes Ollamu).

Funguje i bez internetu: V mé lokální verzi (VirtualBox) mám nastavené vlastní DHCP a DNS, takže se na web dostanu přes doménu turonfilip.skola.test, i když vypnu kabel od netu.

 Technologie, co jsem použil
Backend: Python + Flask (obsluhuje web a kecá s AI).

Frontend: HTML + CSS (Dark Mode) + JavaScript (posílá dotazy bez načítání stránky).

Databáze: Redis (samostatný kontejner pro ukládání statistik).

Kontejnery: Docker & Docker Compose (celý projekt se spustí jedním příkazem).

Sítě (Varianta B): ISC-DHCP-Server a BIND9 (DNS) pro ten offline režim.

 Co je v jakém souboru?
app.py – Hlavní kód v Pythonu. Je tam ta logika výhybky a připojení k databázi.

templates/index.html – Vzhled webu. Používám tam knihovnu marked.js, aby odpovědi od AI (kód a nadpisy) vypadaly hezky.

compose.yml – Konfigurace pro učitelův server (Varianta A). Spouští web a Redis.

docker-lokalni.yml – Moje původní nastavení pro offline běh s Ollamou.

Dockerfile – Návod, jak se má moje aplikace "upéct" do kontejneru.

requirements.txt – Seznam knihoven (Flask, requests, redis), které se musí nainstalovat.

 Jak to spustit?
Varianta A (Učitelův Cloud)
Tady stačí mít soubory na GitHubu. Portál si sám načte compose.yml, postaví aplikaci a připojí k ní Redis.

URL: https://filip-0g.kurim.ithope.eu (nebo tvoje doména)

Status: https://filip-0g.kurim.ithope.eu/status

Varianta B (Lokálně v noťasu / Offline)
Pustit Ubuntu Server ve VirtualBoxu (vnitřní síť).

Skočit do složky projektu: cd ~/it-poradna

Spustit Docker: sudo docker compose -f docker-lokalni.yml up -d

Na klientovi (Ubuntu/Windows) v prohlížeči zadat: http://turonfilip.skola.test:8081

 Síťové info (pro moji offline verzi)
IP Serveru: 10.10.10.1 / 24

DHCP Rozsah: 10.10.10.100 - 10.10.10.200

DNS Záznam: turonfilip.skola.test -> 10.10.10.1

Port aplikace: 8081

 Kontrolní body (Endpoints)
Moje aplikace má povinné cesty pro kontrolu stavu:

/ping -> odpoví "pong" (test, jestli web žije).

/status -> vrátí JSON s mým jménem a časem serveru.
