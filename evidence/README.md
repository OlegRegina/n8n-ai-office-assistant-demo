# Nachweise

Stand: 24.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

| Datei | Art | Was sie zeigt | Was sie **nicht** zeigt |
|---|---|---|---|
| [`validation-report.txt`](validation-report.txt) | automatisch (`scripts/validate.py`) | Schlüssel, Muster in allen Dateien, Struktur, Freigaben (S11), Absenderfilter (S12), Vergleich mit den privaten Exporten | spätere Änderungen; kein Beweis für das Fehlen sensibler Daten |
| [`validation-notes.md`](validation-notes.md) | manuell | Abdeckung und Wirksamkeit der Prüfung | – |
| [`import-test.md`](import-test.md) | Protokoll | Import aller 12 Workflows in n8n 2.43.7 | **Lokaler Import ≠ Funktionstest der Integrationen** |
| [`logic-test.md`](logic-test.md) | wiederholbar (`tests/logic-harness/`) | 10 Szenarien: Absenderfilter, Termin löschen, Gmail-Suche | Modell, Telegram-Freigabe, Google-APIs |
| [`live-test.md`](live-test.md) | Protokoll des Autors | Ergebnisse der Vorgängerfassung im privaten System | diese Fassung; keine öffentlichen Nachweise |

Ohne private Exporte kann jede Person prüfen: `python3 -I -B scripts/validate.py --repo .` und `bash tests/logic-harness/run.sh` (Docker).
