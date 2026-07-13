from __future__ import annotations

import html
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_XLSX = REPO_ROOT / "data" / "Comparison_Batch_vs_Perfusion.xlsx"
OUT_DIR = REPO_ROOT / "figures"

SCENARIOS = [
    ("Perfusion", "Perfusion\nmain model", "#0072B2"),
    ("Batch large", "Batch\n90:10 large", "#D55E00"),
    ("Batch local", "Batch\n90:10 local", "#009E73"),
]


@dataclass(frozen=True)
class TextStyle:
    size: float = 9.0
    family: str = "Arial"
    weight: str = "normal"
    color: str = "#1A1A1A"
    anchor: str = "middle"


class SVG:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img">'
        ]

    def line(self, x1, y1, x2, y2, color="#333333", width=1.0, dash: str | None = None):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{color}" stroke-width="{width}"{dash_attr}/>'
        )

    def rect(self, x, y, w, h, fill, stroke="none", stroke_width=0.0):
        self.parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
        )

    def text(self, x, y, text, style: TextStyle, rotate: float | None = None):
        transform = f' transform="rotate({rotate:.1f} {x:.2f} {y:.2f})"' if rotate else ""
        safe = html.escape(str(text))
        self.parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="{style.family}" '
            f'font-size="{style.size:.1f}" font-weight="{style.weight}" fill="{style.color}" '
            f'text-anchor="{style.anchor}" dominant-baseline="middle"{transform}>{safe}</text>'
        )

    def multiline_text(self, x, y, text, style: TextStyle, line_height=11):
        lines = str(text).split("\n")
        start = y - (len(lines) - 1) * line_height / 2
        for i, line in enumerate(lines):
            self.text(x, start + i * line_height, line, style)

    def save(self, path: Path):
        path.write_text("\n".join(self.parts + ["</svg>"]), encoding="utf-8")


class PDF:
    def __init__(self, path: Path, width: int, height: int):
        self.canvas = canvas.Canvas(str(path), pagesize=(width, height))
        self.height = height

    def _y(self, y):
        return self.height - y

    @staticmethod
    def _rgb(hex_color: str):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def line(self, x1, y1, x2, y2, color="#333333", width=1.0, dash: str | None = None):
        c = self.canvas
        c.setStrokeColorRGB(*self._rgb(color))
        c.setLineWidth(width)
        if dash:
            c.setDash(3, 3)
        else:
            c.setDash()
        c.line(x1, self._y(y1), x2, self._y(y2))

    def rect(self, x, y, w, h, fill, stroke="none", stroke_width=0.0):
        c = self.canvas
        c.setFillColorRGB(*self._rgb(fill))
        if stroke != "none":
            c.setStrokeColorRGB(*self._rgb(stroke))
            c.setLineWidth(stroke_width)
            c.rect(x, self._y(y + h), w, h, stroke=1, fill=1)
        else:
            c.rect(x, self._y(y + h), w, h, stroke=0, fill=1)

    def text(self, x, y, text, style: TextStyle, rotate: float | None = None):
        c = self.canvas
        font = "Helvetica-Bold" if style.weight == "bold" else "Helvetica"
        c.setFont(font, style.size)
        c.setFillColorRGB(*self._rgb(style.color))
        width = stringWidth(str(text), font, style.size)
        tx = x - width / 2 if style.anchor == "middle" else x
        if style.anchor == "end":
            tx = x - width
        if rotate:
            c.saveState()
            c.translate(x, self._y(y))
            c.rotate(-rotate)
            c.drawString(-width / 2, -style.size / 3, str(text))
            c.restoreState()
        else:
            c.drawString(tx, self._y(y) - style.size / 3, str(text))

    def multiline_text(self, x, y, text, style: TextStyle, line_height=11):
        lines = str(text).split("\n")
        start = y - (len(lines) - 1) * line_height / 2
        for i, line in enumerate(lines):
            self.text(x, start + i * line_height, line, style)

    def save(self):
        self.canvas.showPage()
        self.canvas.save()


