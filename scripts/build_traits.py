#!/usr/bin/env python3
"""Build data/traits.json for the describe-a-bird search + the male/female notes. Offline, no network.
Inputs: data/traits_curated.txt (hand-written field-guide traits), data/wiki_desc.json (Wikipedia text),
data/species.json. For any bird missing from the curated table, colours / marks are keyword-parsed from
its Wikipedia description and flagged q="wiki". Length (cm) is parsed from Wikipedia when stated and used to
cross-check the curated value. 'How to tell male vs female' = VERBATIM Wikipedia sentences only."""
import json, re, os, sys

COLORS = ["red", "orange", "yellow", "olive", "green", "blue", "brown", "rufous", "buff", "gray", "black", "white", "pink", "purple", "chestnut", "iridescent"]
WIKI_COLOR = {"red": r"\b(red|crimson|scarlet|reddish)\b", "orange": r"\borange\b", "yellow": r"\b(yellow|yellowish|golden)\b",
              "olive": r"\bolive\b", "green": r"\b(green|greenish)\b", "blue": r"\b(blue|bluish)\b", "brown": r"\b(brown|brownish)\b",
              "rufous": r"\b(rufous|rusty|cinnamon|chestnut)\b", "buff": r"\b(buff|buffy|tan|fawn)\b", "gray": r"\b(gr[ae]y|greyish|grayish|slate)\b",
              "black": r"\b(black|blackish)\b", "white": r"\b(white|whitish)\b", "pink": r"\b(pink|pinkish|rosy)\b", "purple": r"\b(purple|violet)\b",
              "iridescent": r"\b(iridescent|glossy)\b", "chestnut": r"\bchestnut\b"}
WIKI_MARK = {"crest": r"\bcrest(ed)?\b", "streaked-breast": r"\bstreak\w*\b[^.]{0,40}\b(breast|chest|underparts)\b|\b(breast|chest|underparts)\b[^.]{0,30}\bstreak",
             "spotted-breast": r"\bspot\w*\b[^.]{0,40}\b(breast|chest|underparts)\b", "wingbars": r"\bwing ?bars?\b", "eyering": r"\beye[- ]?ring\b",
             "long-tail": r"\blong tail\b", "forked-tail": r"\bforked tail\b", "long-legs": r"\blong legs\b", "long-neck": r"\blong neck\b",
             "curved-bill": r"\b(decurved|down-?curved)\b", "hooked-bill": r"\bhooked\b", "barred": r"\bbarr(ed|ing)\b", "black-cap": r"\bblack (cap|crown)\b",
             "red-cap": r"\bred (cap|crown)\b", "black-mask": r"\bblack (face )?mask\b", "white-rump": r"\bwhite rump\b", "yellow-rump": r"\byellow rump\b"}
SEX_W = re.compile(r"\b(males?|females?|sexes|sexually|dimorphi\w*|hens?|drakes?)\b", re.I)
LOOK_W = re.compile(r"\b(plumage|colou?r\w*|alike|similar|identical|duller|brighter|paler|darker|patch|cap|crown|crest|head|throat|breast|bill|"
                    r"red|orange|yellow|green|blue|brown|gr[ae]y|black|white|buff|olive|rufous|chestnut|pink|purple|iridescent|glossy|"
                    r"streak\w*|spot\w*|bar(red|s)?|mask|stripe\w*|dimorphi\w*|distinguish\w*|differ\w*)\b", re.I)
SKIP_W = re.compile(r"\b(eggs?|incubat\w*|nests?|clutch|sings?|songs?|calls?|courtship|copulat\w*|territor\w*|feed(s|ing)?|chicks?|hatch\w*|fledg\w*|mates?|mating|pairs?|weigh\w*|kg|grams?|captiv\w*|hybrid\w*|survival|lifespan|latin|greek|word|named?|etymology|iucn|threatened|binomial|genus|described|population\w*|aggressi\w*|health\w*|condition|cm|mm|in\)|lb|oz)\b", re.I)

CTX_START = re.compile(r"^(This|These|That|Those|However|Although|But|Such|In contrast|By contrast|It|They|He|She)\b")

