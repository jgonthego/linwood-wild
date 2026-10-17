# Linwood Wild

Static site listing every wildlife species you could possibly see around Linwood, NJ,
rated **Likely / Possible / Rare** from real records:

- `scripts/fetch_possible.py` counts GBIF occurrence records since 2000 (eBird EOD, iNaturalist research-grade,
  museum specimens) in rings of 2 km, 8 km and 15 km around a fixed center point (mainland only; the barrier islands
  are cut off along the back-bay line in `scripts/zones.py`), applies the likelihood rules, drops ocean-only
  taxa, and adds names, open-licensed photos and Wikipedia summaries from iNaturalist.
- `scripts/fetch_habitat.py` summarises NJDEP Land Use/Land Cover 2015 around the point (rounded % only).
- `scripts/fetch_sounds.py` adds one openly licensed iNaturalist recording per bird (trimmed with ffmpeg).
- `build.py` builds `docs/`; GitHub Actions deploys to Pages and refreshes the data monthly.

The center point is never published: it lives in the git-ignored `data/home.private.json` locally and in the
`HOME_LAT` / `HOME_LNG` repository secrets for the monthly refresh.

Fonts: Anton and Space Grotesk (SIL OFL). Photos and recordings belong to their authors under the license shown.
OSM data (c) OpenStreetMap contributors (ODbL).
