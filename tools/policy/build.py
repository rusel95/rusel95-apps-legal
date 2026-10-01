#!/usr/bin/env python3
"""Generator for the 49 Compresso privacy-policy pages (MediaCleaner/privacy-policy*.html).

Each language's body lives in bodies/<code>.html (h1 .. contact paragraph). meta.py holds the
per-language title, native name, "English prevails" footer and dir. Bodies name the Settings tab,
the analytics toggle and the Recently Deleted album as @@S@@ / @@T@@ / @@A@@; fill.py swaps in the
app's own strings from ui_terms.tsv (extracted from MediaCleaner/Localizable.xcstrings).

    python3 fill.py && python3 build.py && python3 verify_terms.py && python3 ../check_privacy_policy.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1] / "MediaCleaner"
sys.path.insert(0, str(HERE))
from meta import LANGS  # noqa: E402  code -> dict(name, title, note, rtl)

BLOCK = r"(<h1|<p[ >]|<div|</div>|<h2|<h3|<ul|<li|</ul>)"


def normalize(body: str) -> str:
    body = re.sub(r"\s+", " ", body).strip()
    body = re.sub(r"\s*" + BLOCK, r"\n\1", body)
    body = re.sub(r"\s*(</ul>|</div>)", r"\n\1", body)
    body = re.sub(r"(<div[^>]*>)\s+", r"\1", body)
    out, depth = [], 0
    for line in body.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(("</ul>", "</div>")):
            depth -= 1
        out.append("    " * (2 + depth) + line)
        if (line.startswith("<ul") or line.startswith("<div")) and not line.endswith(("</ul>", "</div>")):
            depth += 1
    assert depth == 0, "unbalanced ul/div"
    return "\n".join(out)


def file_for(code: str) -> str:
    return "privacy-policy.html" if code == "en" else f"privacy-policy.{code}.html"


def page(code: str) -> str:
    m = LANGS[code]
    links = []
    for c, lm in LANGS.items():
        attrs = f' lang="{c}"' + (' dir="rtl"' if lm.get("rtl") else "")
        cur = ' aria-current="page"' if c == code else ""
        links.append(f'                <a href="{file_for(c)}"{attrs}{cur}>{lm["name"]}</a>')
    body = normalize((HERE / "bodies" / f"{code}.html").read_text())
    note = "" if code == "en" else f'\n\n        <p class="note">{m["note"]}</p>'
    return f"""<!DOCTYPE html>
<html lang="{code}"{' dir="rtl"' if m.get("rtl") else ""}>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{m["title"]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #fff;
            padding: 20px;
        }}

        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        h1 {{ font-size: 32px; margin-bottom: 10px; color: #1a1a1a; }}
        h2 {{ font-size: 22px; margin-top: 32px; margin-bottom: 12px; color: #1a1a1a; }}
        h3 {{ font-size: 18px; margin-top: 20px; margin-bottom: 8px; color: #1a1a1a; }}
        p {{ margin-bottom: 16px; }}
        ul {{ margin-bottom: 16px; margin-inline-start: 24px; }}
        li {{ margin-bottom: 8px; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .updated {{ color: #666; font-size: 15px; margin-bottom: 24px; }}
        .highlight {{ background: #f4f8ff; border-inline-start: 3px solid #0066cc; padding: 14px 18px; margin-bottom: 20px; }}
        .lang {{ font-size: 15px; margin-bottom: 28px; color: #666; }}
        .lang summary {{ cursor: pointer; }}
        .lang nav {{ display: flex; flex-wrap: wrap; gap: 4px 14px; margin-top: 10px; }}
        .lang a[aria-current] {{ color: #1a1a1a; font-weight: 600; }}
        .note {{ color: #666; font-size: 14px; margin-top: 40px; padding-top: 16px; border-top: 1px solid #eee; }}
    </style>
</head>

<body>
    <div class="container">
        <details class="lang">
            <summary>🌐 {m["name"]}</summary>
            <nav>
{chr(10).join(links)}
            </nav>
        </details>

{body}{note}
    </div>
</body>

</html>
"""


if __name__ == "__main__":
    missing = [c for c in LANGS if not (HERE / "bodies" / f"{c}.html").exists()]
    todo = [c for c in LANGS if c not in missing]
    for code in todo:
        (REPO / file_for(code)).write_text(page(code))
    print(f"wrote {len(todo)} pages; missing bodies: {' '.join(missing) or 'none'}")
