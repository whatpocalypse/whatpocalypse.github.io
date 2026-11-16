"""Build the self-contained pages of whatpocalypse.github.io.

Each page in the repository root is generated from `_src/` and carries everything it
needs inline: the stylesheet, the logo mark as SVG and the Inter Display font as a
base64 data URI. Edit `_src/`, then run `python build.py` (standard library only) and
commit the generated pages together with the sources.

The font file `fonts/InterDisplay-subset.woff` is a subset of Inter 4.001 (variable,
opsz pinned to 32, wght 400 to 800), made with fontTools:

    python -m fontTools.varLib.instancer "Inter[opsz,wght].ttf" opsz=32 wght=400:800 -o var.ttf
    python -m fontTools.subset var.ttf --flavor=woff --no-hinting --desubroutinize
        --unicodes="U+0020-007E,U+00A0,U+00A9,U+00B7,U+2019,U+201C,U+201D,U+2026,U+2192"
        --layout-features="kern,liga,calt" --name-IDs=0,1,2,3,4,5,6,13,14
        --output-file=fonts/InterDisplay-subset.woff

The font is licensed under the SIL Open Font License 1.1 (`fonts/OFL.txt`).
"""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "_src"
SITE = "https://whatpocalypse.github.io/"
FORBIDDEN = (chr(0x2013), chr(0x2014))  # en and em dash

# The Whatpocalypse mark: three question mark blades around a dot.
BLADE = "M -39.4,-105 A 40 40 0 1 1 20,-77.4 Q 2,-68 0,-54 L 0,-44"
# Tight box around the drawn mark (the blades reach further up than down).
MARK_BOX = (-156, -171, 312, 285)

PAGES = [
    {
        "out": "index.html",
        "path": "",
        "title": "Whatpocalypse | Impossible scenarios. Real science.",
        "description": (
            "Whatpocalypse: impossible what if scenarios told with real science and "
            "code-generated 3D animation. A new Short every day, a long video every week."
        ),
        "bar": False,
    },
    {
        "out": "privacy.html",
        "path": "privacy.html",
        "title": "Privacy Policy | Whatpocalypse",
        "description": (
            "Privacy policy of the Whatpocalypse publisher app and the Whatpocalypse website."
        ),
        "bar": True,
    },
    {
        "out": "terms.html",
        "path": "terms.html",
        "title": "Terms of Use | Whatpocalypse",
        "description": "Terms of use of the Whatpocalypse website and the Whatpocalypse publisher app.",
        "bar": True,
    },
]


def mark_defs() -> str:
    blade = f'<path id="wp-blade" d="{BLADE}" fill="none" stroke="currentColor" stroke-width="30"/>'
    uses = "".join(f'<use href="#wp-blade" transform="rotate({a})"/>' for a in (120, 240))
    return (
        '<svg class="defs" width="0" height="0" aria-hidden="true" focusable="false" '
        'style="position:absolute;width:0;height:0;overflow:hidden">'
        f'<defs><g id="wp-mark">{blade}{uses}<circle r="26" fill="currentColor"/></g></defs></svg>'
    )


def mark_viewbox() -> str:
    return " ".join(str(v) for v in MARK_BOX)


def favicon_uri() -> str:
    x, y, w, h = MARK_BOX
    side = max(w, h) / 0.8
    cx, cy = x + w / 2, y + h / 2
    vx, vy = cx - side / 2, cy - side / 2
    blades = "".join(
        f"<path d='{BLADE}' transform='rotate({a})' fill='none' stroke='%23F3F0EA' "
        "stroke-width='30'/>"
        for a in (0, 120, 240)
    )
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{vx:g} {vy:g} {side:g} {side:g}'>"
        f"<rect x='{vx:g}' y='{vy:g}' width='{side:g}' height='{side:g}' rx='{side * 0.2:g}' "
        f"fill='%2305070B'/>{blades}<circle r='26' fill='%23F3F0EA'/></svg>"
    )
    return "data:image/svg+xml," + quote(svg, safe="/:=' %,.-()")


def minify_css(css: str) -> str:
    css = re.sub(r"/\*(?!!).*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    css = css.replace(";}", "}")
    return css.strip()


def build_css() -> str:
    font = base64.b64encode((ROOT / "fonts" / "InterDisplay-subset.woff").read_bytes())
    css = (SRC / "style.css").read_text(encoding="utf-8")
    return minify_css(css).replace("{{FONT_DATA}}", font.decode("ascii"))


def bar() -> str:
    return (
        '<header class="bar"><div class="wrap"><a class="brand" href="./">'
        f'<svg class="mark" viewBox="{mark_viewbox()}" width="32" height="29" aria-hidden="true" '
        'focusable="false"><use href="#wp-mark"/></svg>Whatpocalypse</a></div></header>'
    )


def footer() -> str:
    return (
        '<footer class="foot"><div class="wrap"><p>&copy; 2026 Whatpocalypse</p>'
        '<nav aria-label="Site"><a href="./">Home</a><a href="privacy.html">Privacy</a>'
        '<a href="terms.html">Terms</a></nav></div></footer>'
    )


def render(page: dict, css: str) -> str:
    body = (SRC / page["out"]).read_text(encoding="utf-8").strip()
    body = body.replace('viewBox="-176 -176 352 352"', f'viewBox="{mark_viewbox()}"')
    url = SITE + page["path"]
    head = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{page['title']}</title>",
        f'<meta name="description" content="{page["description"]}">',
        '<meta name="theme-color" content="#05070B">',
        '<meta name="color-scheme" content="dark">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="icon" type="image/svg+xml" href="{favicon_uri()}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Whatpocalypse">',
        f'<meta property="og:title" content="{page["title"]}">',
        f'<meta property="og:description" content="{page["description"]}">',
        f'<meta property="og:url" content="{url}">',
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        '<a class="skip" href="#main">Skip to content</a>',
        mark_defs(),
    ]
    if page["bar"]:
        head.append(bar())
    return "\n".join([*head, body, footer(), "</body>", "</html>", ""])


def main() -> int:
    css = build_css()
    for page in PAGES:
        html = render(page, css)
        bad = [c for c in FORBIDDEN if c in html]
        if bad:
            print(f"{page['out']}: forbidden dash characters {bad!r}", file=sys.stderr)
            return 1
        (ROOT / page["out"]).write_text(html, encoding="utf-8", newline="\n")
        print(f"{page['out']}: {len(html.encode('utf-8')):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
