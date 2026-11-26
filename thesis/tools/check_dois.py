"""Check every DOI in references.bib against Crossref (title similarity). Read-only."""
import difflib
import json
import re
import sys
import time
import urllib.request

bib = open(sys.argv[1], encoding="utf-8").read()
entries = re.split(r"\n(?=@)", bib)
rows = []
for e in entries:
    key = re.match(r"@\w+\{([^,]+),", e.strip())
    if not key:
        continue
    key = key.group(1)
    title = re.search(r"title\s*=\s*\{(.+?)\},?\s*\n", e, re.S)
    title = re.sub(r"[{}\\]", "", title.group(1)) if title else ""
    doi = re.search(r"doi\s*=\s*\{([^}]+)\}", e, re.I)
    year = re.search(r"year\s*=\s*\{(\d{4})\}", e)
    if not doi:
        rows.append({"key": key, "title": title, "doi": None, "status": "no DOI"})
        continue
    d = doi.group(1).strip()
    try:
        req = urllib.request.Request(f"https://api.crossref.org/works/{urllib.request.quote(d)}", headers={"User-Agent": "thesis-bibliography-check/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            msg = json.load(r)["message"]
        ct = (msg.get("title") or [""])[0]
        sim = difflib.SequenceMatcher(None, title.lower(), ct.lower()).ratio()
        cy = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
        status = "OK" if sim >= 0.8 else ("CHECK" if sim >= 0.5 else "MISMATCH")
        rows.append({"key": key, "doi": d, "bib_title": title, "crossref_title": ct, "similarity": round(sim, 2), "bib_year": year.group(1) if year else None, "crossref_year": cy, "status": status})
    except Exception as ex:  # noqa: BLE001
        rows.append({"key": key, "doi": d, "bib_title": title, "status": f"DOI NOT RESOLVED ({type(ex).__name__}: {ex})"})
    time.sleep(0.3)
json.dump(rows, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for r in rows:
    if r["status"] != "OK":
        print(r["key"], "|", r["status"], "|", r.get("doi"), "|", (r.get("bib_title") or r.get("title", ""))[:70], "| CR:", (r.get("crossref_title") or "")[:70])
print("total", len(rows), "ok", sum(r["status"] == "OK" for r in rows))
