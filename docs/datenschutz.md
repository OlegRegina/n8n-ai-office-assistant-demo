# Datenschutz

> **Eigenprojekt / Demo, kein Kundenauftrag.**
> **Keine Rechtsberatung, keine Konformitätszusage.** Diese Seite beschreibt die Datenflüsse, damit eine Prüfung nach dem Schweizer Datenschutzgesetz (revDSG) und – wo anwendbar – der DSGVO vorbereitet werden kann.

## Datenflüsse

| Daten | Ziel | Zweck |
|---|---|---|
| Nachrichten an den Assistenten, Antworten, Freigabe-Nachrichten, Chat- und Benutzer-ID | Telegram | Bedienung und Freigabe; Bot-Chats sind nicht Ende-zu-Ende-verschlüsselt (Angabe des Anbieters, nicht geprüft) |
| Auftrag, Gesprächsverlauf (Fenster je Chat), Ergebnisse der Werkzeuge: Suchtreffer, Inhalte gelesener E-Mails (bis 6000 Zeichen), Anhänge (bis 8000 Zeichen), gelesene Dokumente, Termine | OpenAI | Verstehen des Auftrags, Auswahl der Werkzeuge, Antwort |
| Suchanfragen, Entwürfe (Empfänger, Betreff, Text, Anhang), gesendete E-Mails | Google (Gmail, Drive) | Lesen, Entwerfen, Senden nach Freigabe |
| Termine (Titel, Zeiten) | Google Calendar | Lesen; Anlegen, Ändern, Löschen nach Freigabe |
| Schlüssel, Empfänger, Betreff und Status erstellter Entwürfe | n8n-Datentabelle `AI_DRAFT_REGISTRY` | Schutz vor doppelten Entwürfen |
| Ein- und Ausgaben der Nodes einer Ausführung | n8n-Instanz (Ausführungsdaten) | Ablauf und Fehlersuche, je nach Einstellungen der Instanz |

## Aufbewahrung

Ein Löschkonzept ist nicht umgesetzt: Telegram-Chats, Gmail, Drive und Calendar bis zur manuellen Löschung; Gesprächsgedächtnis und Datentabelle werden vom Workflow nicht geleert; n8n-Ausführungsdaten nach den Einstellungen der Instanz; OpenAI nach den Bedingungen und Einstellungen des Kontos (nicht geprüft).

## Hinweise

- **Personenbezogene Daten Dritter:** E-Mails, Anhänge, Dokumente und Termine enthalten Daten von Dritten; gelesene Inhalte gehen an OpenAI.
- **Anbieter ausserhalb der Schweiz:** OpenAI, Google und Telegram. Vor einem Einsatz mit echten Daten: Bekanntgabe ins Ausland, Verträge zur Auftragsbearbeitung, Einstellungen der Anbieter prüfen.
- **Zugriff:** Nur die eingetragene Telegram-Benutzer-ID wird bedient; Nachrichten anderer werden vom Trigger dennoch angenommen und als Ausführung gespeichert.
- **Menschliche Kontrolle:** Senden und Kalenderänderungen nur nach Freigabe; Lesen und Entwürfe ohne Freigabe.
- **Demo-Betrieb:** nur synthetische Daten aus [`test-data/`](../test-data/) und Test-Konten.

## Nicht geprüft

- Ob ein konkreter Einsatz revDSG oder DSGVO erfüllt.
- Welche Ausführungsdaten eine konkrete n8n-Instanz speichert und wie lange.
