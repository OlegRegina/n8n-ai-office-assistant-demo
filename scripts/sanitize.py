#!/usr/bin/env python3
"""Bereinigt die privaten n8n-Exporte des KI-Büroassistenten (1 Haupt-Workflow + 11 Werkzeug-Workflows) für dieses Repository.

Aufruf:  python3 -I -B scripts/sanitize.py --source-dir <ordner mit den 12 privaten Exporten> --out workflows [--overwrite]

Grundsatz: nur die hier festgelegten Änderungen; jede Regel hat eine erwartete Anzahl (EXPECT). Weicht eine Zahl ab, tritt ein
unbekanntes Feld auf oder bleibt ein unerlaubter Wert stehen, bricht das Skript ab, bevor etwas geschrieben wird.
Das Skript enthält keine privaten Werte: Adressen, IDs und Namen werden über Regeln gefunden, nicht über gespeicherte Werte.

Regeln
  A1  Zugangsdaten-Verweise an Nodes entfernen                    A2  webhookId entfernen
  A3  Testdaten (pinData) entfernen                               A4  Verwaltungsfelder des Workflows entfernen (id, versionId,
                                                                      activeVersion mit Kopie aller Nodes, meta, shared, tags, Zeitstempel …)
  A5  Verweis auf den privaten Error-Workflow entfernen           A6  active = false, availableInMCP = false
  B1  Kalender (E-Mail-Adresse des Kontos) → primary              B2  Telegram-Benutzer-ID im Absenderfilter → Platzhalter
  B3  Workflow-IDs → feste Demo-IDs; Verweise der Werkzeug-Nodes (toolWorkflow) auf diese IDs
  B4  E-Mail-Adressen in den Beispielen der Gmail-Suche → anna.muster@example.com
  B5  Name in Signatur-Regeln → [Your Name]                       B6  Kürzel des Arbeitgebers im Kalender-Werkzeug entfernen
  B7  Name des Haupt-Workflows → «KI-Büroassistent (Demo)»
  B8  Verweis auf die n8n-Datentabelle (ID der Tabelle und des Projekts) → Platzhalter; der Tabellenname bleibt
  C1  Antwortsprache: «Always respond in Russian.» → Deutsch oder Englisch (Sprache der Nachricht)
  C2  russische Zeilen der Systemanweisung → Englisch/Deutsch (ausser den zwei Regeln für E-Mails auf Russisch: Grussformel «С уважением,» und neutrale Anrede «Здравствуйте,»)
  C3  russische Texte in Freigaben, Ergebnissen und Code-Kommentaren → Deutsch
  C4  Notizzettel (interne Entwicklungsnotizen, teils veraltet, mit Test-IDs) → kurze deutsche Beschreibung
"""
import argparse, copy, json, re, sys
from collections import Counter
from pathlib import Path

PLACEHOLDER_USER = "REPLACE_WITH_TELEGRAM_USER_ID"
PLACEHOLDER_TABLE = "REPLACE_WITH_DATA_TABLE_ID"
CALENDAR = "primary"
EXAMPLE_MAIL = "anna.muster@example.com"
MAIN_NAME = "KI-Büroassistent (Demo)"
CY = re.compile("[А-Яа-яЁё]")
MAIL = re.compile(r"[\w.+-]+(?:@|%40)[\w-]+\.[\w.-]+")

