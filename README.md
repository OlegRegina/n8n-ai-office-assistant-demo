# KI-Büroassistent – Demo (n8n)

> **Eigenprojekt / Demo, kein Kundenauftrag.**
> Bereinigte Kopie eines privat betriebenen n8n-Systems (1 Haupt-Workflow, 11 Werkzeug-Workflows). Alle Testdaten sind synthetisch. Die Workflows in diesem Repository sind **inaktiv** und wurden in der Demo **nicht gegen echte Dienste ausgeführt**.
> English version: [README.en.md](README.en.md)

## Was das System macht

Man schreibt dem Assistenten in Telegram einen Auftrag in normaler Sprache, zum Beispiel: «Suche die letzte E-Mail von Frau Muster und bereite eine Antwort mit dem Vertrag vor.» Ein KI-Agent (OpenAI) wählt dafür Werkzeuge aus:

| Bereich | Werkzeuge | Freigabe nötig? |
|---|---|---|
| Gmail lesen | E-Mails suchen, E-Mail lesen, Anhang lesen (DOCX, PDF) | nein (nur lesend) |
| Gmail Entwürfe | Antwortentwurf, neuer Entwurf mit einem Anhang aus Google Drive | nein – ein Entwurf wird nicht gesendet |
| Gmail senden | Entwurf senden | **ja** |
| Google Drive | Dateien suchen, Dokument lesen | nein (nur lesend) |
| Google Calendar | Termine lesen, Verfügbarkeit prüfen | nein (nur lesend) |
| Google Calendar | Termin anlegen, ändern, löschen | **ja** |

**Freigabe:** Vor dem Senden einer E-Mail und vor jeder Änderung am Kalender schickt das System eine Freigabe-Nachricht in Telegram («✅ E-Mail senden» / «❌ Abbrechen»). Ohne Ja geschieht nichts davon. Dass alle schreibenden Werkzeuge nur über einen Freigabe-Node am Agenten hängen, prüft [`scripts/validate.py`](scripts/validate.py) automatisch (S11).

**Absenderfilter:** Nur die eingetragene Telegram-Benutzer-ID wird bedient; alle anderen Nachrichten werden still ignoriert (S12, Logiktest F1–F5).

**Sprache:** Der Assistent antwortet in der Sprache der Nachricht, Deutsch oder Englisch. Freigaben und Meldungen der Werkzeuge sind deutsch.

Ablauf und alle Nodes: [docs/architecture.md](docs/architecture.md).

## Inhalt

| Pfad | Inhalt |
|---|---|
| [`workflows/ki-bueroassistent.json`](workflows/ki-bueroassistent.json) | Haupt-Workflow «KI-Büroassistent (Demo)» (26 Nodes) |
| [`workflows/tools/`](workflows/tools/) | 11 Werkzeug-Workflows (85 Nodes) |
| [`docs/setup.md`](docs/setup.md) | Einrichtung: Import, Zugänge, Benutzer-ID, Datentabelle, Test |
| [`docs/architecture.md`](docs/architecture.md) | Ablauf, Werkzeuge, Freigaben |
| [`docs/test-plan.md`](docs/test-plan.md) | Testfälle mit Status |
| [`docs/datenschutz.md`](docs/datenschutz.md) | Datenflüsse und Datenschutzhinweise |
| [`test-data/`](test-data/) | Synthetische Testnachrichten und Testdaten |
| [`tests/logic-harness/`](tests/logic-harness/) | Wiederholbarer Logiktest (10 Szenarien, isoliertes n8n, Docker) |
| [`evidence/`](evidence/) | Prüfbericht, Importtest, Logiktest, Protokoll der Live-Tests |
| [`scripts/`](scripts/) | Bereinigung (`sanitize.py`) und Prüfung (`validate.py`) |
| [`SECURITY.md`](SECURITY.md) | Was entfernt wurde, Risiken, Meldung von Problemen |

## Import in Kürze

1. Alle 12 Dateien importieren – am einfachsten per CLI: `n8n import:workflow --separate --input=<ordner>`. Die Demo-IDs bleiben dabei erhalten, und die 11 Werkzeuge sind sofort mit dem Haupt-Workflow verbunden. Beim Import über die Oberfläche die Werkzeuge im Haupt-Workflow neu auswählen ([setup](docs/setup.md)).
2. Zugänge verbinden: Telegram, Gmail, Google Drive, Google Calendar (OAuth2), OpenAI.
3. **Eigene Telegram-Benutzer-ID** in `IF — Allowed Sender?` eintragen (Platzhalter `REPLACE_WITH_TELEGRAM_USER_ID`); ohne Eintrag antwortet der Assistent niemandem.
4. Datentabelle `AI_DRAFT_REGISTRY` anlegen und im Werkzeug «Gmail Create Draft — Single Attachment» auswählen (Platzhalter `REPLACE_WITH_DATA_TABLE_ID`).
5. `[Your Name]` in der Systemanweisung durch den eigenen Namen ersetzen (Grussformel der Entwürfe).
6. Nur mit **Test-Konten** und einem eigenen Bot testen.

## Status & Grenzen

### Stand der Prüfung (24.11.2026)

