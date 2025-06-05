# Gemini Telegram Bot

Ein einfach zu installierender Telegram‑Bot für den Raspberry Pi, der über die
Google‑Gemini‑API Antworten generiert. Der Bot merkt sich pro Benutzer den
Gesprächsverlauf und zeigt Antworten stückweise an.
## Inhaltsverzeichnis

- [Funktionen](#funktionen)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Automatischer Start per systemd](#automatischer-start-per-systemd)
- [Docker-Variante](#docker-variante)
- [Modell aktualisieren](#modell-aktualisieren)
- [Verwendung](#verwendung)
- [Lizenz](#lizenz)


## Funktionen

- Chat‑Modell: `gemini-2.5-flash-preview-05-20` (via `GEMINI_MODEL` anpassbar)
- Streaming‑Antworten für schnelle Rückmeldungen
- Mehrere Nachrichten pro Unterhaltung
- Längere Antworten werden bei Bedarf automatisch in mehrere Nachrichten à
  höchstens 4096 Zeichen aufgeteilt, da Telegram keine längeren Nachrichten
  akzeptiert
- Verlauf bleibt gespeichert, bis `/clear` aufgerufen oder der Bot
  neu gestartet wird
- Bilder verstehen: Fotos oder Bilddateien können mit oder ohne Bildunterschrift gesendet werden. Die Caption wird als Prompt genutzt und das Ergebnis als Antwort ausgegeben.
- PDF-Dateien verstehen: Hochgeladene PDFs (bis 20 MB) lassen sich zusammenfassen oder durchsuchen. Eine optionale Beschriftung dient als Prompt.
- Audiodateien verstehen: Sprach- oder Musikdateien können analysiert oder transkribiert werden. Auch hier kann eine Caption als Frage genutzt werden.
- Webseiten-Inhalte analysieren: Enthält ein Prompt Links, werden diese über das URL-Context-Tool geladen.
- Web-Suche über Google für aktuelle Informationen (sofern Tools aktiviert)
- Nutzbar in privaten Chats oder Gruppen
- Überwacht Tokenverbrauch und API-Limits, um Free-Tier-Fehler zu vermeiden

## Voraussetzungen

- Raspberry Pi mit aktuellem Raspberry Pi OS oder vergleichbarer Linux‑
  Distribution
- Python **3.12.10** oder neuer (empfohlen)
- Ein Telegram‑Bot‑Token von [BotFather](https://t.me/BotFather)
- Ein Gemini‑API‑Key aus [Google AI Studio](https://makersuite.google.com/app/apikey)
- Git zum Klonen des Projekts

## Installation

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
GEMINI_API_KEY=<DEIN_GEMINI_KEY>
GEMINI_MODEL=gemini-2.5-flash-preview-05-20
AUTHORIZED_USER_IDS=12345,67890
# Optional limits for the free tier (defaults passend zum Modell)
GEMINI_RPM_LIMIT=10
GEMINI_TPM_LIMIT=250000
# Lifetime of inactive sessions in seconds (0 = unlimited)
SESSION_TTL=0
# Set to false if the chosen model does not support tools
ENABLE_TOOLS=true
# SYSTEM_INSTRUCTION ist optional. Mehrzeilige Texte mit \n trennen.
SYSTEM_INSTRUCTION="DU BIST DIE KI\\n1. ..."
```

`AUTHORIZED_USER_IDS` ist eine kommaseparierte Liste der Telegram-IDs, die den Bot nutzen dürfen. `SYSTEM_INSTRUCTION` legt die Systemvorgaben fest und kann weggelassen werden. Mehrzeilige Texte werden mit `\n` getrennt. Das Modell kann jederzeit durch Anpassen von `GEMINI_MODEL` geändert werden. Speichern und die Datei schließen. `ENABLE_TOOLS` aktiviert die Google-Suche und sollte auf `false` gesetzt werden, wenn das genutzte Modell keine Tools unterstützt.

### Sicherheitseinstellungen

Alle Safety-Filter der Gemini-API sind im Auslieferungszustand deaktiviert (`BLOCK_NONE`). Die entsprechenden
Einstellungen stehen in `config.py` und lassen sich bei Bedarf ändern.

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

Mit Docker lässt sich der Bot ohne weitere Abhängigkeiten ausführen.

1. **Image erstellen**

   ```bash
   docker build -t gemini-bot .
   ```

2. **Umgebungsvariablen definieren**

   Lege eine Datei `.env` im Projektordner an und trage dort die
   Zugangsdaten und optionalen Einstellungen ein:

   ```env
   TELEGRAM_BOT_API_KEY=<DEIN_TELEGRAM_TOKEN>
   GEMINI_API_KEY=<DEIN_GEMINI_KEY>
   GEMINI_MODEL=gemini-2.5-flash-preview-05-20
   AUTHORIZED_USER_IDS=12345,67890
   # optional
   SESSION_TTL=0
   ENABLE_TOOLS=true
   SYSTEM_INSTRUCTION="DU BIST DIE KI\n1. ..."
   ```

`AUTHORIZED_USER_IDS` ist eine kommaseparierte Liste der Telegram-IDs,
  die den Bot nutzen dürfen. `SYSTEM_INSTRUCTION` kann weggelassen werden.
`ENABLE_TOOLS` aktiviert die Google-Suche und sollte auf `false` gesetzt werden,
  wenn das genutzte Modell keine Tools unterstützt.

3. **Container starten**

   ```bash
   docker run -d --restart=unless-stopped \
     --env-file .env \
     --name gemini-bot \
     gemini-bot
   ```

   Alternativ lässt sich Docker Compose nutzen. Beispiel `docker-compose.yml`:

   ```yaml
   version: "3.8"
   services:
     bot:
       build: .
       restart: unless-stopped
       env_file: .env
   ```

   Anschließend startet der Bot mit:

   ```bash
   docker compose up -d
   ```


## Modell aktualisieren

Google veröffentlicht regelmäßig neue Gemini‑Modelle. Um ein anderes Modell zu
nutzen, reicht es, den Namen in der `.env`‑Datei bei `GEMINI_MODEL` anzupassen
und den Container beziehungsweise das Programm neu zu starten.

## Verwendung

- `/clear` – bisherigen Verlauf löschen
 - Unterhaltungen bleiben erhalten, bis sie per `/clear` entfernt oder der Bot
  neu gestartet wird

Im Privatchat können Fragen direkt ohne Befehl gesendet werden.
Fotos oder Bilddateien können ebenfalls geschickt werden. Eine angefügte
Beschriftung dient dabei als Prompt für Gemini.
PDF- oder Audiodateien funktionieren genauso: Datei senden und optional eine
Frage in der Caption stellen.
YouTube-Links funktionieren ähnlich: Link schicken und die Frage entweder
nachträglich oder gemeinsam mit dem Link stellen. Der Befehl `/youtube` ist
weiterhin nutzbar, erscheint aber nicht im Menü.
- Enthält eine Nachricht weitere Links, analysiert der Bot deren Inhalte automatisch und nutzt sie als Kontext.

### Hinweis zur Textformatierung

Telegram unterstützt nur eine eingeschränkte Form von Markdown. Um Fehler
bei der Darstellung zu vermeiden, kann über die Umgebungsvariable
`SYSTEM_INSTRUCTION` festgelegt werden, dass das Modell seine Antworten bereits
im passenden *MarkdownV2*-Format liefert. Ein Beispiel für die `.env`-Datei:

```env
SYSTEM_INSTRUCTION="Antworte immer in korrektem MarkdownV2 und entkomme alle Sonderzeichen, die Telegram benötigt."
```

Damit sind keine zusätzlichen Skripte nötig, um längere Texte sicher zu übermitteln.

## Lizenz

Dieses Projekt steht unter der [Apache‑2.0‑Lizenz](LICENSE).
