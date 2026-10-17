"""Pure-python geometry helpers (no dependencies) for classifying observation points
as mainland land / marsh / tidal or open water / barrier island, using OpenStreetMap
data pre-extracted into data/geo.json by scripts/fetch_osm.py."""
import json, math

ISLAND_TOWNS = {"Longport", "Margate City", "Ventnor City", "Atlantic City", "Ocean City", "Brigantine"}
MARSH = {"saltmarsh", "marsh", "tidalflat", "reedbed", "wet_meadow", None}

def pip(x, y, ring):
    inside, n = False, len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-300) + xi:
            inside = not inside
        j = i
    return inside

def in_poly(x, y, poly):
    """poly = {"outer":[ring..], "inner":[ring..], "bbox":[minx,miny,maxx,maxy]}"""
    b = poly["bbox"]
    if not (b[0] <= x <= b[2] and b[1] <= y <= b[3]): return False
    if not any(pip(x, y, r) for r in poly["outer"]): return False
    return not any(pip(x, y, r) for r in poly.get("inner", []))

class Geo:
    def __init__(self, path="data/geo.json"):
        g = json.load(open(path))
        self.towns, self.water, self.wetland = g["towns"], g["water"], g["wetland"]
        self.k = math.cos(math.radians(39.34))
        self.chains = [[(lon * self.k, lat) for lon, lat in c] for c in g["coast"]]

    def coast_side_is_water(self, lon, lat, max_m=3000):
        """OSM coastline convention: land on the LEFT of the way direction, water on the right.
        Uses the nearest coastline segment (with the standard corner rule at vertices)."""
        P = (lon * self.k, lat); best = None
        for c in self.chains:
            closed = c[0] == c[-1]
            for i in range(len(c) - 1):
                A, B = c[i], c[i + 1]
                dx, dy = B[0] - A[0], B[1] - A[1]
                L = dx * dx + dy * dy or 1e-30
                t = max(0.0, min(1.0, ((P[0] - A[0]) * dx + (P[1] - A[1]) * dy) / L))
                qx, qy = A[0] + t * dx, A[1] + t * dy
                d = (P[0] - qx) ** 2 + (P[1] - qy) ** 2
                if best is None or d < best[0] - 1e-18:
                    best = (d, c, i, t, closed)
        if best is None or math.sqrt(best[0]) * 111000 > max_m: return False
        d, c, i, t, closed = best
        def left(A, B): return (B[0] - A[0]) * (P[1] - A[1]) - (B[1] - A[1]) * (P[0] - A[0]) > 0
        A, B = c[i], c[i + 1]
        if 0 < t < 1: return not left(A, B)
        # nearest point is a vertex: combine the two adjacent segments
        if t == 0: U, V, W = (c[i - 1] if i > 0 else (c[-2] if closed else None)), A, B
        else: U, V, W = A, B, (c[i + 2] if i + 2 < len(c) else (c[1] if closed else None))
        if U is None: return not left(V, W)
        if W is None: return not left(U, V)
        l1, l2 = left(U, V), left(V, W)
        turn = (V[0] - U[0]) * (W[1] - V[1]) - (V[1] - U[1]) * (W[0] - V[0])
        land = (l1 and l2) if turn > 0 else (l1 or l2)
        return not land

    def coast_dist_m(self, lon, lat):
        P = (lon * self.k, lat); best = 1e9
        for c in self.chains:
            for i in range(len(c) - 1):
                A, B = c[i], c[i + 1]; dx, dy = B[0] - A[0], B[1] - A[1]
                L = dx * dx + dy * dy or 1e-30
                t = max(0.0, min(1.0, ((P[0] - A[0]) * dx + (P[1] - A[1]) * dy) / L))
                best = min(best, (P[0] - A[0] - t * dx) ** 2 + (P[1] - A[1] - t * dy) ** 2)
        return best ** 0.5 * 111000

    def town(self, lon, lat):
        for name, poly in self.towns.items():
            if in_poly(lon, lat, poly): return name
        return None

    def classify(self, lon, lat):
        """-> (kind, town) with kind in land | marsh | water | island"""
        t = self.town(lon, lat)
        if t in ISLAND_TOWNS: return "island", t
        if self.coast_side_is_water(lon, lat): return "water", t
        for w in self.water:
            if in_poly(lon, lat, w): return "water", t
        for w in self.wetland:
            if in_poly(lon, lat, w): return ("marsh" if w.get("type") in MARSH else "land"), t
        return "land", t
