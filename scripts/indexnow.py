#!/usr/bin/env python3
"""IndexNow for Vita: submit only URLs whose source hash changed. Public key only."""
import argparse, hashlib, json, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://vita.sok.lv"
ENDPOINT = "https://api.indexnow.org/indexnow"
MANIFEST = ROOT / "indexnow_manifest.json"
KEY = "vita574350b961c7d455"  # public IndexNow key; key file is served at /indexnow-<key>.txt

def sources():
    m = {"/": ROOT / "index.html",
         "/methodology/": ROOT / "methodology.html",
         "/archive/": ROOT / "archive.html",
         "/llms.txt": ROOT / "llms.txt"}
    for p in (ROOT / "_weekly").glob("*.md"):
        m[f"/weekly/{p.stem}/"] = p
    for p in (ROOT / "_notes").glob("*.md"):
        m[f"/notes/{p.stem}/"] = p
    return m

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load():
    if not MANIFEST.exists():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {}

def submit(urls, key):
    if not urls:
        print("[indexnow] nothing changed")
        return True
    body = json.dumps({"host": "vita.sok.lv", "key": key, "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("[indexnow]", r.status, "for", len(urls), "URL(s)")
        return r.status in (200, 202)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    current = {u: digest(p) for u, p in sources().items()}
    if a.seed:
        MANIFEST.write_text(json.dumps(current, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[indexnow] seeded {len(current)} URL hash(es), nothing sent")
        return
    old = load()
    changed = [u for u, h in current.items() if a.all or old.get(u) != h]
    if submit(changed, KEY):
        MANIFEST.write_text(json.dumps(current, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
