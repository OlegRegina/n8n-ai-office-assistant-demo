#!/usr/bin/env python3
"""Prüft die Läufe des Logiktests:  python3 -I -B verify.py <ordner-mit-den-Läufen>"""
import json, sys
from pathlib import Path
run = Path(sys.argv[1]); rows = []; ok = 0
def load(name):
    raw = (run / f"{name}.json").read_text(encoding="utf-8"); j = json.loads(raw[raw.index("{"):])
    rd = j["data"]["resultData"]["runData"]
    def out(node):
        r = rd.get(node)
        return [it["json"] for br in r[0]["data"]["main"] if br for it in br] if r else None
    return out, j["data"]["resultData"].get("error")
def rec(name, good, info):
    global ok; ok += bool(good); rows.append(f"{'PASS' if good else 'FAIL'} {name} | {info}")
for name, want in (("F1_eigene_Nachricht", "Weiter zum Agenten"), ("F2_fremde_Nachricht", "Ignoriert"), ("F3_fremder_Knopf", "Ignoriert"),
                   ("F4_eigener_Knopf", "Weiter zum Agenten"), ("F5_ohne_Absender", "Ignoriert")):
    out, err = load(name); got = [n for n in ("Weiter zum Agenten", "Ignoriert") if out(n) is not None]
    rec(name, not err and got == [want], f"→ {got}")
out, err = load("D1_aktiver_Termin"); r = out("SET — Return Delete Result")
rec("D1_aktiver_Termin", not err and out("GOOGLE CALENDAR — Delete Event") is not None and r and r[0].get("success") is True and out("SET — Already Deleted") is None, "gelöscht, success=true")
out, err = load("D2_bereits_geloescht"); r = out("SET — Already Deleted")
rec("D2_bereits_geloescht", not err and out("GOOGLE CALENDAR — Delete Event") is None and r and r[0].get("status") == "already_deleted" and "bereits gelöscht" in json.dumps(r[0], ensure_ascii=False),
    "nicht erneut gelöscht, Meldung auf Deutsch")
out, err = load("G1_leere_Anfrage"); r = out("RESULT — Invalid Search Query")
rec("G1_leere_Anfrage", not err and out("GMAIL — Search Messages") is None and r and r[0].get("status") == "invalid_query" and "Suchanfrage fehlt" in json.dumps(r[0], ensure_ascii=False), "keine Suche, Meldung auf Deutsch")
out, err = load("G2_keine_Treffer"); r = out("RESULT — No Messages Found")
rec("G2_keine_Treffer", not err and r and r[0].get("status") == "no_messages_found" and out("Prepare Search Results") is None, "Meldung «keine Treffer»")
out, err = load("G3_Treffer"); r = out("Prepare Search Results")
rec("G3_Treffer", not err and r and r[0].get("message_id") == "m1" and out("RESULT — No Messages Found") is None, f"Treffer übergeben (message_id={r[0].get('message_id') if r else None})")
print("\n".join(rows)); print(f"{ok}/{len(rows)} PASS"); sys.exit(0 if ok == len(rows) else 1)
