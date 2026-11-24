# Logiktest

Stand: 24.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

> Echte Nodes und Ausdrücke aus dem Repository laufen in isoliertem n8n 2.43.7; Telegram, Gmail und Google Calendar sind durch feste Beispieldaten ersetzt: **kein Funktionstest der Integrationen.**

**Ergebnis: PASS, 10 von 10** (F1–F5, D1–D2, G1–G3); Szenarien in [`docs/test-plan.md`](../docs/test-plan.md), Aufbau in [`tests/logic-harness/README.md`](../tests/logic-harness/README.md).

Was die Szenarien belegen: Der Absenderfilter lässt nur die erlaubte ID durch (auch bei Knopfdrücken) und ignoriert fremde und fehlende Absender. «Termin löschen» löscht nur einen aktiven Termin und meldet einen bereits gelöschten auf Deutsch. «Suche in Gmail» sucht bei leerer Anfrage nicht und meldet «keine Treffer» klar.

Was sie nicht belegen: Verhalten des Modells (Werkzeugwahl, Inhalt der Antworten), die Freigabe in Telegram, die Google-APIs.

Wiederholung: `bash tests/logic-harness/run.sh`
