#!/usr/bin/env python3
"""Build docs/ (static site) from data/species.json + src/. No dependencies."""
import json, shutil, os, datetime, hashlib

RAPTOR = {"Accipitriformes", "Falconiformes", "Strigiformes", "Cathartiformes"}
WATER = {"Charadriiformes", "Pelecaniformes", "Anseriformes", "Gruiformes", "Gaviiformes",
         "Podicipediformes", "Suliformes", "Procellariiformes", "Ciconiiformes",
         "Phoenicopteriformes", "Coraciiformes", "Phaethontiformes"}
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]

PFX = "https://inaturalist-open-data.s3.amazonaws.com/photos/"

def build_extras(d):
    """docs/data/gallery.json (compact photo arrays) + docs/data/traits.json, from the committed/refreshed data files."""
    ids = {s["id"] for s in d["species"]}
    g = json.load(open("data/gallery.json")) if os.path.exists("data/gallery.json") else {}
    tr = json.load(open("data/traits.json")) if os.path.exists("data/traits.json") else {}
    def c(p, lab=True):
        u = p["u"].replace(PFX, "@")
        r = [u, p["a"], p["l"], p.get("o")]
        if lab and p.get("t"): r.append(p["t"])
        return r
    out = {}
    for k, e in g.items():
        if int(k) not in ids: continue
        o = {key: [c(p) for p in e[key]] for key in ("m", "f", "j") if e.get(key)}
        if e.get("x"): o["x"] = [c(p, False)[:3] for p in e["x"]]
        for key in ("nm", "nf", "nj"):
            if key in e: o[key] = e[key]
        out[k] = o
    json.dump(out, open("docs/data/gallery.json", "w"), separators=(",", ":"), ensure_ascii=False)
    tout = {k: {x: v[x] for x in ("len", "c", "fc", "k", "b", "h", "q", "sex", "wurl") if v.get(x)} for k, v in tr.items() if int(k) in ids}
    json.dump(tout, open("docs/data/traits.json", "w"), separators=(",", ":"), ensure_ascii=False)
    birds = [str(s["id"]) for s in d["species"] if s["g"] == "birds"]
    mf = sum(1 for b in birds if out.get(b, {}).get("m") and out.get(b, {}).get("f"))
    return mf, sum(1 for b in birds if tout.get(b, {}).get("sex")), sum(1 for b in birds if b in tout)

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
    shutil.copy("src/extra.js", "docs/assets/extra.js")
    mf, sexn, ntr = build_extras(d)
    payload = json.dumps(d, separators=(",", ":"), ensure_ascii=False)
    open("docs/data/species.json", "w").write(payload)
    ver = hashlib.sha1((payload + open("src/app.js").read() + open("src/extra.js").read() + open("src/style.css").read()
                        + open("docs/data/gallery.json").read() + open("docs/data/traits.json").read()).encode()).hexdigest()[:8]
    m = datetime.date.today().month - 1
    sp = d["species"]
    hab = json.load(open("data/habitat.json"))
    def habline(key, label):
        parts = [f"~{v}% {k}" for k, v in hab[key].items()]
        return f"<b>{label}:</b> " + ", ".join(parts) + "."
    lik = sum(1 for s in sp if s["lik"] == "likely")
    recs = sum(s["A"] + s["B"] + s["C"] for s in sp)  # (zones nest, so this over-counts; only used as "tens of thousands")
    recs_c = sum(s["C"] for s in sp)
    rep = {"VER": ver, "TOTAL": f"{len(sp):,}", "LIKELY": str(lik),
           "BIRDS": str(sum(1 for s in sp if s["g"] == "birds")), "RECORDS": f"{recs_c:,}",
           "MONTH": MONTHS[m], "DATE": d["pulled_date"], "SOUNDS": str(d["sound_count"]),
           "HAB500": habline("500m", "Within 0.5 km"), "HAB2K": habline("2000m", "Within 2 km"),
           "HABNOTES": "".join(f"<li>{n}</li>" for n in hab["notes"]), "HABSRC": hab["source"],
           "RULE_BIRDS": d["rules"]["birds"], "RULE_OTHER": d["rules"]["other"],
           "REMOVED": str(len(d["removed_marine"])), "MF": str(mf), "SEXNOTES": str(sexn), "TRAITS": str(ntr), "UNMATCHED": str(len(d["unmatched_names"]))}
    html = open("src/index.html").read()
    for k, v in rep.items(): html = html.replace("{{" + k + "}}", v)
    open("docs/index.html", "w").write(html)
    open("docs/.nojekyll", "w").write("")
    print("built docs/:", len(sp), "species, v", ver)

if __name__ == "__main__":
    main()
