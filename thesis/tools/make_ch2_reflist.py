"""Regenerate the chapter 2 reference list (Markdown) and LaTeX copy from references.bib.

Run from the repository root:  python -I -X utf8 thesis/tools/make_ch2_reflist.py
- The Markdown chapter keeps a "References cited in this chapter" list for thesis/compile_pdf.py.
- The LaTeX chapter omits it; BibTeX prints the bibliography from main.tex.
"""
import re
import sys
from pathlib import Path

REPO = Path(".")
MD = REPO / "thesis/chapters/02_literature_review.md"
TEX = REPO / "thesis/latex/chapters/02_literature_review.tex"
BIB = REPO / "thesis/latex/references.bib"
MARK = "## References cited in this chapter"


def bib_entries(text: str) -> dict[str, dict[str, str]]:
    out = {}
    for e in re.split(r"\n(?=@)", text):
        m = re.match(r"\s*@(\w+)\{([^,]+),", e)
        if not m:
            continue
        fields = {k.lower(): v for k, v in re.findall(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", e)}
        fields["_type"] = m.group(1)
        out[m.group(2)] = fields
    return out


def clean(s: str) -> str:
    s = s.replace("\\&", "&").replace("--", "–").replace("\\url", "")
    s = re.sub(r"\\['`\"^~v]\{?(\w)\}?", r"\1", s)
    return re.sub(r"[{}]", "", s).strip()


def is_corporate(a: str) -> bool:
    """True for an author field that is one braced group, e.g. {{European Space Agency}}."""
    a = a.strip()
    if not (a.startswith("{") and a.endswith("}")):
        return False
    depth = 0
    for i, ch in enumerate(a):
        depth += {"{": 1, "}": -1}.get(ch, 0)
        if depth == 0 and i < len(a) - 1:
            return False
    return True


def authors(a: str) -> str:
    if is_corporate(a):
        return clean(a)
    names = [clean(x) for x in a.split(" and ")]
    surname = lambda n: n.split(",")[0].strip() if "," in n else n.split()[-1] if " " in n and not n.isupper() else n
    if len(names) > 2:
        return f"{surname(names[0])} et al."
    return " & ".join(surname(n) for n in names)


def fmt(key: str, f: dict[str, str]) -> str:
    parts = [f"**{authors(f.get('author', ''))}** ({f.get('year', 'n.d.')}). {clean(f.get('title', ''))}."]
    venue = f.get("journal") or f.get("booktitle") or f.get("howpublished") or f.get("publisher")
    if venue:
        v = f"*{clean(venue)}*"
        if f.get("volume"):
            v += f", {f['volume']}"
        if f.get("pages"):
            v += f", {clean(f['pages'])}"
        parts.append(v + ".")
    if f.get("doi"):
        parts.append(f"https://doi.org/{f['doi']}")
    elif f.get("url"):
        parts.append(clean(f["url"]))
    return " ".join(parts) + f" [{key}]"


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    body = md.split(MARK)[0].rstrip()
    keys = []
    for group in re.findall(r"\[(R\d{3}(?:\s*,\s*R\d{3})*)\]", body):
        for k in (x.strip() for x in group.split(",")):
            if k not in keys:
                keys.append(k)
    bib = bib_entries(BIB.read_text(encoding="utf-8"))
    missing = [k for k in keys if k not in bib]
    if missing:
        sys.exit(f"cited but not in references.bib: {missing}")
    ordered = sorted(keys, key=lambda k: authors(bib[k].get("author", "")).lower())
    lines = [f"{i}. {fmt(k, bib[k])}" for i, k in enumerate(ordered, 1)]
    note = "<!-- Generated from thesis/latex/references.bib by thesis/tools/make_ch2_reflist.py. Do not edit by hand. -->"
    MD.write_text(f"{body}\n\n{MARK}\n\n{note}\n\n" + "\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    sys.path.insert(0, str(REPO / "thesis"))
    from convert_chapters import markdown_to_latex  # noqa: E402

    tex_src = re.sub(r"<!--(.*?)-->", lambda m: "\n".join("% " + l.strip() for l in m.group(1).strip().splitlines()), body, flags=re.S)
    tex = markdown_to_latex(tex_src)
    tex = re.sub(r"^\\% ", "% ", tex, flags=re.M)  # keep the AI-use note a LaTeX comment, not printed text
    TEX.write_text(tex, encoding="utf-8", newline="\n")
    print(f"{len(keys)} cited keys; reference list and LaTeX regenerated")


if __name__ == "__main__":
    main()
