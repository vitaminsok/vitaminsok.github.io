# Vita site (GitHub Pages)

Brand: **Vita** — micronutrients, decoded — evidence, not advice.
Address: `https://vita.sok.lv` (DNS + Pages registration by kraser).

## Publishing path (same as Paper Sky / Sky Chapter)
1. Gather keyless evidence: NIH ODS, EFSA, WHO, Europe PMC/PubMed, Open Food Facts, USDA.
2. Write `_weekly/<YYYY-MM-DD>-<slug>.md` with `date`, `stamp` (`YYYY-MM-DD 06:35`), `title`, `description`, `cold_open`, `sources_checked`, `article: true`. One article per day.
3. `python3 scripts/build_rss.py`
4. Publish with `~/.hermes/scripts/publish_pages.py` after the repo is added to `github-publish-policy.json`.
5. `python3 scripts/indexnow.py` — SHA-256 manifest, delta submit only; public key file `<key>.txt`, POST includes `keyLocation`.
6. `python3 scripts/audit_page.py` — source + live checks, writes `data/audit-<date>.json`.
7. Browser pass: texts, computed styles, screenshot. One review row with `expected`/`review_after`.

## Hard rules
Informational only; no dose from us; norms only as dated citations from NIH/EFSA/WHO; no supplement sales, no partner links; disclaimer on every page. Vitamins are organic molecules, Ca/Mg are mineral elements — never blur the categories.

## Needs from kraser
- GitHub org/repo name for the Pages repo (to add to publish policy).
- DNS for `vita.sok.lv` → GitHub Pages.
