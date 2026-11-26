#!/usr/bin/env python3
"""Vita post-publish audit — texts, view-layer markup, citations. Uses curl, not urllib."""
import argparse, datetime, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "data"
DOMAIN = "https://vita.sok.lv"
KEY_FILE = "vita574350b961c7d455.txt"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

def fetch(url, tries=3, wait=10):
    last = None
    for i in range(tries):
        try:
            p = subprocess.run(["curl", "-sS", "-A", UA, "--max-time", "25",
                                "-w", "\n__STATUS__%{http_code}", url],
                               capture_output=True, text=True, timeout=30)
            body, _, code = p.stdout.rpartition("\n__STATUS__")
            return int(code.strip() or 0), body
        except Exception as e:
            last = type(e).__name__
        if i + 1 < tries:
            import time; time.sleep(wait)
    return 0, last or "no response"

def latest_date():
    ds = []
    for p in (ROOT / "_weekly").glob("*.md"):
        m = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", p.read_text(encoding="utf-8"), re.M)
        if m: ds.append(m.group(1))
    return max(ds) if ds else None

def meta(text):
    out = {}
    for line in text.splitlines():
        if line.strip() == "": break
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out

def rec(checks, label, ok, fatal=True, detail=None):
    checks.append({"check": label, "status": "PASS" if ok else ("FAIL" if fatal else "WARN"),
                   "detail": str(detail if detail is not None else "")[:160]})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--source", action="store_true")
    a = ap.parse_args()
    date = a.date or latest_date()
    if not date:
        raise SystemExit("no chapter found")
    chapter_path = next(iter(sorted((ROOT / "_weekly").glob(f"{date}*.md"))), None)
    if chapter_path is None:
        raise SystemExit(f"no chapter file for {date}")
    checks = []
    p = chapter_path
    txt = p.read_text(encoding="utf-8") if p.exists() else ""
    fm = meta(txt)
    body = txt.split("---", 2)[-1]
    for k in ("title", "date", "description", "cold_open", "sources_checked"):
        rec(checks, f"frontmatter.{k}", bool(fm.get(k)))
    rec(checks, "frontmatter.article", fm.get("article", "").lower() == "true")
    rec(checks, "no raw markdown", "**" not in body and not re.search(r"^#\s", body, re.M))
    rec(checks, "disclaimer in source", "not medical advice" in body.lower() or "not medical" in body.lower())
    rec(checks, "source links >= 2", len(re.findall(r"https?://", body)) >= 2,
        detail=len(re.findall(r"https?://", body)))
    rec(checks, "sources heading", "Sources" in body)
    notes = sorted((ROOT / "_notes").glob("*.md"))
    rec(checks, "notes >= 2", len(notes) >= 2, detail=str(len(notes)))
    style = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    rec(checks, "cookiebar [hidden] CSS", "#cookiebar[hidden]{display:none" in style)
    rec(checks, "IndexNow key file", (ROOT / KEY_FILE).exists())

    if not a.source:
        url = f"{DOMAIN}/weekly/{p.stem}/"
        code, html = fetch(url)
        rec(checks, "chapter HTTP 200", code == 200, detail=code)
        if code == 200:
            types = []
            for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
                try: types.append(json.loads(b).get("@type"))
                except Exception: types.append("INVALID")
            rec(checks, "JSON-LD WebSite+Article", "WebSite" in types and "Article" in types, detail=str(types))
            rec(checks, "no duplicate WebSite", types.count("WebSite") == 1, detail=str(types))
            rec(checks, "canonical", f'rel="canonical" href="{url}"' in html)
            rec(checks, "H1", bool(re.search(r"<h1[^>]*>.+</h1>", html, re.S)))
            rec(checks, "OG + twitter:image", "og:site_name" in html and "twitter:image" in html)
            rec(checks, "cookiebar + consent", 'id="cookiebar"' in html and "vita_cookie_consent" in html)
            rec(checks, "live disclaimer", "not medical advice" in html.lower())
        sm, smap = fetch(DOMAIN + "/sitemap.xml")
        rec(checks, "sitemap contains chapter", sm == 200 and url in smap, detail=sm)
        rr, rss = fetch(DOMAIN + "/rss.xml")
        rec(checks, "rss contains chapter", rr == 200 and url in rss, detail=rr)
        lc, ll = fetch(DOMAIN + "/llms.txt")
        rec(checks, "llms.txt markdown links", lc == 200 and "](" in ll, detail=lc)
        kc, _ = fetch(f"{DOMAIN}/{KEY_FILE}")
        rec(checks, "IndexNow key live", kc == 200, detail=kc)

    fails = [c for c in checks if c["status"] == "FAIL"]
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"audit-{date}.json"
    out.write_text(json.dumps({"date": date,
                               "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                               "checks": checks, "fails": len(fails)},
                              ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[audit] {date}: {len(checks)} checks, {len(fails)} FAIL -> {out}")
    for c in fails[:10]: print("  FAIL", c["check"], c["detail"])
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
