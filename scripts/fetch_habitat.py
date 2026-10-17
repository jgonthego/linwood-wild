#!/usr/bin/env python3
"""Habitat around the center point from NJDEP Land Use/Land Cover 2015 (NJ GIS, free ArcGIS REST),
sampled on a 25 m grid within 0.5 km and 2 km. Writes ONLY rounded, non-identifying descriptors
to data/habitat.json (no coordinates, no distances)."""
import json, math, sys, os, urllib.request, urllib.parse
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zones import home
from geo import pip
LU = "https://mapsdep.nj.gov/arcgis/rest/services/Features/Land_lu/MapServer/13/query"

def main():
    lat, lng = home()
    q = urllib.parse.urlencode({"geometry": f"{lng},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326, "distance": 2100,
        "units": "esriSRUnit_Meter", "spatialRel": "esriSpatialRelIntersects", "outFields": "LABEL15,TYPE15",
        "returnGeometry": "true", "outSR": 4326, "geometryPrecision": 6, "f": "json"})
    fs = json.load(urllib.request.urlopen(LU + "?" + q, timeout=120))["features"]
    polys = []
    for f in fs:
        r = f["geometry"]["rings"]; xs = [p[0] for x in r for p in x]; ys = [p[1] for x in r for p in x]
        polys.append((f["attributes"], r, (min(xs), min(ys), max(xs), max(ys))))
    def at(x, y):
        for a, r, b in polys:
            if b[0] <= x <= b[2] and b[1] <= y <= b[3] and sum(pip(x, y, ring) for ring in r) % 2: return a
    def bucket(a):
        if not a: return "other"
        L, T = a["LABEL15"].upper(), a["TYPE15"].upper()
        if "SALINE" in L or "COASTAL" in L: return "salt marsh"
        if "TIDAL" in L: return "bay & tidal water"
        if T == "WATER": return "fresh water"
        if T == "WETLANDS": return "freshwater wetland"
        if "RESIDENTIAL" in L: return "residential yards"
        if T == "URBAN": return "other developed"
        if T == "FOREST": return "forest"
        return T.lower()
    k = math.cos(math.radians(lat)); out = {}
    for R in (500, 2000):
        c = Counter(); n = 0
        for i in range(-R, R + 1, 25):
            for j in range(-R, R + 1, 25):
                if i * i + j * j > R * R: continue
                c[bucket(at(lng + j / (111320 * k), lat + i / 110540))] += 1; n += 1
        out[f"{R}m"] = {b: int(5 * round(20 * v / n)) for b, v in c.most_common() if 100 * v / n >= 2.5}
    forest2k = sum(v for b, v in out["2000m"].items() if b == "forest")
    out["source"] = "NJDEP Land Use/Land Cover 2015 (NJGIN), sampled on a 25 m grid; percentages rounded to 5%"
    out["notes"] = ["Suburban yards on the edge of the back-bay salt marsh",
                    "Tidal creeks and bay water within 2 km",
                    "Woods: only small patches (under 5%) within 2 km — no pine-barrens forest" if forest2k < 5 else "Some forest within 2 km"]
    json.dump(out, open("data/habitat.json", "w"), indent=1); print(out)

if __name__ == "__main__":
    main()
