#!/usr/bin/env python3
"""Build docs/ (static site) from data/species.json + src/. No dependencies."""
import json, shutil, os, datetime, hashlib

RAPTOR = {"Accipitriformes", "Falconiformes", "Strigiformes", "Cathartiformes"}
WATER = {"Charadriiformes", "Pelecaniformes", "Anseriformes", "Gruiformes", "Gaviiformes",
         "Podicipediformes", "Suliformes", "Procellariiformes", "Ciconiiformes",
         "Phoenicopteriformes", "Coraciiformes", "Phaethontiformes"}
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

def main():
    d = json.load(open("data/species.json"))
    for s in d["species"]:
        if s["g"] == "birds":
            o = s.get("order", "")
            s["cat"] = "raptor" if o in RAPTOR else "marsh" if o in WATER else "yard"
    snd = json.load(open("data/sounds.json")) if os.path.exists("data/sounds.json") else {}
    for s in d["species"]:
        a = snd.get(str(s["id"]))
        if a and os.path.exists(a["file"]): s["snd"] = a
    d["sound_count"] = sum(1 for s in d["species"] if s.get("snd"))
    if os.path.exists("docs"): shutil.rmtree("docs")
    os.makedirs("docs/assets/fonts"); os.makedirs("docs/data")
    for f in os.listdir("src/fonts"): shutil.copy(f"src/fonts/{f}", "docs/assets/fonts/")
    if os.path.isdir("audio"): shutil.copytree("audio", "docs/audio")
    shutil.copy("src/style.css", "docs/assets/style.css"); shutil.copy("src/app.js", "docs/assets/app.js")
    payload = json.dumps(d, separators=(",", ":"), ensure_ascii=False)
    open("docs/data/species.json", "w").write(payload)
    ver = hashlib.sha1((payload + open("src/app.js").read() + open("src/style.css").read()).encode()).hexdigest()[:8]
    m = datetime.date.today().month - 1
    sp = d["species"]
    rep = {"VER": ver, "RADIUS": str(d["area"]["radius_km"]), "TOTAL": f"{len(sp):,}",
           "BIRDS": str(sum(1 for s in sp if s["g"] == "birds")), "OBS": f"{sum(s['n'] for s in sp):,}",
           "TOWNS": " · ".join(d["area"]["towns"]), "MONTH": MONTHS[m], "MONTHIDX": str(m),
           "DATE": d["pulled_date"], "SOUNDS": str(d["sound_count"])}
    html = open("src/index.html").read()
    for k, v in rep.items(): html = html.replace("{{" + k + "}}", v)
    open("docs/index.html", "w").write(html)
    open("docs/.nojekyll", "w").write("")
    print("built docs/:", len(sp), "species, v", ver)

if __name__ == "__main__":
    main()
