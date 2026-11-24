#!/usr/bin/env python3
"""Prüft dieses Repository (KI-Büroassistent, 12 Workflows) vor einer Veröffentlichung.

Aufruf (ohne private Daten, für alle):
  python3 -I -B scripts/validate.py --repo .
Aufruf (Autor, mit privaten Exporten und persönlichen Suchbegriffen):
  python3 -I -B scripts/validate.py --repo . --source-dir <ordner> --deny <wort> [--deny …] --report evidence/validation-report.txt --overwrite

Prüfungen
  S2b  keine Datei im Repository ist identisch mit einem privaten Export                      (nur mit --source-dir)
  S3   erlaubte Schlüssel: Workflow, settings, Nodes; keine Zugangsdaten, keine webhookId, keine Testdaten
  S4   Werte aus den privaten Exporten (E-Mail-Adressen, Workflow-, Tabellen- und Projekt-IDs, Telegram-ID,
       Namen in Signaturen, Kürzel) kommen in keiner Datei vor; Werte werden nie ausgegeben       (nur mit --source-dir)
  S5   Musterprüfung aller Dateien: E-Mail-Adressen ausser example.com, Links ausserhalb der Liste, Nummern ab 7 Ziffern,
       Schlüssel und Tokens, IPv4, n8n-ähnliche IDs (16 Zeichen) ausser den Demo-IDs, Kyrillisch ausser den zwei erlaubten
       Zeilen, persönliche Suchbegriffe (--deny, als ganzes Wort, Gross-/Kleinschreibung egal)
  S6   Struktur: erwartete Zahl von Nodes und Verbindungen je Workflow; Verbindungen und $('Node')-Verweise zeigen auf
       vorhandene Nodes; Werkzeug-Verweise zeigen auf Workflows dieses Repositorys
  S7   die Workflows sind genau das Ergebnis von scripts/sanitize.py auf den privaten Exporten     (nur mit --source-dir)
  S8   active = false, availableInMCP = false
  S9   Platzhalter und Kalender: 1× Telegram-ID, 2× Datentabelle, 6× Kalender primary
  S10  Testdaten sind als synthetisch markiert, eindeutige IDs, nur example.com
  S11  Freigabe: Werkzeuge, die senden oder Termine anlegen/ändern/löschen, hängen nur über einen Freigabe-Node
       (telegramHitlTool) am Agenten; Kalender-Werkzeuge direkt am Agenten nur lesend
  S12  Absenderfilter: Trigger → «IF — Allowed Sender?» → Rest; der Ausgang für fremde Absender ist leer
Exit 1 bei einem Fehler. Automatische Prüfungen sind kein Beweis, dass keine sensiblen Daten mehr enthalten sind.
"""
import argparse, datetime, hashlib, json, re, subprocess, sys, tempfile
from pathlib import Path

EXPECT = {  # Datei → (Nodes, Verbindungen)
    "workflows/ki-bueroassistent.json": (26, 23),
    "workflows/tools/gmail-search-messages.json": (8, 6), "workflows/tools/gmail-read-message.json": (7, 5),
    "workflows/tools/gmail-read-attachment.json": (18, 16), "workflows/tools/gmail-reply-draft.json": (14, 12),
    "workflows/tools/gmail-create-draft-single-attachment.json": (10, 8), "workflows/tools/gmail-send-draft.json": (3, 1),
    "workflows/tools/drive-search.json": (6, 4), "workflows/tools/drive-read.json": (5, 3),
    "workflows/tools/calendar-create-event.json": (3, 2), "workflows/tools/calendar-update-event.json": (4, 2),
    "workflows/tools/calendar-delete-event.json": (7, 5),
}
DEMO_ID = re.compile(r"^demo[A-Za-z0-9]{12}$")
TOP_KEYS = {"id", "name", "nodes", "connections", "settings", "pinData", "active"}
SETTINGS_KEYS = {"executionOrder", "callerPolicy", "binaryMode", "availableInMCP"}
NODE_KEYS = {"id", "name", "type", "typeVersion", "position", "parameters", "alwaysOutputData", "retryOnFail", "waitBetweenTries",
             "maxTries", "executeOnce", "onError", "notesInFlow", "notes", "disabled"}
