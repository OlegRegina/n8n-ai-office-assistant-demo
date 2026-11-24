# Live-Tests im privaten System des Autors

Stand: 24.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

> Angaben aus dem Projektprotokoll des Autors zu Tests im eigenen n8n mit Test-E-Mails, Test-Dokumenten und Test-Terminen. **Öffentliche Nachweise gibt es dafür nicht.** Getestet wurde die **Vorgängerfassung**: Antworten auf Russisch, Freigabe-Texte auf Russisch, **ohne Absenderfilter**. In dieser Demo wurde nichts gegen echte Dienste ausgeführt.

| Datum | Ablauf | Ergebnis laut Protokoll |
|---|---|---|
| vor dem 17.11.2026 (Datum im Protokoll nicht angegeben) | Termin anlegen, ändern, löschen über Telegram, je nach Freigabe | bestanden |
| 14.10.2026 | Golden Test Gmail + Kalender (E-Mail suchen und lesen, Kalender lesen, Antwort in Telegram) | bestanden |
| 17.10.2026 | DOCX-Anhang lesen (Einzelschritt mit festen Testdaten, nicht vom Agenten aufgerufen) | bestanden: Text extrahiert, auf 8000 Zeichen gekürzt |
| 17.11.2026 | Golden Test: Telegram → Gmail suchen und lesen → Drive-Dokument finden → Entwurf mit PDF-Anhang → Freigabe über Link → gesendet; Gegenprobe «Ablehnen» → nicht gesendet | bestanden; im Gmail-Postfach geprüft (Entwurf mit Anhang, danach unter «Gesendet») |
| 22.11.2026 | Entwurf an Test-Adresse mit Anhang | bestanden: draft_id, Empfänger, Betreff und Anhang gemeldet; Grussformel einmal |

## Was daraus folgt

- Die Kernabläufe (Lesen, Entwurf mit Anhang, Senden nur nach Freigabe, Ablehnen) sind in der Vorgängerfassung belegt.
- Nicht belegt sind diese Fassung (Deutsch/Englisch, Absenderfilter), die Abweisung fremder Konten, Prompt Injection und die Freigabe-Knöpfe direkt im Chat (dort im privaten System ohne Reaktion, siehe E3).
