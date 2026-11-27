"""Compare regenerated case-study JSON outputs with the committed versions.

Used after `linux/run_all.sh --full` (and by the weekly GitHub run): every
number must match the committed file within a relative tolerance of 1e-9
(floating-point rounding between operating systems is about 1e-15). Run ids,
timestamps, paths and software versions are ignored.

Exit code 0 = every published number reproduced; 1 = at least one differs.

Usage (repository root):  python linux/compare_results.py
"""

from __future__ import annotations

import json
import math
import subprocess  # nosec B404 - fixed git argv
import sys
from pathlib import Path
from typing import Any, Iterator

FILES = ("results.json", "reference_cos.json", "robustness.json", "independent_check.json")
IGNORED_KEYS = {
    "run_id",
    "main_run_id",
    "created_utc",
    "generated_utc",
    "timestamp",
    "started_utc",
    "finished_utc",
    "runtime_seconds",
    "environment",
    "git",
    "command",
    "manifest",
    "path",
    "href",
    "python",
    "platform",
    "versions",
    "checked_at",
    "checked_run_id",
    "code_commit",
}
REL_TOL = 1e-9
ABS_TOL = 1e-12


def walk(a: Any, b: Any, path: str = "") -> Iterator[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in IGNORED_KEYS or k.endswith(("_utc", "_at", "_run_id", "_commit")):
                continue
            if k not in a or k not in b:
                yield f"{path}/{k}: present only in {'new' if k in b else 'committed'} file"
                continue
            yield from walk(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield f"{path}: list length {len(a)} -> {len(b)}"
            return
        for i, (x, y) in enumerate(zip(a, b)):
            yield from walk(x, y, f"{path}[{i}]")
    elif isinstance(a, bool) or isinstance(b, bool):
        if a != b:
            yield f"{path}: {a!r} -> {b!r}"
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not (math.isnan(a) and math.isnan(b)) and not math.isclose(
            a, b, rel_tol=REL_TOL, abs_tol=ABS_TOL
        ):
            yield f"{path}: {a!r} -> {b!r}"
    elif a != b:
        yield f"{path}: {str(a)[:60]!r} -> {str(b)[:60]!r}"


def committed(path: Path, repo: Path) -> Any:
    rel = path.relative_to(repo).as_posix()
    out = subprocess.run(  # nosec B603 B607 - fixed git argv
        ["git", "show", f"HEAD:{rel}"], cwd=repo, capture_output=True, check=True
    )
    return json.loads(out.stdout.decode("utf-8"))


def main(repo: Path = Path(__file__).resolve().parents[1]) -> int:
    data = repo / "docs" / "case-study" / "data"
    problems: list[str] = []
    checked = 0
    for case in sorted(p for p in data.iterdir() if p.is_dir()):
        for name in FILES:
            f = case / name
            if not f.exists():
                continue
            try:
                old = committed(f, repo)
            except subprocess.CalledProcessError:
                continue
            new = json.loads(f.read_text(encoding="utf-8"))
            diffs = list(walk(old, new))
            checked += 1
            problems += [f"{case.name}/{name}{d}" for d in diffs]
    print(f"compared {checked} files (relative tolerance {REL_TOL})")
    if problems:
        print(f"{len(problems)} differences:")
        for p in problems[:100]:
            print("  " + p)
        return 1
    print("every published number reproduced")
    return 0


if __name__ == "__main__":
    sys.exit(main())
