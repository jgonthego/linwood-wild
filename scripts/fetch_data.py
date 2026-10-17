#!/usr/bin/env python3
"""Pull real, research-grade wildlife observations from the free iNaturalist API (v1)
and keep only what could realistically turn up at a mainland Linwood, NJ home:

  * search circle: 5 km around the Linwood town centre (public OSM town centroid, rounded)
  * every observation point is classified with OpenStreetMap data (data/geo.json):
      barrier-island towns (Margate, Longport, Ventnor, Atlantic City, Ocean City) -> dropped
      tidal / open water (seaward of the OSM coastline, bays, channels, lakes)  -> dropped
      salt marsh / marsh edge -> kept, flagged "marsh";  everything else -> "land"
  * obscured (privacy-randomised) points and points with >1 km GPS uncertainty -> dropped
  * marine-only taxa (cetaceans, seals, sea turtles, pelagic/ocean birds, ...) -> dropped,
    unless at least one kept record is clearly over land: mainland land (not marsh) and
    at least 300 m from the shoreline (so shore-based photos of birds on the bay don't count)
Output: data/species.json. No API key needed; ~1 request/second."""
import json, re, time, datetime, urllib.request, urllib.parse, sys, os
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import Geo

API = "https://api.inaturalist.org/v1"
LAT, LNG, RADIUS_KM = 39.34, -74.58, 5   # Linwood town centroid (rounded) -- not any address
UA = "linwood-wild/1.0 (static wildlife site)"
OK_LICENSES = {"cc0": "CC0", "cc-by": "CC BY", "cc-by-sa": "CC BY-SA", "cc-by-nc": "CC BY-NC"}
LICENSE_URLS = {"cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
                "cc-by": "https://creativecommons.org/licenses/by/4.0/",
                "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/",
                "cc-by-nc": "https://creativecommons.org/licenses/by-nc/4.0/"}
GROUPS = [
    ("birds",   "Birds",                 {"iconic_taxa": "Aves"}),
    ("mammals", "Mammals",               {"iconic_taxa": "Mammalia"}),
    ("herps",   "Reptiles & Amphibians", {"iconic_taxa": "Reptilia,Amphibia"}),
    ("insects", "Insects",               {"iconic_taxa": "Insecta"}),
    # Arachnida (spiders, ticks, mites, harvestmen) + Myriapoda (centipedes, millipedes) + Oniscidea (land isopods: pill/sow bugs)
    ("crawlies","Spiders & other bugs",  {"taxon_id": "47119,144128,84718"}),
]
# Marine-only taxa (iNaturalist taxon ids). Dropped unless a kept record is on mainland land.
MARINE = {152871: "whales & dolphins (Cetacea)", 372843: "seals (Phocoidea)", 46306: "manatees (Sirenia)",
          372234: "sea turtles (Chelonioidea)", 39675: "leatherback turtles (Dermochelyidae)",
          3784: "gannets & boobies (Sulidae)", 71295: "auks & puffins (Alcidae)", 71367: "jaegers & skuas (Stercorariidae)",
          4020: "shearwaters & petrels (Procellariidae)", 71326: "storm-petrels (Hydrobatidae)", 793435: "storm-petrels (Oceanitidae)",
          7031: "scoters (Melanitta)", 7023: "eiders (Somateria)",
          4328: "Brown Pelican (Pelecanus occidentalis)", 7169: "Long-tailed Duck (Clangula)", 7110: "Harlequin Duck (Histrionicus)"}
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

def observations(extra):
    out, above = [], 0
    while True:
        d = get("/observations", {**BASE, **extra, "per_page": 200, "order_by": "id", "order": "asc", "id_above": above})
        if not d["results"]: return out
        out += d["results"]; above = d["results"][-1]["id"]
        if len(d["results"]) < 200: return out

def photo(p):
    if not p or (p.get("license_code") or "").lower() not in OK_LICENSES: return None
    lc = p["license_code"].lower()
    url = p.get("medium_url") or (p.get("url") or "").replace("square", "medium")
    return {"url": url, "sq": (p.get("square_url") or p.get("url") or "").replace("square", "small"),
            "attr": p.get("attribution", ""), "license": OK_LICENSES[lc], "license_url": LICENSE_URLS[lc]}

def clean_summary(html):
    if not html: return None
    t = re.sub(r"<[^>]+>", "", html); t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s*\([^()]*\)", "", t)
    s = " ".join(re.split(r"(?<=[.!?])\s+(?=[A-Z])", t)[:2])
    return s[:320].rsplit(" ", 1)[0] + "…" if len(s) > 320 else s

