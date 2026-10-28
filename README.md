# Healthcare Analytics — Doctor Visits (build script)

Reads `healthcare_visits.csv` and produces a standalone HTML dashboard
following the Student-Friendly Dataset Understanding Guide screenshots:

  1. Dataset Overview
  2. Main Objective (compare age, health condition, illness, income,
     chronic conditions, healthcare support vs number of visits)
  3. Column Definitions
  4. Grouping the Columns
  5. Simple Meaning of Healthcare Analytics

Plus stat tiles (avg visits is the lead figure), bar/column charts per
grouping, and a full data table view — all styled per the dataviz skill
(thin marks, hairline gridlines, categorical fixed-order hues, sequential
single-hue ramps, legend for >= 2 series, selective direct labels, per-mark
tooltips, dark mode selected, text tokens for labels, tooltip never gated).

Pure stdlib Python (no pandas/matplotlib). Output: `healthcare_dashboard.html`.
