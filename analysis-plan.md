# Analysis Plan — Healthcare Doctor Visits

Objective (per guide): compare age, health condition, illness, income, chronic conditions, and healthcare support with number of doctor visits; identify useful patterns.

Planned outputs (single standalone HTML dashboard + embedded table):
- Stat tiles (KPI row): total records, total visits, avg visits per patient, % with chronic condition — avg visits is the lead figure.
- Bar chart: average visits by gender (categorical, 2 fixed slots blue/orange; no legend needed for one measure).
- Column chart: average visits by age band (sequential blue ramp by magnitude).
- Column chart: average visits by income band (sequential blue ramp).
- Bar chart: visits by nchronic / lchronic (yes/no) — categorical 2 series.
- Healthcare support: visits by private/freepoor/freerepat (yes/no).
- Table view: every value reachable without tooltip.
- Dark mode selected; text tokens for labels; tooltip per mark; never gated.

Non-negotiables: no dual-axis; categorical hues never cycled past 8; sequential one-hue; marks thin with 2px surface gaps; legend present for ≥2 series; selective direct labels.
