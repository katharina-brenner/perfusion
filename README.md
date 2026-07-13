# Batch vs. Perfusion Paper Figures

This repository contains APA-style, publication-ready figures comparing batch and perfusion scenarios for cultivated meat bioprocessing.

## Where to Find Everything

- `figures/`: final figures for manuscript use.
- `data/`: source Excel workbook used to generate the figures.
- `src/`: reproducible Python plotting script.
- `requirements.txt`: Python packages needed to regenerate the figures.

## Recommended Files for a Paper

Use the vector files whenever possible:

- `figures/fig1_medium_intensity.pdf`
- `figures/fig1_medium_intensity.svg`
- `figures/fig2_reactor_capacity_100kta.pdf`
- `figures/fig2_reactor_capacity_100kta.svg`

The `.png` files are included for quick preview and presentations.

## APA-Style Figure Captions

**Figure 1**  
Medium intensity of batch and perfusion scenarios. Medium consumption is shown in liters per kilogram for dry cell weight (DCW)-normalized and total biomass-normalized output. Values were calculated from the source workbook.

**Figure 2**  
Production bioreactor capacity required for 100 kTA annual production. Required total production bioreactor volume is shown on a log-scaled x-axis to preserve differences across one order of magnitude. Reactor counts are shown where available in the source workbook.

## Reproduce the Figures

From the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 src/make_batch_perfusion_figures.py
```

The script reads:

```text
data/Comparison_Batch_vs_Perfusion.xlsx
```

and writes the final figure files to:

```text
figures/
```

## Notes

- The plotting code uses the Okabe-Ito color palette for colorblind-safe scenario colors.
- PDF and SVG outputs are vector graphics and should remain sharp in Word, LaTeX, Illustrator, Inkscape, and journal submission systems.
- The figures use large sans-serif text and restrained gridlines for readability in manuscript layouts.