def main():
    geo = Geo(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "geo.json"))
    now = datetime.datetime.now(datetime.timezone.utc)
    sp, drops = {}, Counter()
    for key, label, q in GROUPS:
        obs = observations(q); print(f"group {key}: {len(obs)} raw observations")
        for o in obs:
            t = o.get("taxon") or {}
            if not t or (t.get("rank_level") or 0) > 10: drops["coarser than species"] += 1; continue
            if o.get("obscured") or o.get("geoprivacy") in ("obscured", "private") or o.get("taxon_geoprivacy") in ("obscured", "private"):
                drops["obscured location"] += 1; continue
            if (o.get("positional_accuracy") or 0) > 1000: drops["GPS uncertainty > 1 km"] += 1; continue
            gj = o.get("geojson") or {}
            if not gj.get("coordinates"): drops["no coordinates"] += 1; continue
            lon, lat = gj["coordinates"]
            kind, town = geo.classify(lon, lat)
            if kind in ("water", "island"): drops["on " + ("barrier island" if kind == "island" else "water")] += 1; continue
            sid = t["id"] if t.get("rank_level", 10) >= 10 else t["ancestor_ids"][-2]   # roll subspecies up to species
            s = sp.get(sid)
            if not s:
                s = sp[sid] = {"id": sid, "g": key, "sci": t["name"] if sid == t["id"] else "", "com": (t.get("preferred_common_name") or "") if sid == t["id"] else "",
                               "n": 0, "m": [0]*12, "ph": photo(t.get("default_photo")) if sid == t["id"] else None,
                               "wiki_url": t.get("wikipedia_url") if sid == t["id"] else None,
                               "anc": set(t.get("ancestor_ids", [])), "_k": Counter(), "_t": Counter(), "_last": ("", None)}
            s["n"] += 1; s["_k"][kind] += 1
            if kind == "land" and any(k in s["anc"] for k in MARINE) and geo.coast_dist_m(lon, lat) >= 300:
                s["_k"]["inland"] += 1
            if town: s["_t"][town] += 1
            mo = (o.get("observed_on_details") or {}).get("month")
            if mo: s["m"][mo - 1] += 1
            d = o.get("observed_on") or ""
            if d > s["_last"][0]: s["_last"] = (d, o["id"])
    # marine-only rule
    removed, kept_exc = [], []
    for sid in list(sp):
        s = sp[sid]; hit = [v for k, v in MARINE.items() if k in s["anc"]]
        if not hit: continue
        if s["_k"]["inland"] > 0: kept_exc.append((sid, hit[0])); s["marine_exception"] = True
        else: removed.append((sid, hit[0])); 
    # taxon details: names for rolled-up species, order/family, Wikipedia summary, open-licensed photos
    ids = list(sp)
    for i in range(0, len(ids), 30):
        for t in get("/taxa/" + ",".join(map(str, ids[i:i+30])))["results"]:
            s = sp.get(t["id"])
            if not s: continue
            s["sci"] = t["name"]; s["com"] = t.get("preferred_common_name") or s["com"]
            for a in t.get("ancestors", []):
                if a["rank"] == "order": s["order"] = a["name"]
                if a["rank"] == "family": s["family"] = a["name"]; s["family_com"] = a.get("preferred_common_name") or ""
            s["fact"] = clean_summary(t.get("wikipedia_summary"))
            if t.get("wikipedia_url"): s["wiki_url"] = t["wikipedia_url"]
            if not s["ph"]: s["ph"] = photo(t.get("default_photo"))
            if not s["ph"]:
                for tp in t.get("taxon_photos", []):
                    ph = photo(tp.get("photo"))
                    if ph: s["ph"] = ph; break
        print(f"  taxa {min(i+30, len(ids))}/{len(ids)}")
    removed_info = [{"id": sid, "com": sp[sid]["com"], "sci": sp[sid]["sci"], "rule": r, "n": sp[sid]["n"]} for sid, r in removed]
    exc_info = [{"id": sid, "com": sp[sid]["com"], "sci": sp[sid]["sci"], "rule": r, "n": sp[sid]["n"], "land": sp[sid]["_k"]["inland"]} for sid, r in kept_exc]
    for sid, _ in removed: del sp[sid]
    towns = Counter()
    for s in sp.values():
        k = s.pop("_k"); s["land"] = k["land"]; s["marsh"] = k["marsh"]
        towns.update(s.pop("_t")); d, oid = s.pop("_last"); s.pop("anc")
        if d: s["last_seen"] = d; s["last_obs"] = f"https://www.inaturalist.org/observations/{oid}"
    out = {"pulled_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "pulled_date": datetime.datetime.now().strftime("%Y-%m-%d"),
           "area": {"label": "Mainland Linwood, NJ & immediate surroundings", "radius_km": RADIUS_KM,
                    "towns": [t for t, c in towns.most_common() if c >= 5]},
           "source": "iNaturalist API v1 — research-grade observations; locations classified with OpenStreetMap data",
           "dropped_observations": dict(drops), "removed_marine": removed_info, "marine_kept_on_land": exc_info,
           "groups": [{"key": k, "label": l} for k, l, _ in GROUPS],
           "species": sorted(sp.values(), key=lambda s: -s["n"])}
    with open("data/species.json", "w") as f: json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
    print("species:", len(sp), "dropped obs:", dict(drops), "towns:", dict(towns))
    print("removed by marine rule:", [(r["com"], r["n"]) for r in removed_info]); print("kept (land record):", [(r["com"], r["land"]) for r in exc_info])

if __name__ == "__main__":
    main()