# Quellname → (Ausgabedatei, Demo-ID mit 16 Zeichen wie n8n)
FILES = {
    "🤖 03 — AI Operations Agent": ("ki-bueroassistent.json", "demoOfficeAgent1"),
    "📧TOOL — Gmail Search Messages": ("tools/gmail-search-messages.json", "demoGmailSearch1"),
    "📧TOOL — Gmail Read Message": ("tools/gmail-read-message.json", "demoGmailRead001"),
    "📧TOOL — Gmail Read Attachment": ("tools/gmail-read-attachment.json", "demoGmailAttach1"),
    "📧TOOL — Gmail Reply Draft V2": ("tools/gmail-reply-draft.json", "demoGmailReply01"),
    "📧TOOL — Gmail Create Draft — Single Attachment": ("tools/gmail-create-draft-single-attachment.json", "demoGmailDraft01"),
    "📧TOOL — Gmail Send Draft": ("tools/gmail-send-draft.json", "demoGmailSend001"),
    "📁TOOL — Drive Search": ("tools/drive-search.json", "demoDriveSearch1"),
    "📁TOOL — Drive Read": ("tools/drive-read.json", "demoDriveRead001"),
    "📅TOOL — Calendar Create Event": ("tools/calendar-create-event.json", "demoCalCreate001"),
    "📅TOOL — Calendar Update Event": ("tools/calendar-update-event.json", "demoCalUpdate001"),
    "📅TOOL — Calendar Delete Event": ("tools/calendar-delete-event.json", "demoCalDelete001"),
}
assert all(len(i) == 16 for _, i in FILES.values())

TOP_KEEP = ("name", "nodes", "connections", "settings")
SETTINGS_KEEP = {"executionOrder", "callerPolicy", "binaryMode", "availableInMCP"}
SETTINGS_DROP = {"errorWorkflow", "timeSavedMode"}
NODE_KEYS = {"id", "name", "type", "typeVersion", "position", "parameters", "alwaysOutputData", "retryOnFail", "waitBetweenTries",
             "maxTries", "executeOnce", "onError", "notesInFlow", "notes", "disabled"}
NODE_DROP = {"credentials", "webhookId"}

# C2 — Systemanweisung, zeilenweise (Muster ohne private Werte)
PROMPT_LINES = [
    ("C1", r"^Always respond in Russian\.$", "Respond in the language of the user's message: German or English. If the language is unclear, respond in German."),
    ("C2", r"^Для tools, которые уже защищены Human Approval, .*$",
     "For tools that are already protected by Human Approval, do NOT ask for confirmation in a plain text message beforehand."),
    ("C2", r'^Resolve relative dates \("[^"]+", "[^"]+"\) from the email\'s Date header,$',
     'Resolve relative dates ("morgen", "am Freitag") from the email\'s Date header,'),
    ("C2", r'^not just "Встреча"\.$', 'not just "Besprechung".'),
    ("C2", r'^If the user rejects an approval request, say it in natural words, for example: .*$',
     'If the user rejects an approval request, say it in natural words, for example: "Sie haben den Versand abgelehnt. Die E-Mail wurde nicht gesendet." Never say "vom Freigabesystem abgelehnt".'),
    ("B5", r'^(- Closing: "Freundliche Grüsse", then a new line with: )\S+$', r"\1[Your Name]"),
    ("B5", r'^(English emails: closing "Best regards," then a new line with: )\S+$', r"\1[Your Name]"),
    ("B5", r'^(Russian emails: closing "С уважением," then a new line with: )\S+$', r"\1[Your Name]"),
]
# erlaubte kyrillische Zeilen nach der Bereinigung (Regeln für E-Mails auf Russisch)
PROMPT_CYRILLIC_ALLOWED = [r'^Russian emails: closing "С уважением," then a new line with: \[Your Name\]$',
                           r'^Use a person\'s name in a greeting only if .*Russian "Здравствуйте,".*$']

