# Whip Bestell Bot

Ein Telegram-Bot zur Verwaltung von Event-Ausgaben und Buchungen.

## Funktionen

### Für alle Nutzer
- Verfügbare Events anzeigen
- Ausgaben für Events eintragen
- Mit dem Bot in Gruppen interagieren, indem man ihn erwähnt (@botname)

### Für Admins
- Events erstellen
- Nur Summen anzeigen (ohne persönliche Details)
- Benachrichtigungen erhalten, wenn Nutzer Beträge eintragen

## Installation

1. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

2. Bot konfigurieren:
   - Stelle sicher, dass deine `.env` Datei folgendes enthält:
     ```
     TOKEN=dein_bot_token_hier
     ADMIN_IDS=deine_telegram_user_id,weitere_admin_id
     ```
   - Um deine Telegram User ID zu finden, schreibe [@userinfobot](https://t.me/userinfobot) auf Telegram

3. Bot starten:
```bash
python bot.py
```

## Befehle

### Für alle Nutzer
- `/start` - Bot starten und verfügbare Befehle anzeigen
- `/list_events` - Alle verfügbaren Events anzeigen
- `/enter_amount` - Deine Ausgaben für ein Event eintragen

### Für Admins
- `/create_event <event_name>` - Ein neues Event erstellen
- `/events` - Alle Events mit Statistiken anzeigen
- `/view_sums` - Nur Summen ohne persönliche Details anzeigen

## Datenspeicherung

Alle Daten werden in der `data.json` Datei gespeichert. Dies umfasst:
- Events (Name, Erstellungsdatum, Ersteller)
- Eintragungen (Event ID, User ID, Benutzername, Betrag, Zeitstempel)

## Datenschutz & Nutzung

- Der Bot funktioniert in **privaten Nachrichten** und in **Gruppen, wenn er erwähnt wird** (@botname)
- Befehle können in Gruppen verwendet werden, indem der Bot erwähnt wird: `/list_events@botname`
- Zum Eintragen von Beträgen sollten Nutzer dem Bot privat schreiben (Sicherheit)
- Wenn Nutzer Beträge eintragen, erhalten Admins Benachrichtigungen mit nur dem Betrag (ohne persönliche Details)
- Admins können nur Summen ohne persönliche Details mit dem Befehl `/view_sums` anzeigen