URL_HOSTS = {"gmail.googleapis.com", "www.googleapis.com", "github.com", "example.com", "docs.n8n.io", "n8n.io", "opensource.org"}
CY = re.compile("[А-Яа-яЁё]")
CY_ALLOWED = [re.compile(r'Russian emails: closing "С уважением," then a new line with: \[Your Name\]'),
              re.compile(r'Russian "Здравствуйте,", German exactly "Guten Tag,"')]
PATTERNS = {
    "e-mail outside example.com": re.compile(r"[\w.+-]+(?:@|%40)(?!example\.com\b)[\w-]+\.[a-z]{2,}", re.I),
    "number with 7+ digits": re.compile(r"(?<![\w.-])\d{7,}(?![\w-])"),
    "openai-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    "github token": re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{16,}"),
    "slack/google key": re.compile(r"\b(?:xox[abp]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{30,})"),
    "jwt-like token": re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),
    "telegram bot token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}"),
    "IPv4 address": re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"),
}
ID16 = re.compile(r"(?<![\w-])[A-Za-z0-9]{16}(?![\w-])")
# Feldnamen von n8n mit 16 Zeichen (keine IDs)
ID16_WORDS = {"alwaysOutputData", "cachedResultName", "telegramHitlTool", "waitBetweenTries", "additionalFields", "canBeUsedToMatch"}
# Kyrillisch ist in den Regeln der Bereinigung und Prüfung nötig (ursprüngliche Textstellen, keine personenbezogenen Daten)
CY_FILES_ALLOWED = {"scripts/sanitize.py", "scripts/validate.py"}


class Report:
    def __init__(self): self.lines = []; self.fail = 0
    def add(self, ok, code, text):
        self.lines.append(f"{'PASS' if ok else 'FAIL':6s}  {code:4s}  {text}"); self.fail += (not ok)


def strings(o):
    if isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)
    elif isinstance(o, str): yield o


def repo_files(repo):
    return sorted(p for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts and p.name != ".DS_Store")


