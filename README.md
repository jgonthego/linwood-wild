# Linwood Wild

Static site showing every wildlife species with research-grade [iNaturalist](https://www.inaturalist.org) observations within ~15 km of Linwood, NJ (South Jersey shore, Atlantic County): birds, mammals, reptiles & amphibians, insects, and spiders & other bugs.

- `scripts/fetch_data.py` pulls data from the free iNaturalist API v1 (no key) into `data/species.json`
  (species counts, per-month counts, open-licensed photos only: CC0 / CC BY / CC BY-SA / CC BY-NC, Wikipedia summaries via iNat).
- `build.py` builds `docs/` from `src/` + data. No dependencies.
- GitHub Actions deploys to Pages on push, and refreshes the data monthly.

Fonts: Anton and Space Grotesk, SIL Open Font License (see `src/fonts`).
Photos remain the property of their photographers under the license shown with each photo.