# C3 — Textstellen in Parametern (Teilstrings; Muster ohne private Werte)
FRAGMENTS = [
    # Kalender-Werkzeug: Begriffe der Antwort (vorher Russisch); B6: Kürzel des Arbeitgebers entfällt
    ("B6", re.compile(r'- [A-Z]{4} / Dienst / Schicht / work shift → "рабочая смена"'), '- Dienst / Schicht / work shift → "Schicht"'),
    ("C3", '- Meeting / Besprechung / call → "встреча"', '- Meeting / Besprechung / call → "Besprechung"'),
    ("C3", '- Appointment / Termin → "запись" or "приём"', '- Appointment / Termin → "Termin"'),
    ("C3", '- If the type is unclear → use the neutral word "событие"', '- If the type is unclear → use the neutral word "Eintrag"'),
    # Freigaben (Telegram)
    ("C3", "'📅 Подтверждение изменения встречи\\n\\n'", "'📅 Termin ändern – Freigabe\\n\\n'"),
    ("C3", "'Инструмент: '", "'Werkzeug: '"),
    ("C3", "'Параметры:\\n'", "'Angaben:\\n'"),
    ("C3", "'Разрешить изменение встречи?'", "'Änderung freigeben?'"),
    ("C3", "'🗑️ УДАЛЕНИЕ СОБЫТИЯ\\n\\n'", "'🗑️ TERMIN LÖSCHEN\\n\\n'"),
    ("C3", "'AI Agent запрашивает разрешение удалить событие из Google Calendar.\\n\\n'", "'Der Assistent möchte einen Termin aus Google Calendar löschen.\\n\\n'"),
    ("C3", "'ID события: '", "'Termin-ID: '"),
    ("C3", "'Подтвердить удаление?'", "'Löschen freigeben?'"),
    ("C3", "'📅 Подтверждение создания события\\n\\n'", "'📅 Neuer Termin – Freigabe\\n\\n'"),
    ("C3", "'Название инструмента: '", "'Werkzeug: '"),
    ("C3", "'Параметры события:\\n'", "'Angaben zum Termin:\\n'"),
    ("C3", "'Разрешить создание события в Google Calendar?'", "'Termin in Google Calendar anlegen?'"),
    ("C3", "'📨 Подтверждение отправки письма\\n\\n'", "'📨 E-Mail senden – Freigabe\\n\\n'"),
    ("C3", "'ID черновика: '", "'Entwurf-ID: '"),
    ("C3", "'Разрешить отправку этого черновика?'", "'Diesen Entwurf senden?'"),
    # Werkzeug «Entwurf mit Anhang»: Empfänger «an mich»
    ("C3", 'If the user says "to myself" or "себе" without stating the address', 'If the user says "to myself" or "an mich" without stating the address'),
    # Ergebnisse an den Agenten
    ("C3", "Событие уже удалено. Повторное удаление не требуется.", "Der Termin ist bereits gelöscht. Erneutes Löschen ist nicht nötig."),
    ("C3", "'[ссылка]'", "'[Link]'"),
    ("C3", "Поиск не выполнен: поисковый запрос отсутствует.", "Suche nicht ausgeführt: Die Suchanfrage fehlt."),
    ("C3", "Черновик не создан. Необходимо указать получателя, тему и текст письма.", "Kein Entwurf erstellt. Empfänger, Betreff und Text der E-Mail sind nötig."),
    ("C3", "Черновик ответа создан. Письмо не отправлено.", "Antwortentwurf erstellt. Die E-Mail wurde nicht gesendet."),
    ("C3", "Новый черновик создан. Письмо не отправлено.", "Neuer Entwurf erstellt. Die E-Mail wurde nicht gesendet."),
    ("C3", "По указанному запросу письма Gmail не найдены.", "Zu dieser Suchanfrage wurden keine Gmail-Nachrichten gefunden."),
    # Code-Kommentare
    ("C3", "// Extract DOCX Text — достаём чистый текст из word/document.xml", "// Extract DOCX Text — reinen Text aus word/document.xml holen"),
    ("C3", "// лимит для AI Agent", "// Grenze für den KI-Agenten"),
    ("C3", "// 1. Читаем binary-файл как строку", "// 1. Binärdatei als Zeichenkette lesen"),
    ("C3", "// 2. Берём только видимый текст <w:t>, табы и переносы — по абзацам", "// 2. Nur sichtbaren Text <w:t>, Tabs und Umbrüche nehmen – absatzweise"),
    ("C3", "// 3. Пустой документ — честно сообщаем", "// 3. Leeres Dokument – ehrlich melden"),
    ("C3", "// 4. Возвращаем только JSON, binary дальше не передаём", "// 4. Nur JSON zurückgeben, Binärdaten nicht weitergeben"),
    ("C3", "// RESULT — DOCX Text: отдаём AI Agent только полезные поля", "// RESULT — DOCX Text: dem KI-Agenten nur die nützlichen Felder geben"),
    ("C3", "// RESULT — Unsupported Type: честный ответ агенту, если тип файла не поддержан", "// RESULT — Unsupported Type: ehrliche Antwort an den Agenten, wenn der Dateityp nicht unterstützt wird"),
    ("C3", "// RESULT — PDF Text: отдаём AI Agent те же 9 полей, что и для DOCX", "// RESULT — PDF Text: dem KI-Agenten dieselben 9 Felder wie bei DOCX geben"),
    ("C3", "// данные письма и вложения", "// Daten der E-Mail und des Anhangs"),
    ("C3", "// результат Extract from File", "// Ergebnis von Extract from File"),
    ("C3", "// Раскодирует MIME-слова в теме: =?UTF-8?B?...?= и =?UTF-8?Q?...?=", "// Dekodiert MIME-Wörter im Betreff: =?UTF-8?B?...?= und =?UTF-8?Q?...?="),
]
# Beschriftung der Freigabe-Knöpfe (Node → (Ja, Nein))
APPROVAL_LABELS = {
    "APPROVAL — Calendar Event1": ("✅ Termin ändern", "❌ Abbrechen"),
    "APPROVAL — Calendar Delete": ("🗑️ Termin löschen", "❌ Abbrechen"),
    "APPROVAL — Calendar Create": ("✅ Termin anlegen", "❌ Abbrechen"),
    "APPROVAL — Gmail Send": ("✅ E-Mail senden", "❌ Abbrechen"),
}
# C4 — Notizzettel (Workflow, Node) → neuer Inhalt
NOTES = {
    ("🤖 03 — AI Operations Agent", "Sticky Note"): """# KI-Büroassistent (Demo)

## Zweck
Assistent für Büroabläufe über Telegram: E-Mails suchen und lesen, Anhänge und Dokumente in Google Drive lesen, Antwortentwürfe schreiben, Termine verwalten.

## Ablauf
Telegram-Nachricht → Absenderfilter (nur die eingetragene Benutzer-ID) → KI-Agent wählt Werkzeuge → Antwort in Telegram.

## Freigabe
Senden einer E-Mail sowie Anlegen, Ändern und Löschen von Terminen laufen nur über einen Freigabe-Schritt in Telegram. Ohne Ihr Ja geschieht nichts davon.

## Sicherheit
Inhalte von E-Mails, Anhängen und Dokumenten sind fremder Text. Die Systemanweisung verbietet, Anweisungen daraus zu befolgen – garantiert ist das nicht (siehe SECURITY.md).""",
    ("🤖 03 — AI Operations Agent", "Sticky Note1"): """## Google Drive
drive_search_files sucht Dateien, drive_read_document liest ein Dokument.
Nur lesend: Es wird keine Datei angelegt, geändert oder gelöscht.""",
    ("📅TOOL — Calendar Delete Event", "Sticky Note"): """# Werkzeug: Termin löschen
Wird erst nach der Freigabe in Telegram aufgerufen (APPROVAL — Calendar Delete).

Eingabe: event_id
Ablauf: Termin lesen → nur einen aktiven Termin löschen → Ergebnis an den Assistenten.
Ein bereits gelöschter Termin wird nicht erneut gelöscht.""",
    ("📅TOOL — Calendar Update Event", "Sticky Note"): """# Werkzeug: Termin ändern
Wird erst nach der Freigabe in Telegram aufgerufen (APPROVAL — Calendar Event1).

Eingabe: event_id, title, start, end
Ausgabe: success, event_id, title, start, end, link
Ändert der Nutzer nur die Zeit, sollen die übrigen Angaben des Termins erhalten bleiben.""",
    ("📁TOOL — Drive Read", "Sticky Note"): """# Werkzeug: Dokument aus Google Drive lesen
Eingabe: file_id
Ablauf: Datei laden → Google Docs bei Bedarf als PDF → Text auslesen → nur Text und Seitenzahl an den Assistenten.
Ausgabe: text, pages
Tabellen und Präsentationen werden nicht unterstützt. Nur lesend.""",
    ("📁TOOL — Drive Search", "Sticky Note"): """# Werkzeug: Suche in Google Drive
Eingabe: query (Name oder Teil des Namens)
Suche über die Google-Drive-API nach dem Dateinamen: PDF und Google Docs, ohne Papierkorb.
Ausgabe: id, name, mimeType, webViewLink
Leere Anfrage → Meldung EMPTY_QUERY. Nur lesend.""",
    ("📧TOOL — Gmail Create Draft — Single Attachment", "Sticky Note"): """# Werkzeug: Neuer E-Mail-Entwurf mit einem Anhang
Erstellt einen Entwurf in Gmail, optional mit einer Datei aus Google Drive als Anhang.
Gesendet wird nichts: Senden nur über gmail_send_draft nach Freigabe in Telegram.""",
    ("📧TOOL — Gmail Read Attachment", "Sticky Note1"): """# Werkzeug: Anhang einer E-Mail lesen
Eingabe: message_id, attachment_index
Ablauf: E-Mail mit Anhängen laden → gewünschten Anhang wählen → DOCX (Text aus word/document.xml) oder PDF (Text auslesen); andere Typen → Meldung «nicht unterstützt».
Ausgabe: success, message_id, attachment_index, filename, mime_type, text (höchstens 8000 Zeichen), char_count, truncated, error
Nur lesend: Es werden keine Dateien angelegt.""",
    ("📧TOOL — Gmail Read Message", "Sticky Note"): """# Werkzeug: E-Mail lesen
Eingabe: message_id
Ausgabe: die wichtigsten Felder der E-Mail und ihr Text (Links als [Link], höchstens 6000 Zeichen).
Nur lesend.""",
    ("📧TOOL — Gmail Reply Draft V2", "Sticky Note"): """# Werkzeug: Antwortentwurf
Eingabe: to, subject, body, thread_id (optional)
Mit thread_id: Entwurf als Antwort in der bestehenden Unterhaltung; ohne: neuer Entwurf.
Fehlen Pflichtangaben, wird nichts erstellt. Gesendet wird nichts.""",
    ("📧TOOL — Gmail Reply Draft V2", "Sticky Note1"): """Senden ist nur über gmail_send_draft nach Freigabe in Telegram möglich.""",
    ("📧TOOL — Gmail Search Messages", "Sticky Note1"): """# Werkzeug: Suche in Gmail
Eingabe: query (Gmail-Suchsyntax, z. B. from:anna.muster@example.com newer_than:7d)
Gesucht wird in allen Ordnern (in:anywhere). Leere Anfrage oder keine Treffer → klare Meldung an den Assistenten.
Nur lesend.""",
    ("📧TOOL — Gmail Send Draft", "Sticky Note"): """# Werkzeug: Entwurf senden
Sendet einen bestehenden Gmail-Entwurf über seine draft_id (drafts.send); Anhänge bleiben erhalten.
Wird nur nach der Freigabe in Telegram aufgerufen (APPROVAL — Gmail Send). Ohne Ihr Ja wird nichts gesendet.""",
}

