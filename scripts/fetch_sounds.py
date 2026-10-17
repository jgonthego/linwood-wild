#!/usr/bin/env python3
"""One short, openly licensed bird recording per bird species, from iNaturalist
research-grade observations with sounds. Only CC0 / CC BY / CC BY-SA / CC BY-NC.
Preference: our own area -> New Jersey -> eastern US -> anywhere.
xeno-canto API v3 requires an account key, so it is not used.
Clips are trimmed to <=15 s, mono, 48 kbps MP3 with ffmpeg into audio/, metadata in data/sounds.json."""
import json, os, re, subprocess, sys, tempfile, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from fetch_data import get, BASE, OK_LICENSES, LICENSE_URLS, UA

TIERS = [("Recorded in this area", {"lat": BASE["lat"], "lng": BASE["lng"], "radius": BASE["radius"]}),
         ("Recorded in New Jersey", {"place_id": 51}),
         ("Recorded in the eastern US", {"swlat": 24, "swlng": -90, "nelat": 48, "nelng": -66}),
         ("Recorded outside the eastern US", {})]
MAX_S = 15

def kind_of(o):
    for f in o.get("ofvs", []):
        n, v = (f.get("name") or "").lower(), (f.get("value") or "").lower()
        if any(k in n for k in ("vocal", "call", "song", "sound")):
            if "song" in v and "call" not in v: return "Song"
            if "call" in v and "song" not in v: return "Call"
    desc = (o.get("description") or "").lower()
    song = re.search(r"\bsongs?\b|\bsinging\b", desc); call = re.search(r"\bcalls?\b|\bcalling\b", desc)
    if song and not call: return "Song"
    if call and not song: return "Call"
    return None

def pick(taxon_id):
    for label, extra in TIERS:
        d = get("/observations", {"taxon_id": taxon_id, "sounds": "true", "quality_grade": "research",
                                  "sound_license": ",".join(OK_LICENSES), "order_by": "votes", "per_page": 10, **extra})
        for o in d["results"]:
            # never substitute: the observation's community taxon must be this species (or a subspecies of it)
            t = o.get("taxon") or {}
            if t.get("id") != taxon_id and taxon_id not in (t.get("ancestor_ids") or []): continue
            for s in o.get("sounds", []):
                lc = (s.get("license_code") or "").lower()
                if lc in OK_LICENSES and s.get("file_url"):
                    return label, o, s, lc
    return None

def main():
    sp = json.load(open("data/species.json"))["species"]
    birds = [s for s in sp if s["g"] == "birds"]
    os.makedirs("audio", exist_ok=True)
    old = json.load(open("data/sounds.json")) if os.path.exists("data/sounds.json") else {}
    out = {}
    for i, b in enumerate(birds):
        key = str(b["id"]); fn = f"audio/{b['id']}.mp3"
        if key in old and os.path.exists(fn): out[key] = old[key]; continue
        r = pick(b["id"])
        if not r: print(f"[{i+1}/{len(birds)}] none: {b['com']}"); continue
        label, o, s, lc = r
        with tempfile.NamedTemporaryFile(suffix=".src") as tmp:
            try:
                req = urllib.request.Request(s["file_url"], headers={"User-Agent": UA})
                tmp.write(urllib.request.urlopen(req, timeout=90).read()); tmp.flush()
                dur = 0
                for lead in ("silenceremove=start_periods=1:start_threshold=-50dB,", ""):
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name,
                        "-af", f"{lead}atrim=0:{MAX_S},dynaudnorm,afade=t=out:st={MAX_S-0.6}:d=0.6",
                        "-ac", "1", "-ar", "32000", "-b:a", "48k", fn], check=True, timeout=120)
                    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", fn],
                                               capture_output=True, text=True).stdout.strip() or 0)
                    if dur >= 1: break
                if dur < 1: raise ValueError("clip too short after trim")
            except Exception as e:
                print(f"[{i+1}] fail {b['com']}: {e}");
                if os.path.exists(fn): os.remove(fn)
                continue
        out[key] = {"file": fn, "attr": s.get("attribution", ""), "license": OK_LICENSES[lc], "license_url": LICENSE_URLS[lc],
                    "obs": f"https://www.inaturalist.org/observations/{o['id']}", "where": label,
                    "date": o.get("observed_on"), "kind": kind_of(o), "dur": round(dur, 1)}
        print(f"[{i+1}/{len(birds)}] {b['com']}: {label}, {out[key]['license']}, {dur:.1f}s")
        json.dump(out, open("data/sounds.json", "w"), indent=0, ensure_ascii=False)
    json.dump(out, open("data/sounds.json", "w"), indent=0, ensure_ascii=False)
    print("birds with sound:", len(out), "of", len(birds))

if __name__ == "__main__":
    main()