| Bereich | Status | Nachweis |
|---|---|---|
| Bereinigung: erlaubte Schlüssel, Musterprüfung aller Dateien, Struktur, Workflows = Ergebnis von `sanitize.py` | PASS laut automatischem Bericht (gilt nur für den damaligen Dateistand) | [`evidence/validation-report.txt`](evidence/validation-report.txt) |
| Freigabe vor Senden und Kalenderänderungen; Absenderfilter direkt nach dem Trigger (statische Prüfung S11, S12) | PASS; sieben absichtlich veränderte Kopien wurden alle erkannt | [`evidence/validation-notes.md`](evidence/validation-notes.md) |
| Lokaler Import aller 12 Workflows in n8n 2.43.7 (isoliert, ohne Netzwerk) | PASS: IDs, Parameter und Verbindungen unverändert, 11 von 11 Werkzeug-Verweisen aufgelöst | [`evidence/import-test.md`](evidence/import-test.md) |
| Logiktest mit Beispieldaten (Absenderfilter, Termin löschen, Suche in Gmail) | PASS, 10 von 10; **nicht** Google, Telegram oder das Modell | [`evidence/logic-test.md`](evidence/logic-test.md) |
| Live-Tests im privaten System des Autors (Vorgängerfassung auf Russisch, ohne Absenderfilter) | DOKUMENTIERT, teilweise; keine öffentlichen Nachweise | [`evidence/live-test.md`](evidence/live-test.md) |
| Diese Fassung (Deutsch/Englisch, mit Absenderfilter) mit echten Diensten | NICHT GETESTET | [`docs/test-plan.md`](docs/test-plan.md) |

> **Lokaler Import ≠ Funktionstest der Integrationen.**

### Bekannte Grenzen

**E1 – Freigabe zeigt nur IDs.** Die Freigabe-Nachricht zum Senden nennt nur die Entwurf-ID, die zum Löschen nur die Termin-ID – nicht Empfänger, Betreff oder Termintitel. Wer freigibt, sollte den Entwurf bzw. Termin vorher selbst ansehen (der Assistent meldet nach dem Erstellen eines Entwurfs Empfänger, Betreff und Anhang). Bei Anlegen und Ändern zeigt die Freigabe die Angaben des Werkzeugaufrufs.

**E2 – Fremder Text im Prompt (Prompt Injection).** E-Mails, Anhänge und Dokumente sind nicht vertrauenswürdig. Die Systemanweisung verbietet, Anweisungen daraus zu befolgen; garantiert ist das nicht. Lesende Werkzeuge und Entwürfe laufen ohne Freigabe; Senden und Kalenderänderungen nicht (siehe [SECURITY.md](SECURITY.md)).

**E3 – Freigabe über Link.** In n8n 2.43.7 reagierten die Knöpfe direkt im Telegram-Chat im privaten System nicht; dort wird die Freigabe über einen Link bestätigt. Im Export ist beim Node «APPROVAL — Calendar Create» die Freigabe im Chat eingeschaltet, bei den drei anderen nicht; welche Variante in einer anderen Instanz funktioniert, ist nicht geprüft.

**E4 – Absenderfilter neu.** Der Filter wurde am 24.11.2026 eingeführt, nachdem sich gezeigt hatte, dass ohne ihn nach der Konfiguration jede Person, die den Bot findet, Aufträge geben und die Freigaben an sich selbst erhalten konnte (die Freigabe geht an den Absender der Nachricht). Im Logiktest weist er fremde und fehlende Absender ab; die Abweisung eines fremden Kontos ist live nicht geprüft.

**E5 – Datenumfang an OpenAI.** Inhalte gelesener E-Mails (bis 6000 Zeichen), Anhänge (bis 8000 Zeichen), gelesene Dokumente, Termine und der Gesprächsverlauf gehen an das Modell ([Datenschutz](docs/datenschutz.md)).

**E6 – Sprache.** Diese Fassung antwortet auf Deutsch oder Englisch. Die privat getestete Fassung antwortete auf Russisch; die deutsche und englische Fassung ist live nicht geprüft.

**E7 – Umfang der Werkzeuge.** Ein Anhang pro Entwurf; Anhänge lesen: DOCX und PDF; Dokumente lesen: PDF und Google Docs (über PDF), keine Tabellen oder Präsentationen. Zeitzone fest `Europe/Zurich`. Die Liste «AVAILABLE TOOLS» in der Systemanweisung nennt nicht alle angeschlossenen Werkzeuge; kleine Tippfehler der Anweisung sind unverändert übernommen.

**E8 – Doppelte Entwürfe.** Das Werkzeug «Entwurf mit Anhang» merkt sich erstellte Entwürfe in der n8n-Datentabelle `AI_DRAFT_REGISTRY`; ohne diese Tabelle läuft es nicht. Der Antwortentwurf hat keinen solchen Schutz.

**E9 – Fehler und Gedächtnis.** Scheitert ein Dienst, meldet der Assistent dies, sofern das Werkzeug ein Ergebnis zurückgibt; bei einem Fehler des Haupt-Workflows gibt es keine Antwort. Das Gesprächsgedächtnis (Fenster je Chat) wird nicht gelöscht.

### Nicht geprüft

- Ausführung dieser Fassung mit echten Diensten; Aktivieren, Verbinden der Zugänge, Webhook.
- Verhalten des Modells bei gezielter Prompt Injection.
- Andere n8n-Versionen als 2.43.7 und die Plattform `linux/amd64`.

## Datenschutz

Das System verarbeitet E-Mails, Dokumente und Termine und übermittelt Teile davon an Anbieter ausserhalb der Schweiz (OpenAI, Google, Telegram): [docs/datenschutz.md](docs/datenschutz.md). Keine Rechtsberatung, keine Konformitätszusage.

## Lizenz

MIT – siehe [LICENSE](LICENSE). Eigenentwicklung, mit Unterstützung von KI-Assistenten erstellt.
