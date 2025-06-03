# Gemini Telegram Bot

Ein einfach zu installierender Telegram‑Bot für den Raspberry Pi, der über die
Google‑Gemini‑API Antworten generiert. Der Bot merkt sich pro Benutzer den
Gesprächsverlauf und zeigt Antworten stückweise an.

## Funktionen

- Chat‑Modell: `gemini-2.5-flash-preview-05-20` (via `GEMINI_MODEL` anpassbar)
- Streaming‑Antworten für schnelle Rückmeldungen
- Mehrere Nachrichten pro Unterhaltung
- Nutzbar in privaten Chats oder Gruppen

## Voraussetzungen

- Raspberry Pi mit aktuellem Raspberry Pi OS oder vergleichbarer Linux‑
  Distribution
- Python **3.12.10** oder neuer (empfohlen)
- Ein Telegram‑Bot‑Token von [BotFather](https://t.me/BotFather)
- Ein Gemini‑API‑Key aus [Google AI Studio](https://makersuite.google.com/app/apikey)
- Git zum Klonen des Projekts

## Installation Schritt für Schritt

### 1. System aktualisieren und Pakete installieren

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git
```

### 2. Quellcode herunterladen

```bash
git clone https://github.com/immunizedcarbon/Gemini-Telegram-Bot.git
cd Gemini-Telegram-Bot
```

### 3. Virtuelle Umgebung einrichten

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Python-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 5. Zugriffsdaten und Modell hinterlegen

1. Bei [BotFather](https://t.me/BotFather) einen neuen Bot anlegen und das Token kopieren.
2. In [Google AI Studio](https://makersuite.google.com/app/apikey) einen Gemini‑API‑Key erzeugen.
3. Im Projektverzeichnis eine Datei `.env` mit folgendem Inhalt anlegen:

```env
TELEGRAM_BOT_API_KEY=<DEIN_TELEGRAM_TOKEN>
GEMINI_API_KEYS=<DEIN_GEMINI_KEY>
GEMINI_MODEL=gemini-2.5-flash-preview-05-20
AUTHORIZED_USER_IDS=12345,67890
```
`AUTHORIZED_USER_IDS` ist eine kommaseparierte Liste der Telegram-IDs, die den Bot nutzen dürfen. Das Modell kann jederzeit durch Anpassen von `GEMINI_MODEL` geändert werden. Speichern und die Datei schließen.

### 6. Bot starten

Aktivierte virtuelle Umgebung vorausgesetzt:

```bash
python main.py
```

Im Terminal sollte nun `Starting Gemini_Telegram_Bot.` erscheinen. Der Bot ist
jetzt einsatzbereit.

## Automatischer Start per systemd (optional)

Für einen dauerhaften Betrieb kann ein systemd‑Service eingerichtet werden:

```bash
sudo nano /etc/systemd/system/gemini-bot.service
```

Mit folgendem Inhalt (Pfad gegebenenfalls anpassen):

```
[Unit]
Description=Gemini Telegram Bot
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/Gemini-Telegram-Bot
EnvironmentFile=/home/pi/Gemini-Telegram-Bot/.env
ExecStart=/home/pi/Gemini-Telegram-Bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Danach:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gemini-bot.service
sudo systemctl start gemini-bot.service
```

Damit läuft der Bot automatisch nach jedem Neustart.

## Docker-Variante

Ist Docker installiert, lässt sich der Bot auch in einem Container betreiben.

1. Image bauen:

   ```bash
   docker build -t gemini-bot .
   ```

2. Eine `.env`‑Datei für Docker erstellen (z.B. im selben Ordner) und die
   Zugangsdaten sowie das Modell eintragen:

   ```env
    TELEGRAM_BOT_API_KEY=<DEIN_TELEGRAM_TOKEN>
    GEMINI_API_KEYS=<DEIN_GEMINI_KEY>
    GEMINI_MODEL=gemini-2.5-flash-preview-05-20
    AUTHORIZED_USER_IDS=12345,67890
    ```
    # AUTHORIZED_USER_IDS ist eine kommaseparierte Liste der Telegram-IDs,
    # die den Bot nutzen dürfen


3. Container starten:

   ```bash
   docker run -d --restart=unless-stopped \
     --env-file .env \
     gemini-bot
   ```

Alternativ kann Docker Compose verwendet werden. Beispiel `docker-compose.yml`:

```yaml
version: "3.8"
services:
  bot:
    build: .
    restart: unless-stopped
    environment:
      TELEGRAM_BOT_API_KEY: "${TELEGRAM_BOT_API_KEY}"
      GEMINI_API_KEYS: "${GEMINI_API_KEYS}"
      GEMINI_MODEL: "${GEMINI_MODEL}"
```

Mit `docker compose up -d` wird der Bot anschließend im Hintergrund gestartet.

## Modell aktualisieren

Google veröffentlicht regelmäßig neue Gemini‑Modelle. Um ein anderes Modell zu
nutzen, reicht es, den Namen in der `.env`‑Datei bei `GEMINI_MODEL` anzupassen
und den Container beziehungsweise das Programm neu zu starten.

## Verwendung

- `/start` – Begrüßung
- `/gemini <Text>` – Frage an den Bot stellen
- `/clear` – bisherigen Verlauf löschen
- Unterhaltungen verfallen nach einer Stunde Inaktivität

Im Privatchat können Fragen auch direkt ohne Befehl gesendet werden.

## Lizenz

Dieses Projekt steht unter der [Apache‑2.0‑Lizenz](LICENSE).