class PNG:
    def __init__(self, path: Path, width: int, height: int, scale: int = 3):
        self.path = path
        self.scale = scale
        self.image = Image.new("RGB", (width * scale, height * scale), "white")
        self.draw = ImageDraw.Draw(self.image)

    @staticmethod
    def _font(size: float, weight: str = "normal"):
        name = "DejaVuSans-Bold.ttf" if weight == "bold" else "DejaVuSans.ttf"
        try:
            return ImageFont.truetype(name, int(round(size * 3)))
        except OSError:
            return ImageFont.load_default()

    def _s(self, value):
        return int(round(value * self.scale))

    def line(self, x1, y1, x2, y2, color="#333333", width=1.0, dash: str | None = None):
        if dash:
            seg = 5
            total = math.hypot(x2 - x1, y2 - y1)
            steps = max(1, int(total / (seg * 2)))
            for i in range(steps):
                a = i / steps
                b = min(1, a + 0.5 / steps)
                self.draw.line(
                    (
                        self._s(x1 + (x2 - x1) * a),
                        self._s(y1 + (y2 - y1) * a),
                        self._s(x1 + (x2 - x1) * b),
                        self._s(y1 + (y2 - y1) * b),
                    ),
                    fill=color,
                    width=max(1, self._s(width)),
                )
        else:
            self.draw.line((self._s(x1), self._s(y1), self._s(x2), self._s(y2)), fill=color, width=max(1, self._s(width)))

    def rect(self, x, y, w, h, fill, stroke="none", stroke_width=0.0):
        box = (self._s(x), self._s(y), self._s(x + w), self._s(y + h))
        self.draw.rectangle(box, fill=fill)
        if stroke != "none" and stroke_width:
            self.draw.rectangle(box, outline=stroke, width=max(1, self._s(stroke_width)))

    def text(self, x, y, text, style: TextStyle, rotate: float | None = None):
        font = self._font(style.size, style.weight)
        text = str(text)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = self._s(x)
        if style.anchor == "middle":
            tx -= tw // 2
        elif style.anchor == "end":
            tx -= tw
        ty = self._s(y) - th // 2
        if rotate:
            temp = Image.new("RGBA", (tw + 8, th + 8), (255, 255, 255, 0))
            td = ImageDraw.Draw(temp)
            td.text((4, 4), text, font=font, fill=style.color)
            temp = temp.rotate(rotate, expand=True)
            self.image.paste(temp, (self._s(x) - temp.width // 2, self._s(y) - temp.height // 2), temp)
        else:
            self.draw.text((tx, ty), text, font=font, fill=style.color)

    def multiline_text(self, x, y, text, style: TextStyle, line_height=11):
        lines = str(text).split("\n")
        start = y - (len(lines) - 1) * line_height / 2
        for i, line in enumerate(lines):
            self.text(x, start + i * line_height, line, style)

    def save(self):
        self.image.save(self.path, dpi=(300, 300))


def read_metric(sheet_name: str, metric: str) -> list[float]:
    df = pd.read_excel(SOURCE_XLSX, sheet_name=sheet_name, header=None)
    row = df[df[0].astype(str).str.strip().eq(metric)]
    if row.empty:
        raise ValueError(f"Metric not found: {sheet_name!r} / {metric!r}")
    values = row.iloc[0, 2:5].tolist()
    return [float(v) if pd.notna(v) else math.nan for v in values]


def make_medium_figure():
    width, height = 980, 680
    svg = SVG(width, height)
    pdf_path = OUT_DIR / "fig1_medium_intensity.pdf"
    pdf = PDF(pdf_path, width, height)
    png = PNG(OUT_DIR / "fig1_medium_intensity.png", width, height)
    draw = [svg, pdf, png]

    metrics = [
        ("DCW-normalized", "medium per kg of DCW", "DCW-normalized"),
        ("Biomass-normalized", "medium per kg of biomass", "Biomass-normalized"),
    ]
    data = [(title, label, read_metric("Medim Usage", metric)) for title, metric, label in metrics]
    x0, x1 = 180, 910
    y0, y1 = 150, 490
    ymax = 45
    ticks = [0, 10, 20, 30, 40]

    for d in draw:
        d.text(width / 2, 54, "Medium intensity of batch and perfusion scenarios", TextStyle(22, weight="bold"))
        d.text(width / 2, 92, "Values are normalized to dry cell weight (DCW) and total biomass output.", TextStyle(15, color="#4D4D4D"))
        d.line(x0, y1, x1, y1, "#2A2A2A", 1.8)
        d.line(x0, y0, x0, y1, "#2A2A2A", 1.8)
        for tick in ticks:
            x = x0 + (tick / ymax) * (x1 - x0)
            d.line(x, y0, x, y1, "#D9D9D9", 1.1)
            d.text(x, y1 + 36, str(tick), TextStyle(14, color="#444444"))
        d.text((x0 + x1) / 2, y1 + 78, "Medium consumption (L kg-1)", TextStyle(16, weight="bold"))

    group_ys = [230, 395]
    bar_h = 28
    offsets = [-42, 0, 42]
    for group_y, (title, axis_label, values) in zip(group_ys, data):
        for d in draw:
            d.text(160, group_y, axis_label, TextStyle(15, weight="bold", anchor="end"))
        for offset, (scenario, _, color), value in zip(offsets, SCENARIOS, values):
            y = group_y + offset - bar_h / 2
            xw = (value / ymax) * (x1 - x0)
            for d in draw:
                d.rect(x0, y, xw, bar_h, color)
                d.text(x0 + xw + 12, y + bar_h / 2, f"{value:.1f}", TextStyle(14, anchor="start", color="#222222"))

    legend_x = 275
    for i, (name, _, color) in enumerate(SCENARIOS):
        lx = legend_x + i * 210
        for d in draw:
            d.rect(lx, 600, 24, 24, color)
            d.text(lx + 34, 612, name, TextStyle(14, anchor="start"))

    svg.save(OUT_DIR / "fig1_medium_intensity.svg")
    pdf.save()
    png.save()


def log_x(value: float, xmin: float, xmax: float, x0: float, x1: float) -> float:
    return x0 + (math.log10(value) - math.log10(xmin)) / (math.log10(xmax) - math.log10(xmin)) * (x1 - x0)


def make_capacity_figure():
    width, height = 1040, 700
    svg = SVG(width, height)
    pdf_path = OUT_DIR / "fig2_reactor_capacity_100kta.pdf"
    pdf = PDF(pdf_path, width, height)
    png = PNG(OUT_DIR / "fig2_reactor_capacity_100kta.png", width, height)
    draw = [svg, pdf, png]

    volume = read_metric(
        "Required total bioreactor V",
        "Required total production bioreactor volume for 100 kTA",
    )
    reactors = read_metric(
        "Required total bioreactor V",
        "Required number of production bioreactors for 100 kTA",
    )
    reactors = [reactors[0], reactors[1], math.nan]

    x0, x1 = 275, 970
    y0, y1 = 160, 500
    xmin, xmax = 1000, 30000
    ticks = [1000, 3000, 10000, 30000]
    row_y = [230, 340, 450]
    bar_h = 46

    for d in draw:
        d.text(width / 2, 54, "Production bioreactor capacity required for 100 kTA", TextStyle(22, weight="bold"))
        d.text(width / 2, 92, "The x-axis is log-scaled to preserve differences across one order of magnitude.", TextStyle(15, color="#4D4D4D"))
        d.line(x0, y1, x1, y1, "#2A2A2A", 1.8)
        d.line(x0, y0, x0, y1, "#2A2A2A", 1.8)
        for tick in ticks:
            x = log_x(tick, xmin, xmax, x0, x1)
            d.line(x, y0, x, y1, "#D9D9D9", 1.1)
            label = f"{tick:,.0f}"
            d.text(x, y1 + 38, label, TextStyle(14, color="#444444"))
        d.text((x0 + x1) / 2, y1 + 84, "Required total production bioreactor volume (m3, log scale)", TextStyle(16, weight="bold"))

    for y, (name, long_name, color), vol, n in zip(row_y, SCENARIOS, volume, reactors):
        x = log_x(vol, xmin, xmax, x0, x1)
        for d in draw:
            d.multiline_text(250, y, long_name, TextStyle(15, weight="bold", anchor="end"), line_height=20)
            d.rect(x0, y - bar_h / 2, x - x0, bar_h, color)
            label = f"{vol:,.0f} m3"
            if not math.isnan(n):
                label += f"  ({n:,.0f} reactors)"
            d.text(x + 14, y, label, TextStyle(14, anchor="start", color="#222222"))

    svg.save(OUT_DIR / "fig2_reactor_capacity_100kta.svg")
    pdf.save()
    png.save()


def main():
    if not SOURCE_XLSX.exists():
        raise FileNotFoundError(SOURCE_XLSX)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    make_medium_figure()
    make_capacity_figure()
    print(f"Wrote figures to {OUT_DIR}")


if __name__ == "__main__":
    main()
