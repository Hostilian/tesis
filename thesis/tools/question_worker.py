"""Work through the next open AI-doable items in the private question backlog.

For each item it asks the configured model (your own OpenRouter or OmniRoute
key, see pipeline/src/llm_gateway.py) for a short plan of checks, and writes
that plan to a private note. The note is a working note, not thesis text.
It does not change any thesis file, commit anything or send anything.

Usage (from the repository root):
  python -I -X utf8 thesis/tools/question_worker.py --max-items 2
  python -I -X utf8 thesis/tools/question_worker.py --provider omniroute --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from pipeline.src import llm_gateway as gw  # noqa: E402

BACKLOG = REPO / "docs" / "thesis_audit" / "QUESTION_BACKLOG_2026-11-27.md"
NOTES = REPO / "docs" / "thesis_audit" / "worker_notes"
BANNER = (
    "> Working note from an AI model, private. Not thesis text. "
    "Check every claim against the evidence before using it."
)
SYSTEM = (
    "You help a bachelor student check a remote-sensing thesis. Give a short plan: "
    "the checks to run, the data or command that proves each one, and what result "
    "would change the thesis. Do not write thesis prose and do not invent sources. "
    "Plain English, under 250 words."
)


def open_ai_items(text: str) -> list[tuple[str, str]]:
    """Rows of the backlog tables whose owner is AI and that are not marked done."""
    items = []
    for line in text.splitlines():
        m = re.match(r"^\|\s*([A-Z]\d+)\s*(✔)?\s*\|(.+)\|\s*$", line)
        if not m or m.group(2):
            continue
        cells = [c.strip() for c in m.group(3).split("|")]
        if len(cells) >= 2 and cells[1].upper().startswith("AI"):
            items.append((m.group(1), cells[0]))
    return items


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", choices=["openrouter", "omniroute"], default="openrouter")
    ap.add_argument("--max-items", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true", help="list the items; call no model")
    args = ap.parse_args(argv)

    items = open_ai_items(BACKLOG.read_text(encoding="utf-8"))[: args.max_items]
    if args.dry_run:
        for iid, q in items:
            print(iid, q)
        return 0

    try:
        provider = gw.load_provider(args.provider)
    except gw.GatewayError as exc:
        print(f"Not running: {exc}", file=sys.stderr)
        return 2

    NOTES.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().isoformat()
    for iid, question in items:
        plan = gw.chat(
            provider,
            [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Item {iid}: {question}"},
            ],
        )
        out = NOTES / f"{iid}-{stamp}.md"
        out.write_text(f"# {iid} — {question}\n\n{BANNER}\n\n{plan.strip()}\n", encoding="utf-8", newline="\n")
        print("wrote", out.relative_to(REPO).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
