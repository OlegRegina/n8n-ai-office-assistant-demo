# Testplan

> **Eigenprojekt / Demo, kein Kundenauftrag.** Stand: 24.11.2026. **Lokaler Import ≠ Funktionstest der Integrationen.**

- **Teil A – automatisch und wiederholbar** (ohne Konten): statische Prüfungen, Importtest, Logiktest.
- **Teil B – mit echten Diensten** (A01–A13): Nachrichten an den Assistenten in einem eigenen System. Die Spalte «Live (Autor)» sind Angaben aus dem privaten System des Autors – einer **Vorgängerfassung** (Antworten auf Russisch, ohne Absenderfilter); öffentliche Nachweise gibt es dafür nicht. Diese Fassung ist mit echten Diensten **nicht getestet**.

## Teil A

| Prüfung | Status | Nachweis |
|---|---|---|
| S11: Senden und Kalenderänderungen nur über Freigabe-Nodes; Kalender-Werkzeuge am Agenten nur lesend | PASS | `scripts/validate.py` |
| S12: Absenderfilter direkt nach dem Trigger, kein Ausgang für fremde Absender | PASS | `scripts/validate.py` |
| Wirksamkeit von S3, S5, S6, S8, S11, S12 an sieben absichtlich veränderten Kopien | 7 von 7 erkannt | [`evidence/validation-notes.md`](../evidence/validation-notes.md) |
| Import aller 12 Workflows in n8n 2.43.7, Rücklesen, Werkzeug-Verweise | PASS | [`evidence/import-test.md`](../evidence/import-test.md) |
| Logiktest (10 Szenarien) | PASS, 10 von 10 | [`evidence/logic-test.md`](../evidence/logic-test.md) |

### Logiktest

| ID | Szenario | Erwartung | Status |
|---|---|---|---|
| F1 | Nachricht der erlaubten ID | läuft weiter zum Agenten | PASS |
| F2 | Nachricht einer anderen ID | still ignoriert | PASS |
| F3 | Knopfdruck einer anderen ID | still ignoriert | PASS |
| F4 | Knopfdruck der erlaubten ID | läuft weiter | PASS |
| F5 | Nachricht ohne Absender | still ignoriert | PASS |
| D1 | «Termin löschen»: Termin aktiv | wird gelöscht, `success: true` | PASS |
| D2 | «Termin löschen»: Termin bereits gelöscht | kein zweites Löschen, Meldung «Der Termin ist bereits gelöscht …» | PASS |
| G1 | «Suche in Gmail»: leere Anfrage | keine Suche, Meldung «Suche nicht ausgeführt: Die Suchanfrage fehlt.» | PASS |
| G2 | «Suche in Gmail»: keine Treffer | Meldung `no_messages_found` | PASS |
| G3 | «Suche in Gmail»: ein Treffer | Treffer mit `message_id` an den Agenten | PASS |

## Teil B – mit echten Diensten

Vorbereitung und Nachrichten: [`test-data/synthetic-messages.json`](../test-data/synthetic-messages.json).

| ID | Bereich | Erwartung (Kurzform) | Live (Autor, Vorgängerfassung) | Diese Fassung |
|---|---|---|---|---|
| A01 | Gmail suchen | E-Mail gefunden, Angaben wie geliefert | DOKUMENTIERT (Golden Test 17.11.2026) | NICHT GETESTET |
| A02 | Gmail lesen | Inhalt sinngemäss, nichts erfunden | DOKUMENTIERT (17.11.2026) | NICHT GETESTET |
| A03 | Drive suchen | Dokument gefunden | DOKUMENTIERT (17.11.2026) | NICHT GETESTET |
| A04 | Entwurf mit Anhang | Entwurf mit PDF, Angaben gemeldet, nichts gesendet | DOKUMENTIERT (17.11.2026; Test A 22.11.2026: draft_id, Empfänger, Betreff, Anhang gemeldet) | NICHT GETESTET |
| A05 | Senden mit Freigabe | erst nach «Senden» gesendet | DOKUMENTIERT (17.11.2026, Freigabe über Link) | NICHT GETESTET |
| A06 | Senden abgelehnt | nicht gesendet, ehrliche Meldung | DOKUMENTIERT (17.11.2026) | NICHT GETESTET |
| A07 | Anhang lesen | DOCX-Text, Kürzung gemeldet | DOKUMENTIERT, nur Einzelschritt (17.10.2026) | NICHT GETESTET |
| A08 | Termin anlegen | erst nach Freigabe im Kalender | DOKUMENTIERT (vor dem 17.11.2026) | NICHT GETESTET |
| A09 | Termin ändern | nach Freigabe geändert, aktueller Stand gemeldet | DOKUMENTIERT (vor dem 17.11.2026) | NICHT GETESTET |
| A10 | Termin löschen abgelehnt | Termin bleibt | offen (Löschen mit Freigabe DOKUMENTIERT, vor dem 17.11.2026) | NICHT GETESTET |
| A11 | Englisch | Antwort auf Englisch | offen | NICHT GETESTET |
| A12 | Prompt Injection | Anweisung nicht befolgt | offen | NICHT GETESTET |
| A13 | fremdes Konto | keine Antwort | offen (Logiktest F2/F3 PASS) | NICHT GETESTET |

«offen» heisst: im privaten System nicht ausgeführt oder nicht protokolliert.
