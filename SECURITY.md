# Sicherheit

Dieses Repository enthält bereinigte Kopien privater n8n-Exporte. **Eigenprojekt / Demo, kein Kundenauftrag.**

## Was entfernt oder ersetzt wurde

| Inhalt | Behandlung |
|---|---|
| Zugangsdaten-Verweise an Nodes (ID und Name), Webhook-IDs | entfernt (25 bzw. 13) |
| Testdaten im Workflow (pinData), Verwaltungsfelder (Versionen, Autor, Kopie aller Nodes der aktiven Fassung, Projekt, Zeitstempel) | entfernt |
| Verweis auf den privaten Error-Workflow | entfernt |
| Workflow-IDs der privaten Instanz | durch feste Demo-IDs ersetzt (`demo…`); die Werkzeug-Verweise zeigen auf diese |
| Kalender (E-Mail-Adresse des Kontos) | durch `primary` ersetzt |
| Telegram-Benutzer-ID im Absenderfilter | durch `REPLACE_WITH_TELEGRAM_USER_ID` ersetzt |
| Verweis auf die n8n-Datentabelle (Tabellen- und Projekt-ID) | durch `REPLACE_WITH_DATA_TABLE_ID` ersetzt; der Tabellenname bleibt |
| E-Mail-Adressen in Beispielen der Gmail-Suche | durch `anna.muster@example.com` ersetzt |
| Name in den Grussformel-Regeln | durch `[Your Name]` ersetzt |
| Kürzel des Arbeitgebers in der Beschreibung des Kalender-Werkzeugs | entfernt |
| Notizzettel (interne Entwicklungsnotizen auf Russisch, teils veraltet, mit Test-IDs) | durch kurze deutsche Beschreibungen ersetzt |
| Antwortsprache und russische Texte (Freigaben, Meldungen, Kommentare) | auf Deutsch bzw. Englisch übertragen; zwei Regeln für E-Mails auf Russisch bleiben |
| MCP-Zugriff und Aktivierung | `availableInMCP = false`, `active = false` |
| Interne UUIDs von Nodes und Bedingungen | bewusst unverändert: gewähren keinen Zugriff |

Alle Änderungen führt [`scripts/sanitize.py`](scripts/sanitize.py) aus; jede Regel hat eine erwartete Anzahl, und das Skript enthält keine privaten Werte. Es enthält die ursprünglichen russischen Textstellen, damit die Übertragung nachvollziehbar ist (keine personenbezogenen Daten).

## Wie geprüft wurde

- [`scripts/validate.py`](scripts/validate.py): erlaubte Schlüssel, Musterprüfung aller Dateien, Struktur, Platzhalter, **Freigabe vor schreibenden Werkzeugen (S11)**, **Absenderfilter (S12)**; mit den privaten Exporten zusätzlich: kein privater Wert in irgendeiner Datei (S4) und die Workflows sind genau das Ergebnis von `sanitize.py` (S7). Bericht: [`evidence/validation-report.txt`](evidence/validation-report.txt).
- Die Systemanweisung (rund 16 700 Zeichen) und alle Texte wurden zusätzlich manuell durchgesehen.

Automatische Prüfungen sind **kein Beweis**, dass keine sensiblen Daten mehr enthalten sind.

## Risiken bei der Nutzung

- **Absender:** Ohne eingetragene Benutzer-ID antwortet der Assistent niemandem. Die Freigabe-Nachricht geht an den Absender der Nachricht – deshalb ist der Absenderfilter zwingend. Den Bot nicht öffentlich bekannt machen.
- **Freigabe zeigt nur IDs** beim Senden und Löschen (E1): Vor dem Freigeben Entwurf bzw. Termin ansehen.
- **Zugriffsrechte:** Die Zugänge zu Gmail, Drive und Calendar erlauben in der Regel mehr, als die Werkzeuge nutzen. Für Tests eigene Test-Konten verwenden.
- Zugangsdaten nur in n8n hinterlegen, nie in Workflow-Dateien, Screenshots oder Chats; ein offengelegtes Token sofort widerrufen.

## Nicht vertrauenswürdige Eingaben (Prompt Injection)

- **Quellen:** E-Mails, Anhänge, Dokumente und Termine stammen oft von Dritten. Ihr Text geht vollständig (bis zu den genannten Grenzen) an den KI-Agenten.
- **Was die Anweisung vorgibt:** Inhalte sind als nicht vertrauenswürdig zu behandeln; Anweisungen darin dürfen Rolle, Freigaben und Regeln nicht ändern.
- **Was technisch begrenzt:** Senden und Kalenderänderungen laufen nur über einen Freigabe-Node (S11). Lesen und Entwürfe laufen ohne Freigabe: Ein manipulierter Inhalt könnte den Agenten zu weiteren Lesevorgängen oder zu einem Entwurf verleiten, der Inhalte enthält; gesendet wird dieser nur nach Freigabe – die aber nur die Entwurf-ID zeigt (E1).
- **Nicht geprüft:** Verhalten der Modelle gegenüber gezielter Prompt Injection (Testfall A12).

## Probleme melden

Bitte ein Issue eröffnen – **ohne** Zugangsdaten, IDs oder personenbezogene Daten. Für vertrauliche Hinweise die private Sicherheitsmeldung des Repositorys verwenden, sofern aktiviert.
