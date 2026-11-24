# Lokaler Importtest – n8n 2.43.7

Stand: 24.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

> **Lokaler Import ≠ Funktionstest der Integrationen.** Geprüft wurde nur, ob sich die 12 bereinigten Workflows in eine leere, isolierte n8n-Instanz importieren lassen und Struktur, Parameter und Verweise erhalten bleiben. Telegram, Google und OpenAI wurden nicht aufgerufen.

| Punkt | Wert |
|---|---|
| Image | `n8nio/n8n:2.43.7`, Digest `sha256:3db21366be1d3c77c1708963129c051948573019659e8873e0294be035ffc1b2`, `linux/arm64`, lokal (`--pull never`) |
| Isolation | `--network none`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--rm`; keine Ports, keine Zugangsdaten; leeres Datenverzeichnis |
| Befehle | `n8n import:workflow --separate --input=/import/`, `n8n export:workflow --all --separate --pretty --output=/export/` |
| Geprüfter Stand | alle 12 Dateien unter `workflows/`; SHA-256 ihrer Verkettung (Haupt-Workflow, dann `tools/*.json` alphabetisch): `8f47b870f7e9fdc5368415c4a299adf2054332bfcfd2dcabb6db298b2c17b139` |

| Prüfung | Ergebnis |
|---|---|
| Import und Rücklesen | PASS – 12 von 12 |
| IDs der Workflows (Demo-IDs) nach dem Import unverändert | PASS |
| Namen, Typen, Typversionen und Parameter aller 111 Nodes, Verbindungen | PASS – unverändert |
| 11 Werkzeug-Verweise des Haupt-Workflows zeigen auf importierte Workflows | PASS – 11 von 11 |
| Workflows inaktiv; keine Zugangsdaten an Nodes | PASS |

Nicht geprüft: Import über die Oberfläche (dort erhalten die Workflows neue IDs, siehe [setup](../docs/setup.md)), Verbinden der Zugänge, Aktivieren, andere n8n-Versionen.
