"""Work through the next open AI-doable items in the private question backlog.

For each item it asks the configured model (your own OpenRouter or OmniRoute
key, see pipeline/src/llm_gateway.py) for a short, structured plan of checks,
and writes that plan to a private note. The note is a working note, not
thesis text. It does not change any thesis file, commit anything or send
anything.

Designed to never crash partway through a batch:
  - each item is requested independently; a failure on one item is recorded
    and the worker moves to the next;
  - the default model is a cheap one, chosen for this repetitive,
    short-answer task; if that model name is rejected by the provider, the
    worker automatically falls back once to the known-good default model
    from the owner's own Hermes config (anthropic/claude-opus-4.6) and says
    so in the note;
  - if a reply does not use the required section headers, the worker asks
    once more, more strictly; if it still does not, the raw reply is kept
    with a visible format warning instead of being discarded.

Usage (from the repository root):
  python -I -X utf8 thesis/tools/question_worker.py --max-items 2
  python -I -X utf8 thesis/tools/question_worker.py --provider omniroute --dry-run
  python -I -X utf8 thesis/tools/question_worker.py --model anthropic/claude-haiku-4.5
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from pipeline.src import llm_gateway as gw  # noqa: E402

BACKLOG = REPO / "docs" / "thesis_audit" / "QUESTION_BACKLOG_2026-11-27.md"
NOTES = REPO / "docs" / "thesis_audit" / "worker_notes"
LOG = NOTES / "worker_run_log.md"
BANNER = (
    "> Working note from an AI model, private. Not thesis text. "
    "Check every claim against the evidence before using it."
)

# Chosen for this repetitive, short structured-answer task: a small/cheap
# model is enough and keeps token cost low across many backlog items.
# If this exact OpenRouter slug stops resolving, the worker falls back
# automatically (see run_item) to DEFAULT_MODEL, which is the model already
# used elsewhere in the owner's own Hermes config.yaml.
CHEAP_MODEL = "anthropic/claude-haiku-4.5"

# Category -> required section headers and a short category-specific brief.
# Forcing exact headers makes a malformed reply easy to detect and retry.
CATEGORY_PROMPTS: dict[str, tuple[str, list[str]]] = {
    "B": (
        "This is a DATA/METHOD sensitivity question about the Sentinel-2 case study "
        "(pipeline/src/case_study.py, pipeline/case_studies/*.json). Say exactly which "
        "config field or code path to change, the exact command to run, and the numeric "
        "range that would make you revise the published result.",
        [
            "## Config or code change",
            "## Command",
            "## Expected numeric range",
            "## Would change the thesis if",
        ],
    ),
    "C": (
        "This is a STATISTICS/CORRECTNESS question about the change-detection method. "
        "Say whether the check needs synthetic data (always labelled synthetic) or the "
        "real published run, the exact test to add, and the pass/fail threshold.",
        [
            "## Test type",
            "## Data (synthetic or real run)",
            "## Pass/fail threshold",
            "## File to add it to",
        ],
    ),
    "D": (
        "This is a SOFTWARE-QUALITY question about the pipeline or the case-study page. "
        "Name the exact open-source tool, the exact command, and what a passing result "
        "looks like.",
        ["## Tool", "## Command", "## Passing result", "## Risk if skipped"],
    ),
    "E": (
        "This is a THESIS-TEXT preparation question. CZU Rector's Directive 7/2026 Art. 8(5) "
        "forbids AI from writing the student's results, discussion or conclusions. Reply with "
        "BULLET FACTS ONLY (numbers, file names, JSON keys) that the student can turn into "
        "their own sentences. Do NOT write connected prose, do NOT draw conclusions, do NOT "
        "use words like 'shows that' or 'demonstrates'.",
        [
            "## Facts (bullets only)",
            "## Source files/keys",
            "## What NOT to write (AI boundary)",
        ],
    ),
    "F": (
        "This is a WEBSITE/PUBLIC-ASSET question about docs/case-study or docs/index.html. "
        "Name the exact file, the exact text or code to find, and what it should become.",
        ["## File", "## Find", "## Replace with", "## How to verify"],
    ),
}
DEFAULT_PROMPT = (
    "Give a short, concrete plan: the checks to run, the data or command that proves "
    "each one, and what result would change the thesis.",
    ["## Checks", "## Evidence", "## Would change the thesis if"],
)

SYSTEM = (
    "You help a non-technical bachelor student check a remote-sensing thesis. "
    "Plain English, under 260 words. Never invent sources, numbers or commands; "
    "use only numbers from the project context. "
    "Use exactly the section headers you are given, in that order, each on its own line "
    "starting with '## '. Do not add other headers."
)


CONTEXT_FILES = {
    "alqueva_olive": "NDVI change, main case",
    "neves_corvo_mine": "bare-soil index change, second case",
}
REPO_MAP = """Repository facts (do not invent other files):
- pipeline/src/case_study.py: change method (index, delta, threshold, patches)
- pipeline/run_case_study.py: CLI, `python pipeline/run_case_study.py run pipeline/case_studies/<case>.json`
- pipeline/case_studies/<case>.json: pinned config per case
- pipeline/src/robustness.py + pipeline/run_robustness.py: bootstrap, threshold curve, second date pair
- pipeline/src/reference_cos.py: comparison with the official DGT land-use map (COS 2018v4 / 2025v1)
- pipeline/src/provider_pc.py + pipeline/run_interop_check.py: second data provider (Planetary Computer)
- pipeline/verify_independent.py: independent re-implementation check
- pipeline/tests/: pytest suite (`python -m pytest pipeline/tests -q`)
- docs/case-study/data/<case>/results.json, robustness.json, reference_cos.json: published outputs
- docs/case-study/index.html: public case-study page
- formal/: Lean 4 proofs of the threshold and flag rules"""


def _short(v: object, n: int = 400) -> str:
    s = json.dumps(v, separators=(",", ":"))
    return s if len(s) <= n else s[:n] + "...(cut)"


def build_context(repo: Path = REPO) -> str:
    """Compact, factual project context for every prompt (about 3-4k chars).

    Only reads public files from this repository. Missing files are skipped.
    """
    parts = [REPO_MAP]
    for case, label in CONTEXT_FILES.items():
        cfg_p = repo / "pipeline" / "case_studies" / f"{case}.json"
        res_p = repo / "docs" / "case-study" / "data" / case / "results.json"
        try:
            cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
            cfg.pop("description", None)
            cfg.pop("selection_rationale", None)
            parts.append(f"\nCase {case} ({label}) config: {_short(cfg, 900)}")
        except (OSError, ValueError):
            continue
        try:
            r = json.loads(res_p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        ch = r.get("change", {})
        keep = {
            k: ch.get(k)
            for k in (
                "increase_area_ha",
                "decrease_area_ha",
                "increase_pixels_in_patches",
                "decrease_pixels_in_patches",
                "min_patch_ha",
            )
            if k in ch
        }
        parts.append(
            f"Published run {r.get('run_id')}: threshold {_short(r.get('threshold'))}; "
            f"dates {_short(r.get('dates'))}; area_km2 {r.get('aoi', {}).get('area_km2')}; "
            f"change {_short(keep)}"
        )
    return "\n".join(parts)


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


def prompt_for(
    item_id: str, question: str, context: str = ""
) -> tuple[str, list[str]]:
    category = re.match(r"[A-Z]", item_id)
    brief, headers = CATEGORY_PROMPTS.get(
        category.group(0) if category else "", DEFAULT_PROMPT
    )
    header_list = "\n".join(headers)
    ctx = (
        f"PROJECT CONTEXT (facts from the repository; use them, do not ask for them):\n"
        f"{context}\n\n"
        if context
        else ""
    )
    return (
        f"{ctx}{brief}\n\nItem {item_id}: {question}\n\n"
        "If something is not in the context, say exactly which file to open and "
        "what to look for in it; do not ask the student questions.\n\n"
        f"Reply using exactly these headers, in this order, nothing else:\n{header_list}",
        headers,
    )


def well_formed(reply: str, headers: list[str]) -> bool:
    return all(h in reply for h in headers)


def run_item(
    provider: gw.ProviderConfig,
    item_id: str,
    question: str,
    model: str,
    transport: gw.Transport | None = None,
    sleep=None,
    context: str = "",
) -> tuple[str, bool, list[str]]:
    """Returns (text_to_write, used_fallback_model, warnings). Never raises."""
    text_prompt, headers = prompt_for(item_id, question, context)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": text_prompt},
    ]
    warnings: list[str] = []
    used_fallback = False
    kw: dict = {}
    if transport is not None:
        kw["transport"] = transport
    if sleep is not None:
        kw["sleep"] = sleep

    def ask(use_model: str) -> str | None:
        try:
            return gw.chat(provider, messages, model=use_model, **kw)
        except gw.GatewayError as exc:
            warnings.append(f"gateway error with model {use_model}: {exc}")
            return None

    fallback = gw.fallback_model(provider)
    reply = ask(model)
    if reply is None and model != fallback:
        used_fallback = True
        reply = ask(fallback)
    if reply is None:
        return (
            f"**FAILED — no reply from either model.**\n\nWarnings:\n"
            + "\n".join(f"- {w}" for w in warnings),
            used_fallback,
            warnings,
        )
    if not well_formed(reply, headers):
        stricter = messages + [
            {"role": "assistant", "content": reply},
            {
                "role": "user",
                "content": "Your reply did not use every required header exactly as given. "
                "Reply again with exactly these headers, each on its own line starting with '## ', nothing else:\n"
                + "\n".join(headers),
            },
        ]
        retry = None
        try:
            retry = gw.chat(
                provider,
                stricter,
                model=fallback if used_fallback else model,
                **kw,
            )
        except gw.GatewayError as exc:
            warnings.append(f"retry failed: {exc}")
        if retry and well_formed(retry, headers):
            reply = retry
        else:
            warnings.append(
                "reply did not match the required format even after one retry; kept as-is"
            )
            reply = (
                "**FORMAT WARNING — headers may be missing or reordered.**\n\n" + reply
            )
    return reply, used_fallback, warnings


def _done_today(item_id: str, today: str) -> bool:
    """A note from today counts as done unless that attempt failed."""
    note = NOTES / f"{item_id}-{today}.md"
    if not note.exists():
        return False
    return "**FAILED" not in note.read_text(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--provider",
        choices=["auto", "openrouter", "omniroute", "omniroute-local", "claude-cli"],
        default="auto",
        help="auto: OpenRouter key, OmniRoute key, local OmniRoute, then Claude CLI",
    )
    ap.add_argument(
        "--model",
        default=None,
        help=f"default: {CHEAP_MODEL} on OpenRouter/OmniRoute, 'haiku' on the "
        "Claude CLI, 'auto/cheap' on local OmniRoute; one fallback if rejected",
    )
    ap.add_argument(
        "--skip-done-today",
        action="store_true",
        help="skip items that already have a note dated today",
    )
    ap.add_argument("--max-items", type=int, default=2)
    ap.add_argument(
        "--dry-run", action="store_true", help="list the items; call no model"
    )
    args = ap.parse_args(argv)

    items = open_ai_items(BACKLOG.read_text(encoding="utf-8"))
    if args.skip_done_today:
        today = dt.date.today().isoformat()
        items = [i for i in items if not _done_today(i[0], today)]
    items = items[: args.max_items]
    if args.dry_run:
        for iid, q in items:
            print(iid, q)
        return 0
    if not items:
        print("No open AI items found in the backlog.")
        return 0

    try:
        provider = gw.load_provider(args.provider)
    except gw.GatewayError as exc:
        print(f"Not running: {exc}", file=sys.stderr)
        return 2

    if args.model is None:
        args.model = (
            CHEAP_MODEL
            if provider.name in ("openrouter", "omniroute")
            else gw.default_model(provider)
        )
    args.provider = provider.name
    NOTES.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().isoformat()
    log_lines = [
        f"\n## Run {dt.datetime.now().isoformat(timespec='seconds')} ({args.provider}, requested model {args.model})"
    ]
    context = build_context()
    for iid, question in items:
        try:
            body, used_fallback, warnings = run_item(
                provider, iid, question, args.model, context=context
            )
        except Exception:  # noqa: BLE001 - a worker must never crash the batch
            body = (
                "**FAILED — unexpected error.**\n\n```\n"
                + traceback.format_exc()[-1500:]
                + "\n```"
            )
            used_fallback, warnings = False, [
                "unhandled exception, see traceback above"
            ]
        out = NOTES / f"{iid}-{stamp}.md"
        out.write_text(
            f"# {iid} — {question}\n\n{BANNER}\n\n{body.strip()}\n",
            encoding="utf-8",
            newline="\n",
        )
        status = "fallback-model" if used_fallback else "ok"
        if warnings:
            status += f" ({len(warnings)} warning(s))"
        log_lines.append(f"- {iid}: {status} -> {out.relative_to(REPO).as_posix()}")
        print("wrote", out.relative_to(REPO).as_posix(), f"[{status}]")
    with LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(log_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
