# Logiktest

**Was getestet wird:** echte Nodes und Ausdrücke aus `workflows/`: der Absenderfilter des Haupt-Workflows (mit erfundener erlaubter ID 42), das Werkzeug «Termin löschen» (Prüfung «Termin aktiv?», Ergebnis- und Meldungs-Nodes) und das Werkzeug «Suche in Gmail» (Prüfung der Anfrage, Treffer, keine Treffer).

**Was ersetzt ist:** Trigger, Gmail- und Calendar-Nodes durch Code-Nodes mit demselben Namen und festen Beispieldaten – Verbindungen und `$('…')`-Verweise bleiben gleich. Keine Aussage über Google, Telegram oder das Modell.

**Isolierung:** `--network none`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--pull never`, `--rm`; keine Zugangsdaten, keine Ports.

```bash
bash tests/logic-harness/run.sh
```

Voraussetzung: Docker und das lokale Image `n8nio/n8n:2.43.7`. Erwartet: `10/10 PASS`.
