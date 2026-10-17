#!/usr/bin/env python3
"""Wikipedia text for every bird (data/wiki_desc.json), free MediaWiki API, no key.
Keeps the lead and the 'Description' / 'Identification' / 'Appearance' section (plain text) so
build_traits.py can (a) parse size/colour keywords for birds without curated traits and
(b) quote VERBATIM sentences about male vs female plumage. Text is CC BY-SA 4.0 (Wikipedia).
Incremental: existing entries are kept."""
import json, os, re, sys, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_data import UA
OUT = "data/wiki_desc.json"
API = "https://en.wikipedia.org/w/api.php"
WANT = re.compile(r"^(description|identification|appearance|plumage|description and identification|morphology|characteristics|physical description|description and taxonomy)$", re.I)

def fetch(title):
    q = {"action": "query", "prop": "extracts|info", "explaintext": 1, "redirects": 1, "titles": title,
         "format": "json", "formatversion": 2, "inprop": "url", "exsectionformat": "wiki"}
    for a in range(4):
        try:
            req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers={"User-Agent": UA + " (github.com/jgonthego/linwood-wild)"})
            p = json.load(urllib.request.urlopen(req, timeout=60))["query"]["pages"][0]
            return p if not p.get("missing") else None
        except Exception as e:
            print("retry", a, title, e, file=sys.stderr); time.sleep(3 * (a + 1))
    return None

def split(text):
    parts = re.split(r"\n(={2,4}) *(.+?) *={2,4}\n", "\n" + text)
    lead = parts[0].strip(); desc = []; i = 1; take = 0
    while i < len(parts):
        lvl, head, body = len(parts[i]), parts[i + 1], parts[i + 2] if i + 2 < len(parts) else ""
        if WANT.match(head.strip()) and lvl == 2: take = 2
        elif lvl <= take: take = 0
        if take or (lvl > 2 and WANT.match(head.strip())): desc.append(body.strip())
        i += 3
    return lead, "\n".join(x for x in desc if x)

def main():
    sp = [s for s in json.load(open("data/species.json"))["species"] if s["g"] == "birds"]
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for i, s in enumerate(sp):
        k = str(s["id"])
        if k in out: continue
        title = (s.get("wiki_url") or "").rsplit("/wiki/", 1)[-1] or s["sci"]
        p = fetch(urllib.parse.unquote(title)) or fetch(s["sci"]) or (s.get("com") and fetch(s["com"]))
        time.sleep(0.3)
        if not p: print("missing", s.get("com")); continue
        lead, desc = split(p.get("extract", ""))
        out[k] = {"title": p["title"], "url": p.get("fullurl"), "lead": lead[:3000], "desc": desc[:6000], "rev": p.get("lastrevid")}
        if i % 20 == 0: json.dump(out, open(OUT, "w"), ensure_ascii=False); print(i, s.get("com"), len(desc))
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=0)
    print("wiki entries:", len(out), "with description section:", sum(1 for v in out.values() if v["desc"]))

if __name__ == "__main__":
    main()
