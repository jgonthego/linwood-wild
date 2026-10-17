"""Search zones around the center point (the point itself is read from the HOME_LAT/HOME_LNG
environment variables or data/home.private.json, which is git-ignored -- never published)."""
import json, math, os

# Line running along the bay side of the barrier islands (Absecon Island, Ocean City).
# Anything east/south-east of it is island, beach or ocean and is excluded from the "mainland" zone.
# South of 39.34 the points follow the westernmost edge of the Margate/Longport/Ocean City municipal
# boundaries (OpenStreetMap); north of that (Ventnor/Atlantic City) they follow the bay shore.
BACKBAY = [(39.48, -74.36), (39.40, -74.43), (39.36, -74.47), (39.35, -74.495), (39.34, -74.513), (39.33, -74.518),
           (39.32, -74.527), (39.31, -74.589), (39.30, -74.601), (39.28, -74.612), (39.25, -74.627), (39.22, -74.654), (39.17, -74.71)]

def home():
    if os.environ.get("HOME_LAT"): return float(os.environ["HOME_LAT"]), float(os.environ["HOME_LNG"])
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "home.private.json")
    if os.path.exists(p): d = json.load(open(p)); return d["lat"], d["lng"]
    return 39.34, -74.58   # fallback: Linwood town centre (rounded)

def line_lon(lat):
    pts = BACKBAY
    if lat >= pts[0][0]: return pts[0][1]
    for (a1, o1), (a2, o2) in zip(pts, pts[1:]):
        if a2 <= lat <= a1: return o1 + (o2 - o1) * (lat - a1) / (a2 - a1)
    return pts[-1][1]

def mainland_ring(lat0, lng0, r_km, n=96):
    """Circle clipped to the mainland side of BACKBAY, counter-clockwise, as [(lng, lat), ...] closed."""
    k = math.cos(math.radians(lat0))
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        lat = lat0 + r_km / 110.54 * math.sin(a); lng = lng0 + r_km / (111.32 * k) * math.cos(a)
        pts.append((lng, lat, lng < line_lon(lat)))
    if all(p[2] for p in pts):
        ring = [(x, y) for x, y, _ in pts]
    else:
        i0 = next(i for i in range(n) if not pts[i][2] and pts[(i + 1) % n][2])   # first mainland point after the cut
        arc = []; i = (i0 + 1) % n
        while pts[i][2]: arc.append(pts[i][:2]); i = (i + 1) % n
        top, bot = arc[0][1], arc[-1][1]
        # close along the bay line from the southern end back up to the northern end
        mid = [(lng, lat) for lat, lng in sorted(BACKBAY) if bot < lat < top
               and ((lng - lng0) * 111.32 * k) ** 2 + ((lat - lat0) * 110.54) ** 2 < r_km ** 2]
        ring = [(line_lon(top), top)] + arc + [(line_lon(bot), bot)] + mid
    ring = [(round(x, 5), round(y, 5)) for x, y in ring]
    return ring + [ring[0]]

def mainland_wkt(lat0, lng0, r_km):
    return "POLYGON((" + ",".join(f"{x} {y}" for x, y in mainland_ring(lat0, lng0, r_km)) + "))"

def circle_wkt(lat0, lng0, r_km, n=48):
    k = math.cos(math.radians(lat0)); ring = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ring.append((round(lng0 + r_km / (111.32 * k) * math.cos(a), 5), round(lat0 + r_km / 110.54 * math.sin(a), 5)))
    ring.append(ring[0])
    return "POLYGON((" + ",".join(f"{x} {y}" for x, y in ring) + "))"
