# Batch vs. Perfusion Paper Figures

This repository contains one APA-style, publication-ready SVG figure comparing required production bioreactor capacity for batch and perfusion scenarios.

## Final Figure

Use this vector file for the paper:

- `fig2_reactor_capacity_100kta.svg`

The figure is in English, uses large labels, and has extra right-side margin so the value labels are not clipped.

## Files

- `fig2_reactor_capacity_100kta.svg`
- `make_batch_perfusion_figures.py`
- `requirements.txt`

The SVG file is a vector graphic and should remain sharp in Word, LaTeX, Illustrator, Inkscape, and journal submission systems.

## APA-Style Figure Captions

**Figure 1**  
Required production bioreactor capacity for 100 kt per year. Total required production bioreactor volume is shown on a log-scaled x-axis to preserve differences across one order of magnitude. Reactor counts are shown where available in the source workbook.

## Reproduce the Figure

From the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 make_batch_perfusion_figures.py
```

The script reads:

```text
Comparison_Batch_vs_Perfusion.xlsx
```

and writes the updated SVG figure to the repository root.

## Notes

- The plots use large sans-serif text for readability in manuscript layouts.
- The colors follow the Okabe-Ito colorblind-safe palette.
- The log-scaled axis in Figure 2 is intentional because the required total bioreactor volume spans roughly one order of magnitude.
