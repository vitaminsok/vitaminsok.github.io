#!/usr/bin/env python3
"""IndexNow for Vita: submit only URLs whose source hash changed. Public key only."""
import argparse, hashlib, json, pathlib, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://vita.sok.lv"
ENDPOINT = "https://api.indexnow.org/indexnow"
MANIFEST = ROOT / "indexnow_manifest.json"
KEY = "vita574350b961c7d455"  # public IndexNow key; key file served at /<key>.txt

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
    urls = [u if u.startswith("http") else SITE + u for u in urls]
    body = json.dumps({"host": "vita.sok.lv", "key": KEY,
                       "keyLocation": f"{SITE}/{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("[indexnow]", r.status, "for", len(urls), "URL(s)")
            return r.status in (200, 202)
    except urllib.error.HTTPError as e:
        print("[indexnow] FAIL", e.code, e.read().decode(errors="replace")[:200])
        return False

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
