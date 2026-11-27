"""Flag filler/hype words and over-long sentences (see docs/WRITING_STYLE.md).

Usage:  python -I -X utf8 thesis/tools/slop_check.py FILE_OR_DIR [...]
Prints file:line, the flagged word or sentence length, and a short excerpt.
Exit code 1 if anything is flagged, so it can run in CI or before a commit.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# word/phrase -> plainer alternative (empty = just delete it)
WORDS = {
    "revolutioniz": "changed",
    "revolutionis": "changed",
    "unprecedented": "",
    "cutting-edge": "",
    "state-of-the-art": "current",
    "seamless": "",
    "leverag": "use",
    "delve": "look at",
    "landscape of": "",
    "realm": "area",
    "holistic": "",
    "synergy": "",
    "game-chang": "",
    "premium": "",
    "enterprise-grade": "",
    "futuristic": "",
    "paradigm shift": "change",
    "plays a crucial role": "matters",
    "plays a vital role": "matters",
    "it is worth noting": "",
    "it is important to note": "",
    "in today's": "",
    "utiliz": "use",
    "utilis": "use",
    "facilitat": "help",
    "robust": "say what was tested",
    "powerful": "",
    "comprehensive": "",
    "unalterable": "",
    "real-time": "say the actual delay",
    "democratiz": "made available",
    "orbital intelligence": "",
    "hidden anomalies": "candidate change",
    "ground truth": "reference data",
    "groundbreaking": "",
    "novel": "new",
}
MAX_WORDS = 30
TEXT_EXT = {".md", ".tex", ".html", ".txt"}


def sentences(line: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]


def check_file(path: Path) -> list[str]:
    out = []
    in_code = False
    for n, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = raw.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line or line.startswith(("<!--", "%", "|---", "http")):
            continue
        text = re.sub(r"<[^>]+>|\[R\d+[^\]]*\]|\\cite\{[^}]*\}|`[^`]*`", "", line)
        low = text.lower()
        for w, alt in WORDS.items():
            if w in low:
                hint = f" -> {alt}" if alt else " -> delete"
                out.append(f"{path}:{n}: '{w}'{hint} | {text[:110]}")
        for s in sentences(text):
            k = len(s.split())
            if k > MAX_WORDS and not s.lstrip().startswith(("|", "-", "*")):
                out.append(f"{path}:{n}: sentence of {k} words | {s[:110]}")
    return out


def main(argv: list[str]) -> int:
    targets = [Path(a) for a in argv] or [Path("thesis/chapters")]
    files = []
    for t in targets:
        files += sorted(p for p in t.rglob("*") if p.suffix in TEXT_EXT) if t.is_dir() else [t]
    hits = [h for f in files for h in check_file(f)]
    print("\n".join(hits))
    print(f"\n{len(hits)} flags in {len(files)} files")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
