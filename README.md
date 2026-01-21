<div align="center">
</div>

# Discord Ticket Bot (Python)

Ein professionelles Ticket-System für Discord mit Kategorien für Support, Reports, Entbannungsanträge, Bewerbungen und Administration. Der Bot bietet Schutz vor Spam, detailliertes Logging und eine Verifizierungs-Pflicht.

## ✨ Funktionen

### 🎫 Ticket-Verwaltung & Limits
* **Kategorien:** Dedizierte Kanäle für Support, Report, Unban, Bewerbung und Administration.
* **Ticket-Limit:** Nutzer können **maximal 2 Tickets gleichzeitig** geöffnet haben.
* **Verifizierungs-Pflicht:** Tickets können nur von Usern erstellt werden, die die verifizierte Rolle besitzen.
* **Management:** User zu Tickets hinzufügen, entfernen oder Tickets von Teammitglieder beanspruchen lassen.

### 🛡️ Sicherheit & Logging
* **Closing Logs:** Beim Schließen eines Tickets wird ein detaillierter Log in den konfigurierten Log-Kanal gesendet.
* **Blacklist:** Integriertes System zum Blockieren und Entblocken von Usern (User können dann keine Tickets mehr öffnen).

---

## 🚀 Schnellstart

**Voraussetzungen:** Python 3.8+ sowie die Bibliothek `discord.py`.

1. **Abhängigkeiten installieren:**
   `pip install discord.py aiohttp`

2. **Konfiguration:**
   Öffne die Datei `bot.py` und trage deine Daten in die entsprechenden Variablen ein (siehe Abschnitt **Code-Anpassungen**).

3. **Bot starten:**
   `python bot.py`

---

## 🛠️ Code-Anpassungen

Passe die folgenden Variablen direkt in deiner `bot.py` Datei an:

### Basis-Setup & Branding
```python
BOT_TOKEN = 'Dein_Token'
LOG_CHANNEL_ID = 0
ADMIN_ROLE_ID = 0
OWNER_ROLE_ID = 0
VERIFIED_ROLE_ID = 0  # Erforderliche Rolle zum Erstellen von Tickets

BANNER_URL = ""
LOGO_URL = ""

CATEGORY_ID_MAP = {
    "Support": ,
    "Report": ,
    "Unban": ,
    "Bewerbung": ,
    "Administration": ,
}

ROLE_ID_MAP = {
    "Support": ,
    "Report": ,
    "Unban": ,
    "Bewerbung": ,
    "Administration": ,
}

BEANSPRUCHUNGS_ROLE_ID = {
    "Support": ,
    "Report": ,
    "Unban": ,
    "Bewerbung": ,
    "Administration": ,
}
