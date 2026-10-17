#!/usr/bin/env python3
"""Build the 'possible at home' species list (data/species.json) from real, citable, free data.

Evidence: GBIF occurrence records (year >= 2000) -- mostly eBird (EOD), iNaturalist research-grade
and museum specimens -- counted by verbatim scientific name in three zones around the center point:
  A  = within 2 km                       (suburbs, salt marsh, tidal creeks)
  B  = within 8 km, mainland only        (barrier islands / ocean cut off along the back-bay line)
  C  = within 15 km, mainland only
Likelihood rules (see LIKELY_RULES below) are applied to those counts; strictly marine taxa are
excluded. Month bars: birds = share of all bird records in zone B per month (corrects for eBird effort);
other groups = records per month in zone C. Names/photos/facts come from iNaturalist.
No keys, no accounts. The center point stays private (data/home.private.json or HOME_LAT/HOME_LNG secrets)."""
import json, re, sys, os, time, datetime, urllib.request, urllib.parse
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zones import home, circle_wkt, mainland_wkt
from fetch_data import get as inat_get, photo, clean_summary, MARINE, UA

GBIF = "https://api.gbif.org/v1/occurrence/search"
GROUPS = [("birds", "Birds", [212]), ("mammals", "Mammals", [359]),
          ("herps", "Reptiles & Amphibians", [11418114, 11592253, 131]),
          ("insects", "Insects", [216]), ("crawlies", "Spiders & other bugs", [367, 360, 361])]
ICONIC = {"birds": {"Aves"}, "mammals": {"Mammalia"}, "herps": {"Reptilia", "Amphibia"}, "insects": {"Insecta"},
          "crawlies": {"Arachnida", "Animalia", "Mollusca"}}
EBIRD = "4fa7b334-ce0d-4e88-aaae-2e0c138d049e"   # eBird Observation Dataset (EOD) on GBIF
COMMON = {"year": "2000,2026", "occurrenceStatus": "PRESENT", "hasGeospatialIssue": "false"}

