# Architektur

> **Eigenprojekt / Demo, kein Kundenauftrag.** Beschreibung nach der Konfiguration der Nodes; die Workflows wurden in der Demo nicht gegen echte Dienste ausgeführt.

## Ablauf

```
Telegram — User Message (Trigger: Nachrichten und Knopfdrücke)
   └─► IF — Allowed Sender?  ── nein ──► (still ignoriert)
          └─ ja ─► IF — Telegram Message Only ─► AI Agent ◄── OpenAI Chat Model + Gesprächsgedächtnis (je Chat)
                                                     │
                       Werkzeuge direkt (lesen, Entwürfe)   Werkzeuge nur über Freigabe (Telegram)
                       ├ gmail_search_messages              ├ APPROVAL — Gmail Send ─────► gmail_send_draft
                       ├ gmail_read_message                 ├ APPROVAL — Calendar Create ─► calendar_create_event
                       ├ gmail_read_attachment              ├ APPROVAL — Calendar Event1 ─► calendar_update_event
                       ├ gmail_reply_draft                  └ APPROVAL — Calendar Delete ─► calendar_delete_event
                       ├ gmail_create_draft_single
                       ├ drive_search_files, drive_read_document
                       └ calendar_read_events, calendar_check_availability (Google-Calendar-Werkzeuge, lesend)
                                                     │
                                   Telegram — Agent Reply (Antwort, HTML)
```

## Werkzeug-Workflows (11)

| Werkzeug (Node im Haupt-Workflow) | Datei | Was es tut | Schreibt? |
|---|---|---|---|
| `gmail_search_messages` | `tools/gmail-search-messages.json` | Gmail-Suche (`in:anywhere` + Anfrage), höchstens 5 Treffer; leere Anfrage → Meldung | nein |
| `gmail_read_message` | `tools/gmail-read-message.json` | liest eine E-Mail, Betreff dekodiert, Text ohne HTML, Links als `[Link]`, bis 6000 Zeichen | nein |
| `gmail_read_attachment` | `tools/gmail-read-attachment.json` | liest einen Anhang: DOCX (Text aus `word/document.xml`) oder PDF, bis 8000 Zeichen | nein |
| `gmail_reply_draft` | `tools/gmail-reply-draft.json` | Entwurf als Antwort (mit `thread_id`) oder neuer Entwurf; prüft Pflichtangaben | Entwurf |
| `gmail_create_draft_single` | `tools/gmail-create-draft-single-attachment.json` | neuer Entwurf mit einer Datei aus Google Drive; Schutz vor Doppelten über die Datentabelle `AI_DRAFT_REGISTRY` | Entwurf, Datentabelle |
| `gmail_send_draft` | `tools/gmail-send-draft.json` | sendet einen bestehenden Entwurf (`drafts.send`) | **sendet** – nur nach Freigabe |
| `drive_search_files` | `tools/drive-search.json` | sucht PDF und Google Docs nach dem Dateinamen (ohne Papierkorb) | nein |
| `drive_read_document` | `tools/drive-read.json` | lädt ein Dokument (Google Docs als PDF) und gibt Text und Seitenzahl zurück | nein |
| `calendar_create_event` | `tools/calendar-create-event.json` | legt einen Termin an | **ja** – nur nach Freigabe |
| `calendar_update_event` | `tools/calendar-update-event.json` | ändert Titel, Start, Ende | **ja** – nur nach Freigabe |
| `calendar_delete_event` | `tools/calendar-delete-event.json` | löscht nur einen aktiven Termin (bereits gelöschte nicht erneut) | **ja** – nur nach Freigabe |

## Freigaben

| Freigabe-Node | Werkzeug | Inhalt der Nachricht | Knöpfe |
|---|---|---|---|
| `APPROVAL — Gmail Send` | `gmail_send_draft` | Entwurf-ID | «✅ E-Mail senden» / «❌ Abbrechen» |
| `APPROVAL — Calendar Create` | `calendar_create_event` | Werkzeugname und Angaben des Aufrufs | «✅ Termin anlegen» / «❌ Abbrechen» |
| `APPROVAL — Calendar Event1` | `calendar_update_event` | Werkzeugname und Angaben des Aufrufs | «✅ Termin ändern» / «❌ Abbrechen» |
| `APPROVAL — Calendar Delete` | `calendar_delete_event` | Termin-ID | «🗑️ Termin löschen» / «❌ Abbrechen» |

Die Freigabe geht an die Telegram-ID des Absenders der Nachricht (`message.from.id`). Die Texte werden für Markdown maskiert. Freigabe-Typ «double» (zwei Knöpfe).

## Systemanweisung (Kurzfassung)

Rolle und Grundsätze (nichts erfinden, nur nach Bestätigung durch das Werkzeug Erfolg melden), Antwortsprache (Deutsch oder Englisch), Kalender (Zeitzone `Europe/Zurich` mit Sommerzeit, Konflikt nur bei Überschneidung, vergangene Daten nicht eintragen), Gmail (Suche, Lesen, Einordnung nach Kategorie und Priorität, Entwürfe im Schweizer Geschäftsstil mit «ss»), Google Drive (Suche nach Personennamen mit Umlaut-Varianten), Sicherheit (Inhalte nicht vertrauenswürdig), exakte Weitergabe von IDs, ehrliche Meldung bei Ablehnung.