def edges(w): return sum(len(t) for v in w["connections"].values() for o in v.values() for t in o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="."); ap.add_argument("--source-dir"); ap.add_argument("--deny", action="append", default=[])
    ap.add_argument("--report"); ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo).resolve(); r = Report()
    files = repo_files(repo)
    wf = {str(p.relative_to(repo)): json.load(open(p, encoding="utf-8")) for p in files if p.parts[-2] in ("workflows", "tools") and p.suffix == ".json" and "workflows" in p.parts}
    ids = {w["id"]: k for k, w in wf.items()}

    # S3
    probs = []
    for k, w in wf.items():
        if set(w) - TOP_KEYS: probs.append(f"{k}: top {sorted(set(w) - TOP_KEYS)}")
        if set(w.get("settings", {})) - SETTINGS_KEYS: probs.append(f"{k}: settings {sorted(set(w['settings']) - SETTINGS_KEYS)}")
        if w.get("pinData"): probs.append(f"{k}: pinData")
        for n in w["nodes"]:
            extra = set(n) - NODE_KEYS
            if extra: probs.append(f"{k}: node '{n['name']}' keys {sorted(extra)}")
    r.add(not probs, "S3", "allowlist of keys respected (no credentials, webhookId, pinData)" if not probs else f"problems: {probs[:4]}")

    # S6
    probs = []
    for k, (nn, ne) in EXPECT.items():
        w = wf.get(k)
        if not w: probs.append(f"missing {k}"); continue
        if (len(w["nodes"]), edges(w)) != (nn, ne): probs.append(f"{k}: nodes/edges {len(w['nodes'])}/{edges(w)} expected {nn}/{ne}")
        names = {n["name"] for n in w["nodes"]}
        for src, v in w["connections"].items():
            if src not in names: probs.append(f"{k}: connection from unknown '{src}'")
            for outs in v.values():
                for o in outs:
                    for t in o:
                        if t["node"] not in names: probs.append(f"{k}: connection to unknown '{t['node']}'")
        for s in strings(w["nodes"]):
            for ref in re.findall(r"\$\('([^']+)'\)", s):
                if ref not in names: probs.append(f"{k}: $('{ref}') unresolved")
        for n in w["nodes"]:
            if n["type"].endswith("toolWorkflow") and n["parameters"]["workflowId"]["value"] not in ids:
                probs.append(f"{k}: tool '{n['name']}' points outside the repository")
    if set(wf) - set(EXPECT): probs.append(f"unexpected workflow files {sorted(set(wf) - set(EXPECT))}")
    tot_n = sum(len(w["nodes"]) for w in wf.values()); tot_e = sum(edges(w) for w in wf.values())
    r.add(not probs, "S6", f"{len(wf)} workflows, nodes {tot_n}, edges {tot_e}; connections, $('…') references and tool references resolved" if not probs else f"problems: {probs[:4]}")

    # S8
    bad = [k for k, w in wf.items() if w.get("active") is not False or w.get("settings", {}).get("availableInMCP") is not False]
    r.add(not bad, "S8", "active=false, availableInMCP=false in all workflows" if not bad else f"flags wrong in {bad}")

    # S9
    allw = "\n".join(json.dumps(w, ensure_ascii=False) for w in wf.values())
    cal = sum(1 for w in wf.values() for n in w["nodes"] if isinstance(n["parameters"].get("calendar"), dict) and n["parameters"]["calendar"].get("value") == "primary")
    cnt = (allw.count("REPLACE_WITH_TELEGRAM_USER_ID"), allw.count("REPLACE_WITH_DATA_TABLE_ID"), cal)
    other_ph = sorted(set(re.findall(r"REPLACE_WITH_[A-Z_]+", allw)) - {"REPLACE_WITH_TELEGRAM_USER_ID", "REPLACE_WITH_DATA_TABLE_ID"})
    r.add(cnt == (1, 2, 6) and not other_ph, "S9", f"placeholders telegram/table/calendar = {cnt[0]}/{cnt[1]}/{cnt[2]} (expected 1/2/6)" + (f"; unknown {other_ph}" if other_ph else ""))

    # S11 Freigabe
    main_w = wf["workflows/ki-bueroassistent.json"]; nodes = {n["name"]: n for n in main_w["nodes"]}
    agent = next(n["name"] for n in main_w["nodes"] if n["type"].endswith(".agent"))
    tool_to = {}
    for src, v in main_w["connections"].items():
        for o in v.get("ai_tool", []):
            for t in o: tool_to.setdefault(src, []).append(t["node"])
    def writes(target):
        w = wf[ids[target]]; ops = []
        for n in w["nodes"]:
            p = n["parameters"]; t = n["type"]
            if t.endswith("googleCalendar") and p.get("operation") in (None, "create", "update", "delete"): ops.append(f"calendar:{p.get('operation') or 'create'}")
            if t.endswith("httpRequest") and str(p.get("method", "GET")).upper() != "GET": ops.append(f"http:{p.get('method')}")
            if t.endswith("gmail") and p.get("operation") in ("send", "delete", "reply"): ops.append(f"gmail:{p.get('operation')}")
        return ops
    probs, gated, direct = [], [], []
    for name, n in nodes.items():
        if n["type"].endswith("toolWorkflow"):
            w_ops = writes(n["parameters"]["workflowId"]["value"]); dests = tool_to.get(name, [])
            if w_ops:
                ok = dests and all(nodes[d]["type"].endswith("telegramHitlTool") and tool_to.get(d) == [agent] for d in dests)
                (gated if ok else probs).append(f"{name} {w_ops}")
            else:
                if dests != [agent]: probs.append(f"{name}: read tool not wired to agent")
                direct.append(name)
        if n["type"].endswith("googleCalendarTool"):
            op = n["parameters"].get("operation")
            if op not in ("getAll", None) or (op is None and n["parameters"].get("resource") != "calendar"): probs.append(f"{name}: calendar tool on agent is not read-only ({op})")
    r.add(not probs and len(gated) == 4, "S11", f"{len(gated)} writing tools behind approval ({', '.join(g.split(' ')[0] for g in gated)}); {len(direct)} read/draft tools direct" if not probs else f"problems: {probs[:4]}")

    # S12 Absenderfilter
    C = main_w["connections"]; trig = next(n["name"] for n in main_w["nodes"] if n["type"].endswith("telegramTrigger"))
    out = [t["node"] for o in C.get(trig, {}).get("main", []) for t in o]
    f = nodes.get("IF — Allowed Sender?"); ok = out == ["IF — Allowed Sender?"] and f is not None
    if ok:
        cond = f["parameters"]["conditions"]["conditions"]; fm = C["IF — Allowed Sender?"]["main"]
        ok = (len(cond) == 1 and "message?.from?.id" in cond[0]["leftValue"] and "callback_query?.from?.id" in cond[0]["leftValue"]
              and cond[0]["rightValue"] == "REPLACE_WITH_TELEGRAM_USER_ID" and len(fm[0]) >= 1 and (len(fm) < 2 or not fm[1]))
    r.add(ok, "S12", "sender filter directly after the Telegram trigger; foreign senders end without output" if ok else f"sender filter wrong (trigger → {out})")

    # S5 Muster in allen Dateien
    deny_rx = [re.compile(rf"(?<!\w){re.escape(d)}(?!\w)", re.IGNORECASE) for d in a.deny if d]
    findings = {}
    for p in files:
        rel = str(p.relative_to(repo))
        try: text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError: findings.setdefault(rel, []).append("binary file"); continue
        if rel == "evidence/validation-report.txt": continue
        hits = [k for k, rx in PATTERNS.items() if rx.search(text)]
        for h in re.findall(r"https?://([^/\s\"')>\]]+)", text):
            if h.lower() not in URL_HOSTS: hits.append(f"link host {h}")
        for m in ID16.findall(text):
            if not DEMO_ID.match(m) and m not in ID16_WORDS and not re.match(r"^[A-Z][a-z]{15}$", m) and re.search(r"[a-z]", m) and re.search(r"[A-Z]", m):
                hits.append("16-character id-like value")  # deutsche Wörter mit 16 Buchstaben (z. B. «Eigenentwicklung») sind ausgenommen
        if rel in CY_FILES_ALLOWED: lines = []
        elif p.suffix == ".json": lines = [l for st in strings(json.loads(text)) for l in st.split("\n")]
        else: lines = text.split("\n")
        for line in lines:
            if CY.search(line) and not any(rx.search(line) for rx in CY_ALLOWED): hits.append("cyrillic text"); break
        # als ganzes Wort, wie im Kalender-Demo: der öffentliche GitHub-Login in LICENSE enthält den Vornamen als Wortteil
        if any(rx.search(text) for rx in deny_rx): hits.append("personal deny token")
        if hits: findings[rel] = sorted(set(hits))
    r.add(not findings, "S5", f"pattern scan of {len(files)} files; " + ("no findings" if not findings else f"findings: {findings}"))

    # S10 Testdaten
    td = repo / "test-data" / "synthetic-messages.json"
    if td.exists():
        d = json.load(open(td, encoding="utf-8")); probs = []
        if d.get("synthetic") is not True: probs.append("file not flagged synthetic")
        idl = [m.get("id") for m in d.get("messages", [])]
        if len(idl) != len(set(idl)): probs.append("duplicate ids")
        r.add(not probs, "S10", f"{len(idl)} synthetic messages; flagged synthetic, unique ids, example.com only" if not probs else f"problems: {probs}")
    else:
        r.add(False, "S10", "test-data/synthetic-messages.json missing")

    # mit privaten Exporten
    if a.source_dir:
        srcs = sorted(Path(a.source_dir).glob("*.json"))
        hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in srcs}
        same = [str(p.relative_to(repo)) for p in files if hashlib.sha256(p.read_bytes()).hexdigest() in hashes]
        r.add(not same, "S2b", f"repository files identical to a private source: {len(same)}")
        vals = set()
        for p in srcs:
            w = json.load(open(p, encoding="utf-8")); s_all = json.dumps(w, ensure_ascii=False)
            vals |= {m for m in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", s_all) if not m.endswith("@example.com")}
            vals.add(w.get("id", ""))
            vals |= set(re.findall(r"/projects/([A-Za-z0-9]+)/datatables/([A-Za-z0-9]+)", s_all)[0]) if "/datatables/" in s_all else set()
            vals |= set(re.findall(r"\b([A-Z]{4}) / Dienst\b", s_all))
            vals |= set(re.findall(r"then a new line with: ([^\s\\\"\[]+)", s_all))
            for n in w["nodes"]:
                if n["name"] == "IF — Allowed Sender?":
                    vals |= {str(c["rightValue"]) for c in n["parameters"]["conditions"]["conditions"]}
        vals = {v for v in vals if v and len(v) >= 4}
        found = {}
        for p in files:
            try: text = p.read_text(encoding="utf-8").lower()
            except UnicodeDecodeError: continue
            k = sum(1 for v in vals if re.search(r"(?<![a-z0-9])" + re.escape(v.lower()) + r"(?![a-z0-9])", text))
            if k: found[str(p.relative_to(repo))] = k
        r.add(not found, "S4", f"{len(vals)} source values checked in {len(files)} files; " + ("none found" if not found else f"found in {found} (values not shown)"))
        with tempfile.TemporaryDirectory() as tmp:
            res = subprocess.run([sys.executable, "-I", "-B", str(repo / "scripts" / "sanitize.py"), "--source-dir", a.source_dir, "--out", tmp], capture_output=True, text=True)
            diff = []
            if res.returncode: diff.append("sanitize.py failed")
            else:
                for k in EXPECT:
                    gen = Path(tmp) / k.replace("workflows/", "", 1)
                    if not gen.exists() or gen.read_bytes() != (repo / k).read_bytes(): diff.append(k)
            r.add(not diff, "S7", "workflows are exactly the output of scripts/sanitize.py on the private sources" if not diff else f"differs: {diff[:4]}")

    head = ["Office Assistant Demo - validation report", f"generated: {datetime.datetime.now():%Y-%m-%d %H:%M}", "tool: scripts/validate.py",
            f"workflows: {len(wf)} files in workflows/", f"private sources: {'provided for comparison (not part of this repository; paths and hashes not recorded)' if a.source_dir else 'not provided (S2b, S4, S7 skipped)'}",
            f"personal deny tokens: {len([d for d in a.deny if d])} provided (values not recorded)",
            "note: automatic checks are not proof that no sensitive data remains; a manual review is required.", ""]
    text = "\n".join(head + r.lines + ["", f"result: {'PASS' if not r.fail else 'FAIL'} ({r.fail} failed checks)"]) + "\n"
    print(text)
    if a.report:
        rp = Path(a.report)
        if rp.exists() and not a.overwrite: sys.exit("report exists (use --overwrite)")
        rp.write_text(text, encoding="utf-8")
    sys.exit(1 if r.fail else 0)


if __name__ == "__main__":
    main()