def gbif(params):
    q = urllib.parse.urlencode([(k, x) for k, v in params.items() for x in (v if isinstance(v, list) else [v])])
    for attempt in range(5):
        try:
            time.sleep(0.25)
            req = urllib.request.Request(GBIF + "?" + q, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception as e:
            print("  gbif retry", attempt, e, file=sys.stderr); time.sleep(5 * (attempt + 1))
    raise RuntimeError("GBIF failed")

def norm(name):
    t = name.lower().strip().split()
    if len(t) < 2 or not re.fullmatch(r"[a-z]+", t[0]) or not re.fullmatch(r"[a-z-]+", t[1]): return None
    if t[1] in ("sp", "sp.", "spp", "spp.", "x", "cf", "cf.", "aff", "aff."): return None
    if len(t) >= 3 and t[2] in ("x", "×"): return None
    return t[0] + " " + t[1]

# Old/lumped names in older eBird & GBIF records -> the taxon that actually occurs in eastern North America
# (current Clements/iNaturalist splits). Without this they would map to the Eurasian/Mangrove forms.
LUMPED = {"circus cyaneus": "circus hudsonius", "troglodytes troglodytes": "troglodytes hiemalis",
          "numenius phaeopus": "numenius hudsonicus", "setophaga petechia": "setophaga aestiva",
          "gallinago gallinago": "gallinago delicata", "gallinula chloropus": "gallinula galeata",
          "larus argentatus": "larus smithsonianus", "melanitta fusca": "melanitta deglandi",
          "charadrius alexandrinus": "charadrius nivosus", "dendroica petechia": "setophaga aestiva"}

def facet(geom, keys, extra=None):
    d = gbif({**COMMON, "geometry": geom, "taxonKey": keys, "limit": 0, "facet": "verbatimScientificName",
              "facetLimit": 10000, **(extra or {})})
    out = defaultdict(int)
    for c in (d["facets"][0]["counts"] if d.get("facets") else []):
        n = norm(c["name"])
        if n: out[LUMPED.get(n, n)] += c["count"]
    return out, d["count"]

def classify(g, a, b, c, strong_flier=False):
    if g == "birds":
        if a >= 30: return "likely"
        if a >= 3 or b >= 50: return "possible"
        return "rare"
    if a >= 2 or b >= 5: return "likely"
    if a >= 1 or b >= 2: return "possible"
    if b == 1: return "rare"
    return "rare" if strong_flier else None   # only recorded 8-15 km away: habitat likely not here

LIKELY_RULES = {"birds": "Likely = 30+ records within 2 km; Possible = 3-29 within 2 km or 50+ within 8 km (mainland); Rare = everything else recorded within 15 km (mainland)",
                "other": "Likely = 2+ records within 2 km or 5+ within 8 km; Possible = 1 record within 2 km or 2-4 within 8 km; Rare = a single record within 8 km. Species only recorded 8-15 km away are left out (they don't travel far and their habitat probably isn't here) - except strong fliers (butterflies, moths, dragonflies & damselflies), which are kept as Rare"}

def season_birds(f):
    mx = max(f) or 1; v = [x / mx for x in f]
    win = (v[11] + v[0] + v[1]) / 3; summ = (v[5] + v[6]) / 2; mig = max((v[3] + v[4]) / 2, (v[8] + v[9]) / 2)
    if min(v) >= 0.1: return "Year-round"
    if summ >= 0.3 and win < 0.1: return "Summer"
    if win >= 0.3 and summ < 0.1: return "Winter"
    if mig >= 0.3 and summ < 0.2 and win < 0.2: return "Migrant"
    if sum(1 for x in f if x > 0) >= 11: return "Year-round"
    return "Irregular"

def inat_lookup(name, g, _depth=0):
    d = inat_get("/taxa", {"q": name, "per_page": 10, "is_active": "true"})
    for t in d["results"]:
        if t.get("rank_level") != 10: continue
        if t.get("iconic_taxon_name") not in ICONIC[g]: continue
        if t["name"].lower() == name or (t.get("matched_term") or "").lower() == name: return t
    if _depth == 0:   # synonym fallback: GBIF backbone accepted name (e.g. Rana clamitans -> Lithobates clamitans)
        try:
            m = json.load(urllib.request.urlopen("https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": name, "kingdom": "Animalia"}), timeout=30))
            acc = (m.get("species") or "").lower()
            if acc and acc != name: return inat_lookup(acc, g, 1)
        except Exception: pass
    return None

