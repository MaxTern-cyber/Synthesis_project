"""
Generate the GitHub social-preview banner (1280x640 PNG) for the repo.

Upload the result at: Settings -> Social preview -> Upload an image.
That image is what appears when the repo URL is shared on
LinkedIn, X/Twitter, Slack, etc.

Run:
    python launchers/make_social_preview.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "social-preview.png"

W, H = 1280, 640
BG_TOP = (15, 23, 42)        # slate-900
BG_BOTTOM = (30, 41, 59)     # slate-800
ACCENT = (78, 205, 196)      # teal -- matches Streamlit primaryColor
ACCENT_DIM = (45, 130, 125)
TEXT = (241, 245, 249)       # slate-100
MUTED = (148, 163, 184)      # slate-400


def _gradient_bg(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _decorative_graph(img: Image.Image) -> None:
    """Draw an abstract DAG-ish lattice on the right side of the banner."""
    draw = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(7)

    # Node grid: 8 columns x 6 rows on the right half
    cols, rows = 8, 6
    x0, y0 = 720, 80
    x1, y1 = 1230, 560
    dx = (x1 - x0) / (cols - 1)
    dy = (y1 - y0) / (rows - 1)

    nodes = []
    for c in range(cols):
        for r in range(rows):
            jx = rng.uniform(-10, 10)
            jy = rng.uniform(-10, 10)
            nodes.append((x0 + c * dx + jx, y0 + r * dy + jy, c, r))

    # Edges: connect each node to 1-2 neighbours in the next column
    for (x, y, c, r) in nodes:
        if c >= cols - 1:
            continue
        targets = [n for n in nodes if n[2] == c + 1 and abs(n[3] - r) <= 1]
        rng.shuffle(targets)
        for tx, ty, _, _ in targets[: rng.choice([1, 1, 2])]:
            alpha = rng.randint(60, 140)
            draw.line([(x, y), (tx, ty)], fill=ACCENT_DIM + (alpha,), width=2)

    # Nodes
    for (x, y, c, r) in nodes:
        radius = rng.choice([5, 6, 7, 8])
        # Highlight a few nodes as "critical path"
        is_hot = (r == 2 and c in (1, 3, 5, 7)) or (r == 3 and c in (2, 4, 6))
        color = (255, 107, 107, 255) if is_hot else ACCENT + (220,)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\verdana.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def main() -> int:
    img = Image.new("RGB", (W, H), color=BG_TOP)
    _gradient_bg(img)
    _decorative_graph(img)

    draw = ImageDraw.Draw(img)

    # Accent bar on the left
    draw.rectangle([60, 110, 70, 530], fill=ACCENT)

    # Title
    title = "Synthesis_project"
    draw.text((100, 95), title, font=_load_font(78, bold=True), fill=TEXT)

    # Subtitle
    sub = "AI-assisted Verilog netlist analysis"
    draw.text((103, 195), sub, font=_load_font(32, bold=False), fill=ACCENT)

    # Body lines
    body = [
        "Verilog netlist  ->  NetworkX DAG  ->  graph algorithms + AI hooks",
        "Fanout cones * Critical paths * FSM detection * CDC * SCC",
        "Visualize a 1278-node multiplier interactively in your browser.",
    ]
    y = 290
    for line in body:
        draw.text((100, y), line, font=_load_font(24), fill=TEXT)
        y += 40

    # Footer
    draw.text((100, 470), "github.com/MaxTern-cyber/Synthesis_project",
              font=_load_font(22, bold=True), fill=ACCENT)
    draw.text((100, 510), "Python  *  NetworkX  *  PyVis  *  Streamlit  *  Plotly",
              font=_load_font(20), fill=MUTED)

    # Tiny "live demo" pill
    pill_text = "  LIVE DEMO  "
    pf = _load_font(18, bold=True)
    pw = draw.textlength(pill_text, font=pf)
    px, py = 100, 555
    draw.rounded_rectangle([px, py, px + pw + 8, py + 32], radius=16, fill=ACCENT)
    draw.text((px + 4, py + 5), pill_text, font=pf, fill=BG_TOP)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"Wrote {OUT}  ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
