IT Poradna s lokální AI (Offline Mini-helpdesk)
Autor: Filip Turoň IT4A

1. Co projekt dělá
Projekt funguje jako plně kontejnerizovaná webová aplikace, která komunikuje s lokálním modelem umělé inteligence (LLM). Uživatel napíše technický dotaz do webového rozhraní a systém mu prostřednictvím AI vygeneruje přesnou odpověď. Projekt navíc obsahuje vlastní DHCP a DNS server, takže funguje jako samostatný ostrov nezávislý na internetu.

2. K čemu je určený
Služba slouží jako "Mini-helpdesk" pro spolužáky v izolované školní síti. Je navržena tak, aby bezpečně a rychle odpovídala na dotazy z oblasti IT (např. vysvětlení síťových pojmů), aniž by data opustila lokální síť. Díky "System promptu" je AI omezena pouze na IT témata.

3. Na jakých technologiích je postavený
Backend: Python 3 + framework Flask

AI Engine: Ollama + lokální model Qwen 2.5:3B (běžící na CPU)

Kontejnerizace: Docker & Docker Compose

Síťové služby (virtuální server): ISC-DHCP-Server (přidělování IP), BIND9 (překlad domény)

4. Síťová konfigurace a Porty
IP adresa a maska serveru: 10.10.10.1 / 24

DHCP (isc-dhcp-server): Rozsah 10.10.10.100 - 10.10.10.200 (Option 006 DNS = 10.10.10.1)

DNS (bind9): Zóna skola.test, A-záznam turonfilip.skola.test -> 10.10.10.1

Port aplikace: 8081

Port LLM API: 11434 (interní Docker síť)

Firewall (UFW): Povolen port 8081/tcp pro přístup z LAN.

5. Jak se spouští
Projekt je plně zautomatizován pomocí Docker Compose. Pro spuštění stačí mít nainstalovaný Docker a provést následující kroky:

Naklonovat nebo stáhnout tento repozitář.

V terminálu přejít do složky s projektem. = cd ~/it-poradna

Spustit příkaz: sudo docker-compose up -d

Aplikace bude po chvíli dostupná ve webovém prohlížeči. V izolované síti zadejte: http://turonfilip.skola.test:8081

Důležité příkazy pro kontrolu stavu:

· Běží kontejnery s webem a AI? -> sudo docker ps

· Běží přidělování adres (DHCP)? -> sudo systemctl status isc-dhcp-server

· Běží překlad domén (DNS)? -> sudo systemctl status bind9

Cesty k nejdůležitějším konfiguračním souborům:

· Kód aplikace: ~/it-poradna/app.py

· Nastavení kontejnerů: ~/it-poradna/docker-compose.yml

· Nastavení DHCP rozsahu: /etc/dhcp/dhcpd.conf

· Konfigurace DNS zóny: /etc/bind/named.conf.local

· Záznamy DNS (IP k doméně): /etc/bind/db.skola.test

· Pevná IP Serveru: /etc/netplan/00-installer-config.yaml

Kontrolní endpointy:

/ping - Vrací text "pong" pro ověření chodu aplikace.

/status - Vrací JSON s informacemi o stavu.

6. Ukázkový cURL na LLM (Ollama API)
Pro přímé ověření funkčnosti AI modelu bez webového rozhraní lze z terminálu serveru zavolat:
curl -X POST http://localhost:11434/api/generate -d '{"model": "qwen2.5:3b", "prompt": "Co je to DHCP?", "stream": false}'
