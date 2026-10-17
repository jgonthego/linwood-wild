#!/usr/bin/env python3
"""One-off: pull OpenStreetMap coastline, water, wetland and municipal boundaries around
Linwood, NJ via Overpass and save a compact data/geo.json (OSM data (c) OpenStreetMap
contributors, ODbL). Re-run only if the area changes."""
import json, math, urllib.request, urllib.parse
BBOX = "39.29,-74.645,39.39,-74.515"
Q = f"""[out:json][timeout:180];(
way["natural"="water"]({BBOX});relation["natural"="water"]({BBOX});
way["natural"="wetland"]({BBOX});relation["natural"="wetland"]({BBOX});
way["natural"="coastline"]({BBOX});
relation["boundary"="administrative"]["admin_level"="8"]({BBOX}););out geom;"""

def key(p): return (round(p[0], 7), round(p[1], 7))

def join(lines):
    """Join open line strings into chains/rings by matching endpoints (direction preserved where possible)."""
    lines = [l[:] for l in lines if len(l) > 1]; out = []
    while lines:
        cur = lines.pop(0); changed = True
        while changed and key(cur[0]) != key(cur[-1]):
            changed = False
            for i, l in enumerate(lines):
                if key(l[0]) == key(cur[-1]): cur += l[1:]
                elif key(l[-1]) == key(cur[0]): cur = l + cur[1:]
                elif key(l[-1]) == key(cur[-1]): cur += l[::-1][1:]
                elif key(l[0]) == key(cur[0]): cur = l[::-1] + cur[1:]
                else: continue
                lines.pop(i); changed = True; break
        out.append(cur)
    return out

def bbox(rings):
    xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    return [min(xs), min(ys), max(xs), max(ys)]

def area_m2(r):
    k = math.cos(math.radians(39.34)) * 111320; s = 0
    for i in range(len(r) - 1): s += r[i][0] * k * r[i + 1][1] * 110540 - r[i + 1][0] * k * r[i][1] * 110540
    return abs(s) / 2

def r6(r): return [[round(x, 6), round(y, 6)] for x, y in r]

def main():
    req = urllib.request.Request("https://overpass-api.de/api/interpreter",
        data=urllib.parse.urlencode({"data": Q}).encode(), headers={"User-Agent": "linwood-wild/1.0"})
    els = json.load(urllib.request.urlopen(req, timeout=240))["elements"]
    geo = {"towns": {}, "water": [], "wetland": [], "coast": [], "note": "OSM data (c) OpenStreetMap contributors, ODbL"}
    coast = []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way":
            ring = [[p["lon"], p["lat"]] for p in e["geometry"]]
            if t.get("natural") == "coastline": coast.append(ring); continue
            if ring[0] != ring[-1]: continue
            poly = {"outer": [r6(ring)], "inner": [], "bbox": bbox([ring])}
        else:
            outer = join([[[p["lon"], p["lat"]] for p in m["geometry"]] for m in e["members"] if m["type"] == "way" and m.get("role") in ("outer", "") and m.get("geometry")])
            inner = join([[[p["lon"], p["lat"]] for p in m["geometry"]] for m in e["members"] if m["type"] == "way" and m.get("role") == "inner" and m.get("geometry")])
            outer = [r for r in outer if key(r[0]) == key(r[-1])]; inner = [r for r in inner if key(r[0]) == key(r[-1])]
            if not outer: continue
            poly = {"outer": [r6(r) for r in outer], "inner": [r6(r) for r in inner], "bbox": bbox(outer)}
        if t.get("boundary") == "administrative": geo["towns"][t.get("name", "?")] = poly
        elif t.get("natural") == "water":
            # small neighbourhood ponds / stormwater basins are kept as "land" (yard-scale habitat);
            # rivers, lakes, tidal channels and any water body over 2 ha count as water
            a = sum(area_m2(r) for r in poly["outer"])
            if t.get("water") in ("pond", "basin", "reservoir") and a < 50000: continue
            if a < 20000 and t.get("water") is None: continue
            poly["type"] = t.get("water"); geo["water"].append(poly)
        elif t.get("natural") == "wetland":
            poly["type"] = t.get("wetland"); geo["wetland"].append(poly)
    geo["coast"] = [r6(c) for c in join(coast)]
    json.dump(geo, open("data/geo.json", "w"), separators=(",", ":"))
    print({k: len(v) for k, v in geo.items() if k != "note"}, list(geo["towns"]))

if __name__ == "__main__":
    main()