def main():
    lat, lng = home()
    zones = {"A": circle_wkt(lat, lng, 2), "B": mainland_wkt(lat, lng, 8), "C": mainland_wkt(lat, lng, 15)}
    now = datetime.datetime.now(datetime.timezone.utc)
    cand = {}
    for g, label, keys in GROUPS:
        z = {k: facet(w, keys)[0] for k, w in zones.items()}
        mzone = "B" if g == "birds" else "C"
        months, totals = [], []
        for m in range(1, 13):
            # birds: eBird checklists only (EOD dataset) so the one-weekend February Great Backyard Bird Count does not skew the seasons
            extra = {"month": m, **({"datasetKey": EBIRD} if g == "birds" else {})}
            f, tot = facet(zones[mzone], keys, extra); months.append(f); totals.append(tot)
        names = set(z["A"]) | set(z["B"]) | set(z["C"])
        for n in names:
            a, b, c = z["A"].get(n, 0), z["B"].get(n, 0), z["C"].get(n, 0)
            raw = [months[i].get(n, 0) for i in range(12)]
            if g == "birds":
                freq = [raw[i] / totals[i] if totals[i] else 0 for i in range(12)]
                mvals = [round(x * 10000, 1) for x in freq]   # records per 10,000 bird records that month
            else:
                mvals = raw
            cand[n] = {"g": g, "name": n, "A": a, "B": b, "C": c, "lik": classify(g, a, b, c, True), "m": mvals, "mraw": raw}
            if g == "birds": cand[n]["season"] = season_birds(mvals) if sum(raw) >= 10 else "Irregular"
            else:
                act = [i for i in range(12) if raw[i]]
                cand[n]["season"] = "Active " + ("year-round" if len(act) >= 11 else
                    (["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][act[0]] + "–" +
                     ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][act[-1]]) if act else "?")
        print(g, "candidates:", sum(1 for v in cand.values() if v["g"] == g), "month totals:", totals)
    # map to iNaturalist taxa
    local = json.load(open("data/inat_local.json"))["species"] if os.path.exists("data/inat_local.json") else []
    local_by_name = {s["sci"].lower(): s for s in local}
    cache_p = "data/cache_inat_names.json"
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    for i, (n, s) in enumerate(sorted(cand.items())):
        key = s["g"] + ":" + n
        if key not in cache:
            t = inat_lookup(n, s["g"])
            cache[key] = {"id": t["id"], "anc": t.get("ancestor_ids", [])} if t else None
            if i % 50 == 0: json.dump(cache, open(cache_p, "w")); print("  inat names", i, "/", len(cand))
    json.dump(cache, open(cache_p, "w"))
    species, removed, unmatched = {}, [], []
    for n, s in cand.items():
        hit = cache.get(s["g"] + ":" + n)
        if not hit: unmatched.append(n); continue
        rule = [v for k, v in MARINE.items() if k in hit["anc"]]
        if rule: removed.append({"name": n, "rule": rule[0], "A": s["A"], "B": s["B"], "C": s["C"]}); continue
        tid = hit["id"]
        if tid in species:   # two GBIF names -> one iNat species: merge
            o = species[tid]
            for k in ("A", "B", "C"): o[k] += s[k]
            o["m"] = [round(x + y, 1) for x, y in zip(o["m"], s["m"])]; o["lik"] = classify(o["g"], o["A"], o["B"], o["C"], True); continue
        s = dict(s); s["id"] = tid; s.pop("mraw")
        species[tid] = s
    # taxon details
    ids = list(species)
    for i in range(0, len(ids), 30):
        for t in inat_get("/taxa/" + ",".join(map(str, ids[i:i + 30])))["results"]:
            s = species.get(t["id"])
            if not s: continue
            s["sci"] = t["name"]; s["com"] = t.get("preferred_common_name") or ""
            for a in t.get("ancestors", []):
                if a["rank"] == "order": s["order"] = a["name"]
                if a["rank"] == "family": s["family"] = a["name"]; s["family_com"] = a.get("preferred_common_name") or ""
            s["fact"] = clean_summary(t.get("wikipedia_summary")); s["wiki_url"] = t.get("wikipedia_url")
            s["ph"] = photo(t.get("default_photo"))
            if not s["ph"]:
                for tp in t.get("taxon_photos", []):
                    ph = photo(tp.get("photo"))
                    if ph: s["ph"] = ph; break
            loc = local_by_name.get(t["name"].lower())
            if loc: s["logged"] = loc["n"]
        print("  taxa", min(i + 30, len(ids)), "/", len(ids))
    FLIERS = {"Lepidoptera", "Odonata"}; dropped_far = []
    for tid in list(species):
        s = species[tid]
        if s["g"] != "birds":
            s["lik"] = classify(s["g"], s["A"], s["B"], s["C"], s.get("order") in FLIERS)
            if s["lik"] is None: dropped_far.append(s.get("com") or s.get("sci")); del species[tid]
    print("dropped (non-birds only recorded 8-15 km away):", len(dropped_far))
    for s in species.values():
        s.pop("name", None)
        s["n"] = s["A"] + s["B"] + s["C"]  # for sorting only
    order = {"likely": 0, "possible": 1, "rare": 2}
    out = {"pulled_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "pulled_date": datetime.datetime.now().strftime("%Y-%m-%d"),
           "source": "GBIF.org occurrence search (eBird EOD, iNaturalist research-grade, museum specimens), records since 2000; names, photos & facts from iNaturalist",
           "rules": LIKELY_RULES, "removed_marine": removed, "dropped_far": len(dropped_far), "unmatched_names": sorted(unmatched),
           "groups": [{"key": k, "label": l} for k, l, _ in GROUPS],
           "species": sorted(species.values(), key=lambda s: (order[s["lik"]], -s["A"], -s["B"], -s["C"]))}
    json.dump(out, open("data/species.json", "w"), separators=(",", ":"), ensure_ascii=False)
    from collections import Counter
    print("species:", len(species), Counter((s["g"], s["lik"]) for s in species.values()))
    print("removed marine:", [(r["name"], r["rule"]) for r in removed]); print("unmatched:", len(unmatched), unmatched[:40])

if __name__ == "__main__":
    main()
