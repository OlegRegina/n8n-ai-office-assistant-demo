# Hinweise zur automatischen Prüfung

Stand: 24.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

- [`validation-report.txt`](validation-report.txt) ist die Ausgabe von `scripts/validate.py` und gilt nur für den Dateistand bei seiner Erzeugung (Datum im Kopf). Er wurde mit den privaten Exporten erzeugt (S2b, S4, S7 ausgeführt); vor einer Veröffentlichung wiederholt der Autor ihn mit persönlichen Suchbegriffen (`--deny`).
- **S7** vergleicht nicht Feld für Feld, sondern verlangt, dass die Workflows im Repository genau das Ergebnis von `scripts/sanitize.py` auf den privaten Exporten sind. Damit sind nur die dort festgelegten Regeln angewendet, jede mit erwarteter Anzahl.
- **S11/S12** prüfen die Sicherheitsarchitektur statisch: schreibende Werkzeuge nur über Freigabe-Nodes; Absenderfilter direkt nach dem Trigger.
- **Persönliche Suchbegriffe (S5, `--deny`)** werden als ganzes Wort gesucht (Gross-/Kleinschreibung egal), wie im Kalender-Demo. Grund: der öffentliche GitHub-Login in `LICENSE` enthält den Vornamen als Wortteil. Geprüft an vier veränderten Kopien: Name als eigenes Wort, in einer E-Mail-Adresse, in Grossbuchstaben und in kyrillischer Schrift – alle erkannt; der Login allein löst keinen Fund aus.

## Wirksamkeit der Prüfung

`validate.py` wurde an sieben absichtlich veränderten Kopien getestet; alle wurden erkannt: Senden direkt am Agenten ohne Freigabe (S11), Absenderfilter umgangen (S12), Filter mit verbundenem Ausgang für Fremde (S6, S12), Zugangsdaten an einem Werkzeug (S3), fremde E-Mail-Adresse in einer Datei (S5), aktives Werkzeug (S8), schreibendes Kalender-Werkzeug direkt am Agenten (S11). Zusätzlich: ein russisches Wort ausserhalb der zwei erlaubten Zeilen wird erkannt (S5).
