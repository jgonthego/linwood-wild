#!/usr/bin/env python3
"""Pull real, research-grade wildlife data from the free iNaturalist API (v1)
into data/species.json. No API key needed. Polite: ~1 request/second.

Search area: a ~15 km circle around the Linwood, NJ town centroid (public
OpenStreetMap boundary centroid, rounded) -- covers the South Jersey shore
back-bay marsh, barrier islands and pine-barrens edge."""
import json, re, time, datetime, urllib.request, urllib.parse, sys, os

API = "https://api.inaturalist.org/v1"
LAT, LNG, RADIUS_KM = 39.34, -74.58, 15   # Linwood town centroid (rounded), not any address
UA = "linwood-wild/1.0 (static wildlife site; github.com/jgonthego/linwood-wild)"
OK_LICENSES = {"cc0": "CC0", "cc-by": "CC BY", "cc-by-sa": "CC BY-SA", "cc-by-nc": "CC BY-NC"}
LICENSE_URLS = {"cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
                "cc-by": "https://creativecommons.org/licenses/by/4.0/",
                "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/",
                "cc-by-nc": "https://creativecommons.org/licenses/by-nc/4.0/"}
GROUPS = [
    ("birds",   "Birds",                   {"iconic_taxa": "Aves"}),
    ("mammals", "Mammals",                 {"iconic_taxa": "Mammalia"}),
    ("herps",   "Reptiles & Amphibians",   {"iconic_taxa": "Reptilia,Amphibia"}),
    ("insects", "Insects",                 {"iconic_taxa": "Insecta"}),
    # Arachnida (spiders, ticks, mites, harvestmen) + Myriapoda (centipedes, millipedes) + Isopoda (pill bugs etc.)
    ("crawlies","Spiders & other bugs",    {"taxon_id": "47119,144128,48147"}),
]
BASE = {"lat": LAT, "lng": LNG, "radius": RADIUS_KM, "quality_grade": "research"}
_last = [0.0]

def get(path, params=None):
    url = f"{API}{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(6):
        wait = 1.05 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print(f"  retry {attempt+1} {url[:110]}: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("failed: " + url)

def species_counts(extra):
    out, page = [], 1
    while True:
        d = get("/observations/species_counts", {**BASE, **extra, "per_page": 500, "page": page})
        out += d["results"]
        if page * 500 >= d["total_results"] or not d["results"]: return out
        page += 1

def photo(p):
    if not p or (p.get("license_code") or "").lower() not in OK_LICENSES: return None
    lc = p["license_code"].lower()
    url = p.get("medium_url") or (p.get("url") or "").replace("square", "medium")
    return {"url": url, "sq": (p.get("square_url") or p.get("url") or "").replace("square", "small"),
            "attr": p.get("attribution", ""), "license": OK_LICENSES[lc], "license_url": LICENSE_URLS[lc]}

def clean_summary(html):
    if not html: return None
    t = re.sub(r"<[^>]+>", "", html)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s*\([^()]*\)", "", t)  # drop parentheticals (pronunciations etc.)
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", t)
    s = " ".join(sents[:2])
    return s[:320].rsplit(" ", 1)[0] + "…" if len(s) > 320 else s

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    species = {}
    for key, label, q in GROUPS:
        print("group", key)
        for r in species_counts(q):
            t = r["taxon"]
            species[t["id"]] = {"id": t["id"], "g": key, "sci": t["name"],
                "com": t.get("preferred_common_name") or "", "n": r["count"],
                "m": [0]*12, "ph": photo(t.get("default_photo")),
                "wiki_url": t.get("wikipedia_url"), "ancestor_ids": t.get("ancestor_ids", [])}
        for m in range(1, 13):
            for r in species_counts({**q, "month": m}):
                s = species.get(r["taxon"]["id"])
                if s: s["m"][m-1] = r["count"]
            print(f"  month {m} ok")
    # taxon details: order/family names, Wikipedia summary, alternate open-licensed photos
    ids = list(species)
    for i in range(0, len(ids), 30):
        batch = ids[i:i+30]
        d = get("/taxa/" + ",".join(map(str, batch)))
        for t in d["results"]:
            s = species.get(t["id"])
            if not s: continue
            for a in t.get("ancestors", []):
                if a["rank"] == "order": s["order"] = a["name"]
                if a["rank"] == "family":
                    s["family"] = a["name"]; s["family_com"] = a.get("preferred_common_name") or ""
            s["fact"] = clean_summary(t.get("wikipedia_summary"))
            if t.get("wikipedia_url"): s["wiki_url"] = t["wikipedia_url"]
            if not s["ph"]:
                for tp in t.get("taxon_photos", []):
                    ph = photo(tp.get("photo"))
                    if ph: s["ph"] = ph; break
            cs = [c for c in t.get("conservation_statuses", []) if c.get("place") and c["place"].get("name") == "New Jersey"]
            if cs: s["nj_status"] = cs[0].get("status_name") or cs[0].get("status")
        print(f"  taxa {i+len(batch)}/{len(ids)}")
    # rarest birds: latest research-grade sighting date (no locations kept)
    rare = sorted([s for s in species.values() if s["g"] == "birds"], key=lambda s: s["n"])
    rare = [s for s in rare if s["n"] <= 2]
    for s in rare:
        d = get("/observations", {**BASE, "taxon_id": s["id"], "order_by": "observed_on", "order": "desc", "per_page": 1})
        if d["results"]:
            o = d["results"][0]
            s["last_seen"] = o.get("observed_on"); s["last_obs"] = f"https://www.inaturalist.org/observations/{o['id']}"
    for s in species.values(): s.pop("ancestor_ids", None)
    out = {"pulled_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "pulled_date": datetime.datetime.now().strftime("%Y-%m-%d"),
           "area": {"label": "Linwood & the South Jersey shore (Atlantic County, NJ)", "radius_km": RADIUS_KM,
                    "towns": ["Linwood", "Northfield", "Somers Point", "Egg Harbor Twp", "Pleasantville",
                              "Absecon", "Margate", "Ventnor", "Atlantic City", "Ocean City (north end)"]},
           "source": "iNaturalist API v1 — research-grade observations",
           "groups": [{"key": k, "label": l} for k, l, _ in GROUPS],
           "species": sorted(species.values(), key=lambda s: -s["n"])}
    os.makedirs("data", exist_ok=True)
    with open("data/species.json", "w") as f: json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
    print("species:", len(species))

if __name__ == "__main__":
    main()
