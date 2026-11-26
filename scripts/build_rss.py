#!/usr/bin/env python3
"""Generate rss.xml from _chapters/*.md frontmatter (keyless, stdlib only)."""
import pathlib, re
from xml.etree import ElementTree as ET
from xml.dom import minidom

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://vita.sok.lv"

def meta(text):
    out = {}
    for line in text.splitlines():
        m = re.match(r'^(date|title|description):\s*(.+)$', line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"\'')
    return out

items = []
for p in sorted((ROOT / "_weekly").glob("*.md")):
    d = meta(p.read_text(encoding="utf-8"))
    if not d.get("date"):
        continue
    link = f'{SITE}/weekly/{p.stem}/'
    items.append((d["date"], d.get("title", p.stem), d.get("description", ""), link))
items.sort(reverse=True)

rss = ET.Element("rss", {"version": "2.0"})
ch = ET.SubElement(rss, "channel")
ET.SubElement(ch, "title").text = "Vita"
ET.SubElement(ch, "link").text = SITE + "/"
ET.SubElement(ch, "description").text = "Micronutrients, decoded — evidence, not advice."
ET.SubElement(ch, "language").text = "en"
for date, title, desc, link in items:
    it = ET.SubElement(ch, "item")
    ET.SubElement(it, "title").text = title
    ET.SubElement(it, "link").text = link
    ET.SubElement(it, "guid").text = link
    ET.SubElement(it, "pubDate").text = date + "T00:00:00Z"
    ET.SubElement(it, "description").text = desc

out = minidom.parseString(ET.tostring(rss, encoding="utf-8")).toprettyxml(indent="  ")
(ROOT / "rss.xml").write_text(out, encoding="utf-8")
print(f"[rss] {len(items)} chapter(s) -> {ROOT / 'rss.xml'}")
