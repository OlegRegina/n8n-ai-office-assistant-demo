# Einrichtung

> **Eigenprojekt / Demo, kein Kundenauftrag.** Der lokale Import wurde mit n8n **2.43.7** geprüft ([`evidence/import-test.md`](../evidence/import-test.md)); Zugänge und ein Lauf mit echten Diensten sind in dieser Demo **nicht geprüft**.

## Voraussetzungen

- n8n (geprüft: Import in 2.43.7) mit Datentabellen.
- **Test-Konten:** Gmail, Google Drive, Google Calendar – keine produktiven Konten.
- Ein **eigener Telegram-Bot** und die **eigene Telegram-Benutzer-ID**.
- Ein OpenAI-API-Zugang.
- Eine n8n-Instanz, die Telegram über eine Webhook-Adresse erreicht (`WEBHOOK_URL`); Freigaben laufen über Links auf diese Instanz.

## Schritte

1. **Import aller 12 Dateien.** Per CLI (empfohlen): Ordner mit `workflows/ki-bueroassistent.json` und `workflows/tools/*.json` anlegen, dann `n8n import:workflow --separate --input=<ordner>`. Die Demo-IDs bleiben erhalten; die Werkzeuge sind verbunden. Über die Oberfläche («Import from File») erhält jeder Workflow eine neue ID: Dann im Haupt-Workflow bei jedem der 11 Werkzeug-Nodes den passenden Workflow neu auswählen (Namen wie in [architecture](architecture.md)).
2. **Zugänge verbinden:** Telegram (Trigger, Antwort, 4 Freigaben), Gmail (Werkzeuge Gmail), Google Drive (Drive-Werkzeuge und Anhänge der Entwürfe), Google Calendar (2 Kalender-Werkzeuge im Haupt-Workflow und 3 Werkzeug-Workflows), Gmail OAuth2 für den HTTP-Request in «Gmail Send Draft», OpenAI (Chat-Modell).
3. **Benutzer-ID eintragen:** in `IF — Allowed Sender?` den Platzhalter `REPLACE_WITH_TELEGRAM_USER_ID` durch die eigene ID ersetzen (zu finden in einer Ausführung unter `message.from.id`).
4. **Datentabelle anlegen:** `AI_DRAFT_REGISTRY` mit den Text-Spalten `draft_key`, `status`, `draft_id`, `recipient`, `subject`, `created_at`; im Werkzeug «Gmail Create Draft — Single Attachment» in beiden Datentabellen-Nodes auswählen (Platzhalter `REPLACE_WITH_DATA_TABLE_ID`).
5. **Name eintragen:** in der Systemanweisung des Nodes «AI Agent» `[Your Name]` (3×) durch den eigenen Namen ersetzen; ebenso im Werkzeug-Node `gmail_create_draft_single` (Feld `body`).
6. **Kalender prüfen:** `primary` = Hauptkalender des verbundenen Kontos; für einen Test-Kalender dessen ID eintragen.
7. **Test:** Testdaten nach [`test-data/synthetic-messages.json`](../test-data/synthetic-messages.json) anlegen («prepare»), Haupt-Workflow nur für die Dauer des Tests aktivieren (die Werkzeuge werden aufgerufen und müssen nicht aktiv sein), Nachrichten A01–A13 senden, Ergebnisse mit [test-plan](test-plan.md) vergleichen.
8. **Danach:** Workflow deaktivieren, Testdaten entfernen.