def sentences(t):
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"([a-z\)\]%])\.([A-Z])", r"\1. \2", t)          # "...in).The" -> two sentences
    return [s.strip() for s in re.split(r"(?<=[^A-Z][^ .][.!?])\s+(?=[A-Z])", t) if s.strip()]

def sex_note(w):
    picked = []
    for src in (w.get("desc", ""), w.get("lead", "")):
        for s in sentences(src):
            near = any(LOOK_W.search(s[max(0, m.start() - 90):m.end() + 90]) for m in SEX_W.finditer(s))
            if near and not CTX_START.match(s) and not SKIP_W.search(s) and 25 <= len(s) <= 400 and s not in picked:
                picked.append(s)
        if picked: break
    out = ""
    for s in picked:
        if len(out) + len(s) > 520: break
        out += (" " if out else "") + s
    return out or None

def length_cm(w):
    t = (w.get("desc", "") + " " + w.get("lead", "")).replace("\u2013", "-").replace("\u2014", "-")
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*cm|(\d+(?:\.\d+)?)\s*cm", t):
        ctx = t[max(0, m.start() - 90):m.start()].lower()
        if re.search(r"wing ?span|wing chord|wing length|tail|bill|tarsus|culmen|egg|wings? (is|are|measure)", ctx[-45:]): continue
        if not re.search(r"long|length|measur|size|from bill|cm", ctx + " cm"): continue
        a = float(m.group(1) or m.group(3)); b = float(m.group(2) or a)
        if 5 <= a <= 200: return round((a + b) / 2, 1)
    return None

def wiki_traits(w):
    t = (w.get("desc") or w.get("lead") or "").lower()
    c = [k for k, rx in WIKI_COLOR.items() if re.search(rx, t)]
    k = [k for k, rx in WIKI_MARK.items() if re.search(rx, t)]
    return c, k

def main():
    sp = [s for s in json.load(open("data/species.json"))["species"] if s["g"] == "birds"]
    wiki = json.load(open("data/wiki_desc.json")) if os.path.exists("data/wiki_desc.json") else {}
    cur = {}
    for line in open("data/traits_curated.txt"):
        if line.startswith("#") or not line.strip(): continue
        p = [x.strip() for x in line.split("|")]
        cur[p[0]] = {"len": float(p[1]), "c": p[2].split(), "fc": p[3].split(), "k": p[4].split(), "b": p[5].split(), "h": p[6].split()}
    out, report = {}, {"size_mismatch": [], "color_not_in_wiki": [], "wiki_only": [], "no_wiki": []}
    for s in sp:
        k = str(s["id"]); w = wiki.get(k) or {}
        wl = length_cm(w) if w else None
        if k in cur:
            e = dict(cur[k]); e["q"] = "curated"
            if wl and abs(wl - e["len"]) / e["len"] > 0.35: report["size_mismatch"].append((s["com"], e["len"], wl))
            if w.get("desc"):
                wc, _ = wiki_traits(w)
                miss = [c for c in e["c"] if c in WIKI_COLOR and c not in wc and c != "iridescent"]
                if miss: report["color_not_in_wiki"].append((s["com"], miss))
        else:
            if not w: report["no_wiki"].append(s["com"]); continue
            c, mk = wiki_traits(w)
            e = {"len": wl, "c": c, "fc": [], "k": mk, "b": [], "h": [], "q": "wiki"}
            report["wiki_only"].append(s["com"])
        if wl: e["wlen"] = wl
        note = sex_note(w) if w else None
        if note: e["sex"] = note
        if w.get("url"): e["wurl"] = w["url"]
        out[k] = e
    json.dump(out, open("data/traits.json", "w"), separators=(",", ":"), ensure_ascii=False)
    json.dump(report, open("data/traits_report.json", "w"), indent=1, ensure_ascii=False)
    print("traits:", len(out), "of", len(sp), "| curated:", sum(1 for e in out.values() if e["q"] == "curated"),
          "| wiki-parsed:", sum(1 for e in out.values() if e["q"] == "wiki"), "| with wiki length:", sum(1 for e in out.values() if e.get("wlen")),
          "| male/female note:", sum(1 for e in out.values() if e.get("sex")))
    print("size mismatches (curated vs wiki >35%):", report["size_mismatch"])
    print("curated colours not mentioned in wiki description:", len(report["color_not_in_wiki"]))

if __name__ == "__main__":
    main()
