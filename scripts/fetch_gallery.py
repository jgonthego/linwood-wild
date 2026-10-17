#!/usr/bin/env python3
"""Photo galleries (data/gallery.json) from the free iNaturalist API v1. No key.

Birds: research-grade observations annotated (by iNaturalist users) as
  Sex = Male   (controlled term 9, value 11)
  Sex = Female (term 9, value 10)
  Life Stage = Juvenile (term 1, value 8)
ordered by community votes, photo licence CC0 / CC BY / CC BY-SA / CC BY-NC only.
A label is attached to a photo ONLY when that observation carries the annotation with a
non-negative vote score; we never infer sex, age, plumage or pose from anything else.
iNaturalist has no controlled term for flight / perched / plumage, so the extra
"more photos" (the taxon's curated iNaturalist photos) stay unlabeled.
Other groups: the curated taxon photos only (unlabeled multi-photo gallery).

Incremental: entries already in data/gallery.json are kept unless older than --max-age days,
so the monthly workflow only fetches new species (time-boxed with --budget seconds)."""
import json, os, sys, time, datetime, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_data import get, OK_LICENSES

OUT = "data/gallery.json"
LIC = ",".join(OK_LICENSES)
QUERIES = [("m", {"term_id": 9, "term_value_id": 11}), ("f", {"term_id": 9, "term_value_id": 10}),
           ("j", {"term_id": 1, "term_value_id": 8})]
PER = 4          # photos per labeled category
EXTRA = 5        # unlabeled taxon photos
BAD_EVIDENCE = {23, 25, 26, 27, 28, 30, 31, 35}   # feather, scat, track, bone, molt, egg, hair, construction

def ann(o):
    """{attribute_id: value_id} for annotations with vote_score >= 0."""
    return {a["controlled_attribute_id"]: a["controlled_value_id"] for a in o.get("annotations", [])
            if (a.get("vote_score") or 0) >= 0}

def ph(p, obs=None, labels=None):
    lc = (p.get("license_code") or "").lower()
    if lc not in OK_LICENSES or not p.get("url"): return None
    u = p["url"].replace("/square.", "/medium.")
    if "/medium." not in u: return None
    r = {"u": u, "a": p.get("attribution", ""), "l": lc, "id": p["id"]}
    if obs: r["o"] = obs
    if labels: r["t"] = labels
    return r

def labels_for(a):
    t = []
    if a.get(9) == 11: t.append("Male")
    if a.get(9) == 10: t.append("Female")
    if a.get(1) == 8: t.append("Juvenile")
    elif a.get(1) == 2: t.append("Adult")
    return t

def bird_entry(tid, seen):
    e = {}
    for key, extra in QUERIES:
        d = get("/observations", {"taxon_id": tid, "quality_grade": "research", "photo_license": LIC, "photos": "true",
                                  "order_by": "votes", "per_page": 12, **extra})
        e["n" + key] = d.get("total_results", 0)   # how many such annotated observations exist on iNat
        out = []
        for o in d["results"]:
            t = o.get("taxon") or {}
            if t.get("id") != tid and tid not in (t.get("ancestor_ids") or []): continue
            a = ann(o)
            if a.get(extra["term_id"]) != extra["term_value_id"]: continue     # annotation must really be there
            if a.get(17) == 19 or a.get(22) in BAD_EVIDENCE: continue          # dead birds, feathers, nests...
            for p in o.get("photos", []):
                if p["id"] in seen: continue
                x = ph(p, o["id"], labels_for(a))
                if x: seen.add(p["id"]); out.append(x); break               # one photo per observation (different birds)
            if len(out) >= PER: break
        if out: e[key] = out
    return e

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age", type=int, default=100000); ap.add_argument("--budget", type=int, default=100000)
    ap.add_argument("--birds-only", action="store_true")
    args = ap.parse_args()
    t0 = time.time(); today = datetime.date.today()
    sp = json.load(open("data/species.json"))["species"]
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    out = {}
    todo_birds = []
    for s in sp:
        k = str(s["id"]); o = old.get(k)
        fresh = o and (today - datetime.date.fromisoformat(o.get("d", "2000-01-01"))).days <= args.max_age
        need_bird = s["g"] == "birds" and not (fresh and "nm" in o)
        if fresh and not need_bird: out[k] = o
        else: todo_birds.append(s) if s["g"] == "birds" else None
        if not fresh and s["g"] != "birds": out.pop(k, None)
    # taxon photos for everything missing them (30 taxa per request)
    need_tp = [s for s in sp if not (out.get(str(s["id"])) or {}).get("x")]
    for i in range(0, len(need_tp), 30):
        if args.birds_only: break
        if time.time() - t0 > args.budget: print("budget hit (taxon photos)"); break
        chunk = need_tp[i:i + 30]
        for t in get("/taxa/" + ",".join(str(s["id"]) for s in chunk))["results"]:
            e = out.setdefault(str(t["id"]), {"d": today.isoformat()})
            xs = []
            for tp in t.get("taxon_photos", []):
                x = ph(tp.get("photo") or {})
                if x: xs.append(x)
                if len(xs) >= EXTRA + 1: break
            e["x"] = xs
        print("taxon photos", min(i + 30, len(need_tp)), "/", len(need_tp))
    for i, s in enumerate(todo_birds):
        if time.time() - t0 > args.budget: print("budget hit; birds left:", len(todo_birds) - i); break
        k = str(s["id"]); e = out.setdefault(k, {"d": today.isoformat()})
        seen = set()
        e.update(bird_entry(s["id"], seen)); e["d"] = today.isoformat()
        if i % 10 == 0:
            json.dump(out, open(OUT, "w"), separators=(",", ":"), ensure_ascii=False)
        print(f"[{i+1}/{len(todo_birds)}] {s.get('com')}: male {len(e.get('m',[]))}/{e['nm']}, female {len(e.get('f',[]))}/{e['nf']}, juv {len(e.get('j',[]))}/{e['nj']}")
    ids = {str(s["id"]) for s in sp}
    out = {k: v for k, v in out.items() if k in ids}
    json.dump(out, open(OUT, "w"), separators=(",", ":"), ensure_ascii=False)
    b = [out.get(str(s["id"]), {}) for s in sp if s["g"] == "birds"]
    print("birds with male+female photos:", sum(1 for e in b if e.get("m") and e.get("f")), "of", len(b))

if __name__ == "__main__":
    main()
