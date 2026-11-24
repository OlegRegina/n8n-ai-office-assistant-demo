#!/usr/bin/env python3
"""Testaufbau für den KI-Büroassistenten. Aufruf:  python3 -I -B make_harness.py <repo> <ausgabeordner>
Echte Nodes und Ausdrücke aus dem Repository laufen in n8n; Telegram, Gmail und Google Calendar sind durch feste Beispieldaten ersetzt
(Code-Nodes mit demselben Namen, damit Verbindungen und $('…')-Verweise gleich bleiben). Szenarien:
  F1–F5  Absenderfilter des Haupt-Workflows (erlaubte ID im Test: die erfundene 42)
  D1–D2  Werkzeug «Termin löschen»: aktiver Termin wird gelöscht, bereits gelöschter nicht
  G1–G3  Werkzeug «Suche in Gmail»: leere Anfrage, keine Treffer, Treffer"""
import copy, json, sys, uuid
from pathlib import Path

repo, dst = Path(sys.argv[1]), Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
L = lambda p: json.load(open(repo / p, encoding="utf-8"))
def code(name, js, pos=(0, 0)): return {"parameters": {"jsCode": js}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": list(pos), "id": str(uuid.uuid4()), "name": name}
def setn(name): return {"parameters": {"assignments": {"assignments": [{"id": str(uuid.uuid4()), "name": "r", "value": name, "type": "string"}]}, "options": {}}, "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [0, 0], "id": str(uuid.uuid4()), "name": name}
START = {"parameters": {}, "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 0], "id": str(uuid.uuid4()), "name": "Start"}
items = lambda arr: "return " + json.dumps([{"json": x} for x in arr], ensure_ascii=False) + ";"

def from_workflow(path, mocks, trigger, trigger_items):
    """Workflow aus dem Repository; Nodes in «mocks» und der Trigger werden durch Code-Nodes ersetzt."""
    w = L(path); nodes = []
    for n in w["nodes"]:
        if n["type"].endswith("stickyNote"): continue
        if n["name"] == trigger: nodes.append(code(n["name"], items(trigger_items), n["position"]))
        elif n["name"] in mocks: nodes.append(code(n["name"], mocks[n["name"]], n["position"]))
        else: nodes.append(copy.deepcopy(n))
    conn = copy.deepcopy(w["connections"]); conn["Start"] = {"main": [[{"node": trigger, "type": "main", "index": 0}]]}
    return [START] + nodes, conn

S = {}
# F: Absenderfilter
main = L("workflows/ki-bueroassistent.json")
filt = copy.deepcopy(next(n for n in main["nodes"] if n["name"] == "IF — Allowed Sender?"))
filt["parameters"]["conditions"]["conditions"][0]["rightValue"] = "42"
for k, upd in {"F1_eigene_Nachricht": {"message": {"text": "x", "from": {"id": 42}, "chat": {"id": 42}}},
               "F2_fremde_Nachricht": {"message": {"text": "x", "from": {"id": 43}, "chat": {"id": 43}}},
               "F3_fremder_Knopf": {"callback_query": {"data": "x", "from": {"id": 43}}},
               "F4_eigener_Knopf": {"callback_query": {"data": "x", "from": {"id": 42}}},
               "F5_ohne_Absender": {"message": {"text": "x", "chat": {"id": 1}}}}.items():
    nodes = [START, code("Telegram — User Message", items([upd])), filt, setn("Weiter zum Agenten"), setn("Ignoriert")]
    conn = {"Start": {"main": [[{"node": "Telegram — User Message", "type": "main", "index": 0}]]},
            "Telegram — User Message": {"main": [[{"node": "IF — Allowed Sender?", "type": "main", "index": 0}]]},
            "IF — Allowed Sender?": {"main": [[{"node": "Weiter zum Agenten", "type": "main", "index": 0}], [{"node": "Ignoriert", "type": "main", "index": 0}]]}}
    S[k] = (nodes, conn)
# D: Termin löschen
for k, status in {"D1_aktiver_Termin": "confirmed", "D2_bereits_geloescht": "cancelled"}.items():
    S[k] = from_workflow("workflows/tools/calendar-delete-event.json",
                         {"DEBUG — Get Event By ID.": items([{"id": "e1", "status": status, "summary": "Besprechung Muster AG"}]),
                          "GOOGLE CALENDAR — Delete Event": items([{"success": True}])},
                         "TRIGGER — Receive Update Data", [{"event_id": "e1"}])
# G: Suche in Gmail
hit = {"id": "m1", "threadId": "t1", "From": "Anna Muster <anna.muster@example.com>", "Subject": "Bitte um den Vertrag", "snippet": "Guten Tag", "labelIds": ["INBOX"]}
for k, (q, res) in {"G1_leere_Anfrage": ("   ", [{}]), "G2_keine_Treffer": ("from:anna.muster@example.com", [{}]), "G3_Treffer": ("from:anna.muster@example.com", [hit])}.items():
    S[k] = from_workflow("workflows/tools/gmail-search-messages.json", {"GMAIL — Search Messages": items(res)}, "When Executed by Another Workflow", [{"query": q}])

ids = []
for i, (k, (nodes, conn)) in enumerate(S.items()):
    wid = f"lt{i + 1:014d}"; ids.append(f"{wid} {k}")
    json.dump({"id": wid, "name": k, "nodes": nodes, "connections": conn, "settings": {"executionOrder": "v1"}, "active": False}, open(dst / f"{k}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n".join(ids))