EXPECT = {"A1": 25, "A2": 13, "A3": 5, "A5": 1, "B1": 6, "B2": 1, "B3": 11, "B4": 2, "B5": 4, "B6": 1, "B7": 1, "B8": 2,
          "C1": 1, "C2": 4, "C3": 39, "C4": 13, "labels": 8}


def walk_set(o, fn):
    """Wendet fn auf jeden String an (gibt neuen Wert zurück)."""
    if isinstance(o, dict): return {k: walk_set(v, fn) for k, v in o.items()}
    if isinstance(o, list): return [walk_set(v, fn) for v in o]
    if isinstance(o, str): return fn(o)
    return o


def strings(o):
    if isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)
    elif isinstance(o, str): yield o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", required=True); ap.add_argument("--out", required=True); ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    src = {}
    for f in sorted(Path(a.source_dir).glob("*.json")):
        w = json.load(open(f, encoding="utf-8"))
        if w.get("name") in FILES: src[w["name"]] = w
    missing = sorted(set(FILES) - set(src))
    if missing: sys.exit(f"ABBRUCH: Quelle fehlt: {missing}")
    idmap = {src[n]["id"]: FILES[n][1] for n in FILES}
    c = Counter(); out = {}; per_frag = Counter()
    for name, w in src.items():
        w = copy.deepcopy(w)
        # A4 / A3 / A6 / B7
        if w.get("pinData"): c["A3"] += len(w["pinData"])
        nw = {k: w[k] for k in TOP_KEEP}
        nw["id"] = FILES[name][1]
        if name == "🤖 03 — AI Operations Agent": nw["name"] = MAIN_NAME; c["B7"] += 1
        st = dict(w.get("settings") or {})
        unknown = set(st) - SETTINGS_KEEP - SETTINGS_DROP
        if unknown: sys.exit(f"ABBRUCH: unbekannte settings in {name}: {unknown}")
        if st.get("errorWorkflow"): c["A5"] += 1
        nw["settings"] = {k: v for k, v in st.items() if k in SETTINGS_KEEP}
        nw["settings"]["availableInMCP"] = False
        nw["pinData"] = {}; nw["active"] = False
        nodes = []
        for n in w["nodes"]:
            unknown = set(n) - NODE_KEYS - NODE_DROP
            if unknown: sys.exit(f"ABBRUCH: unbekannte Node-Felder in {name}/{n['name']}: {unknown}")
            if n.get("credentials"): c["A1"] += len(n["credentials"])
            if n.get("webhookId"): c["A2"] += 1
            n = {k: v for k, v in n.items() if k in NODE_KEYS}
            p = n.get("parameters", {})
            t = n["type"]
            # B1 Kalender
            if isinstance(p.get("calendar"), dict) and MAIL.search(json.dumps(p["calendar"])):
                p["calendar"] = {"__rl": True, "value": CALENDAR, "mode": p["calendar"].get("mode", "list"), "cachedResultName": CALENDAR}; c["B1"] += 1
            # B2 Absenderfilter
            if n["name"] == "IF — Allowed Sender?" and t.endswith(".if"):
                for cond in p["conditions"]["conditions"]: cond["rightValue"] = PLACEHOLDER_USER; c["B2"] += 1
            # B8 n8n-Datentabelle
            if t.endswith("dataTable") and isinstance(p.get("dataTableId"), dict):
                d = p["dataTableId"]
                p["dataTableId"] = {"__rl": True, "value": PLACEHOLDER_TABLE, "mode": d.get("mode", "list"), "cachedResultName": d.get("cachedResultName")}; c["B8"] += 1
            # B3 Verweise auf Werkzeug-Workflows
            if t.endswith("toolWorkflow"):
                ref = p["workflowId"]; new = idmap.get(ref.get("value"))
                if not new: sys.exit(f"ABBRUCH: unbekannter Werkzeug-Verweis in {n['name']}")
                p["workflowId"] = {"__rl": True, "value": new, "mode": ref.get("mode", "list"), "cachedResultName": ref.get("cachedResultName"), "cachedResultUrl": f"/workflow/{new}"}; c["B3"] += 1
            # B4 E-Mail im Beispiel der Gmail-Suche (nur Beschreibung des Werkzeugs)
            if t.endswith("toolWorkflow") and n["name"] == "gmail_search_messages":
                def ex(s):
                    k = len([m for m in MAIL.findall(s) if not m.lower().endswith("@example.com")]); c["B4"] += k
                    return MAIL.sub(lambda m: m.group(0) if m.group(0).lower().endswith("@example.com") else EXAMPLE_MAIL, s)
                p = n["parameters"] = walk_set(p, ex)
            # B5 Name im Signatur-Hinweis des Werkzeugs «Entwurf mit Anhang»
            if t.endswith("toolWorkflow") and n["name"] == "gmail_create_draft_single":
                body = p.get("workflowInputs", {}).get("value", {}).get("body", "")
                if re.search(r'on a new line "[^"\[]+"\.', body):
                    p["workflowInputs"]["value"]["body"] = re.sub(r'(on a new line ")[^"\[]+("\.)', r"\1[Your Name]\2", body, count=1); c["B5"] += 1
            # Freigabe-Knöpfe
            if t.endswith("telegramHitlTool") and n["name"] in APPROVAL_LABELS:
                v = p["approvalOptions"]["values"]; ja, nein = APPROVAL_LABELS[n["name"]]
                v["approveLabel"], v["disapproveLabel"] = ja, nein; c["labels"] += 2
            # C4 Notizzettel
            if t.endswith("stickyNote"):
                key = (name, n["name"])
                if key not in NOTES: sys.exit(f"ABBRUCH: Notiz ohne neue Fassung: {key}")
                p["content"] = NOTES[key]; c["C4"] += 1
            # C1/C2/B5 Systemanweisung
            if t.endswith(".agent"):
                lines = p["options"]["systemMessage"].split("\n")
                for rule, pat, rep in PROMPT_LINES:
                    hit = [i for i, l in enumerate(lines) if re.match(pat, l)]
                    if len(hit) != 1: sys.exit(f"ABBRUCH: Zeile für {rule} nicht eindeutig ({len(hit)}): {pat[:50]}")
                    lines[hit[0]] = re.sub(pat, rep, lines[hit[0]]); c[rule] += 1
                p["options"]["systemMessage"] = "\n".join(lines)
            # C3/B6 Textstellen
            def frag(s):
                for rule, old, new in FRAGMENTS:
                    if isinstance(old, re.Pattern):
                        k = len(old.findall(s)); s = old.sub(new, s)
                    else:
                        k = s.count(old); s = s.replace(old, new)
                    c[rule] += k; per_frag[FRAGMENTS.index((rule, old, new))] += k
                return s
            n["parameters"] = walk_set(p, frag)
            nodes.append(n)
        nw["nodes"] = nodes
        out[name] = nw
    # Zählungen
    unused = [FRAGMENTS[i][1] if isinstance(FRAGMENTS[i][1], str) else FRAGMENTS[i][1].pattern for i in range(len(FRAGMENTS)) if per_frag[i] == 0]
    if unused: sys.exit(f"ABBRUCH: Textstelle nicht gefunden: {unused[:3]}")
    bad = {k: (c.get(k, 0), v) for k, v in EXPECT.items() if c.get(k, 0) != v}
    print("Änderungen je Regel:", ", ".join(f"{k}={c.get(k, 0)}" for k in EXPECT))
    if bad: sys.exit(f"ABBRUCH: Anzahl weicht ab (ist, erwartet): {bad}")
    # Endkontrolle: keine fremden Adressen, kein Kyrillisch ausser den erlaubten Zeilen, kein Kürzel, keine Quell-IDs
    for name, w in out.items():
        for s in strings(w):
            for m in MAIL.findall(s):
                if not m.lower().endswith("@example.com"): sys.exit(f"ABBRUCH: E-Mail-Adresse übrig in {name}")
            for line in s.split("\n"):
                if CY.search(line) and not any(re.match(p, line) for p in PROMPT_CYRILLIC_ALLOWED):
                    sys.exit(f"ABBRUCH: kyrillischer Text übrig in {name}: {line[:60]}")
            if any(i in s for i in idmap): sys.exit(f"ABBRUCH: Quell-ID übrig in {name}")
            if re.search(r"\b[A-Z]{4} / Dienst\b", s): sys.exit("ABBRUCH: Kürzel im Kalender-Werkzeug übrig")
            if "/projects/" in s or "/datatables/" in s: sys.exit(f"ABBRUCH: Verweis auf die private n8n-Instanz übrig in {name}")
    outdir = Path(a.out)
    targets = {name: outdir / FILES[name][0] for name in out}
    exist = [str(p) for p in targets.values() if p.exists()]
    if exist and not a.overwrite: sys.exit(f"ABBRUCH: existiert bereits (--overwrite?): {exist[:3]}")
    for name, w in out.items():
        targets[name].parent.mkdir(parents=True, exist_ok=True)
        targets[name].write_text(json.dumps(w, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(out)} Workflows → {outdir}")


if __name__ == "__main__":
    main()
