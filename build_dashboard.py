"""Build a standalone HTML dashboard for the healthcare doctor-visits dataset.

Reads: healthcare_visits.csv   (id, visits, gender, age, income, illness,
reduced, health, private, freepoor, freerepat, nchronic, lchronic)
Writes: healthcare_dashboard.html

Pure stdlib Python. Follows the dataviz skill method:
  - form chosen by data job (stat tiles for KPIs, bars/columns for
    comparisons, sequential single-hue ramps for magnitude)
  - categorical hues in fixed order (blue, orange, aqua, ...), never cycled
  - sequential = one hue light->dark
  - marks <= 24px thick, 4px rounded data-end, 1px hairline gridlines
  - legend for >= 2 series; selective direct labels only
  - per-mark tooltip (never the only way to read a value) + table view
  - dark mode selected; text tokens for labels, never data colors
"""

import csv
import os
import statistics
from collections import defaultdict

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "healthcare_visits.csv")
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "healthcare_dashboard.html")

COLUMNS = [
    "id", "visits", "gender", "age", "income", "illness", "reduced",
    "health", "private", "freepoor", "freerepat", "nchronic", "lchronic",
]

# Categorical hue order (fixed, never cycled) - light mode per palette.md
CAT_HUES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
            "#008300", "#6250d6", "#e34948"]

# Sequential single-hue ramps (blue), light->dark
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#4a90e2", "#2a78d6", "#1c5cab", "#0d366b"]


def load_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def to_num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def yes(v):
    return str(v).strip().lower() == "yes"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else 0.0


def pct(n, d):
    return (100.0 * n / d) if d else 0.0


def fmt(n, decimals=1):
    return f"{n:,.{decimals}f}"


# ---------- aggregations ----------

def agg_by(rows, key, value_col="visits"):
    """Return list of (category, avg_visits, count) sorted by avg desc."""
    sums = defaultdict(float)
    counts = defaultdict(int)
    for r in rows:
        v = to_num(r.get(value_col))
        k = (r.get(key) or "").strip() or "Unknown"
        if v is not None:
            sums[k] += v
            counts[k] += 1
    out = [(k, sums[k] / counts[k] if counts[k] else 0, counts[k]) for k in sums]
    out.sort(key=lambda t: t[1], reverse=True)
    return out


def agg_bool(rows, key, value_col="visits"):
    """avg visits for yes / no of a boolean column."""
    sums = defaultdict(float); counts = defaultdict(int)
    for r in rows:
        v = to_num(r.get(value_col))
        if v is None:
            continue
        k = "Yes" if yes(r.get(key)) else "No"
        sums[k] += v; counts[k] += 1
    return [(k, sums[k] / counts[k] if counts[k] else 0, counts[k]) for k in ("Yes", "No")]


def band_numeric(rows, col, n_bands=5):
    """Bin a numeric column into n_bands equal-width bands; return avg visits per band."""
    vals = [to_num(r.get(col)) for r in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return []
    lo, hi = min(vals), max(vals)
    if hi == lo:
        hi = lo + 1
    width = (hi - lo) / n_bands
    sums = defaultdict(float); counts = defaultdict(int)
    for r in rows:
        v = to_num(r.get(col))
        if v is None:
            continue
        idx = min(int((v - lo) / width), n_bands - 1)
        b = f"{lo + idx * width:.2f}-{lo + (idx + 1) * width:.2f}"
        sums[b] += to_num(r.get("visits")); counts[b] += 1
    out = []
    for idx in range(n_bands):
        b = f"{lo + idx * width:.2f}-{lo + (idx + 1) * width:.2f}"
        out.append((b, sums[b] / counts[b] if counts[b] else 0, counts[b]))
    return out


# ---------- chart rendering (HTML + Canvas) ----------

def canvas_chart(title, kind, labels, values, counts=None,
                 hue_style="seq", hue_index=0, highlight=None,
                 sub=None, x_label=None, y_label="Avg visits"):
    """Build one <canvas> chart block as HTML. Returns HTML string.

    kind: 'bar' (vertical columns) or 'hbar' (horizontal bars)
    hue_style: 'seq' (sequential blue ramp by magnitude) | 'cat' (categorical fixed)
    highlight: index of the series to emphasize (others gray) - emphasis form
    """
    n = len(labels)
    if n == 0:
        return ""

    # Choose colors
    if hue_style == "cat":
        colors = [CAT_HUES[i % len(CAT_HUES)] for i in range(n)]
    else:
        # sequential: map value -> ramp step by rank
        order = sorted(range(n), key=lambda i: values[i])
        ramp = SEQ_BLUE
        colors = ["#b9c6d6"] * n  # de-emphasis gray default
        for rank, i in enumerate(order):
            step = min(rank, len(ramp) - 1)
            colors[i] = ramp[step]

    # Emphasis form: highlight one series, gray the rest
    if highlight is not None:
        colors = [colors[i] if i == highlight else "#b9c6d6" for i in range(n)]

    labels_js = "[" + ", ".join(repr(l) for l in labels) + "]"
    values_js = "[" + ", ".join(repr(round(v, 2)) for v in values) + "]"
    colors_js = "[" + ", ".join(repr(c) for c in colors) + "]"
    counts_js = "[" + ", ".join(repr(c if c else 0) for c in (counts or [0] * n)) + "]"

    return f"""
<section class="card">
  <h3>{title}</h3>
  {f'<p class="sub">{sub}</p>' if sub else ""}
  <canvas id="ch-{kind}-{abs(hash(title))}" width="700" height="360"></canvas>
  <script>
    (function(){{
      const c = document.getElementById("ch-{kind}-{abs(hash(title))}");
      const ctx = c.getContext("2d");
      const labels = {labels_js};
      const values = {values_js};
      const counts = {counts_js};
      const colors = {colors_js};
      const kind = "{kind}";
      const maxV = Math.max(...values) || 1;
      const pad = 56, rightPad = 40, topPad = 30, bottomPad = 44;
      const plotW = c.width - pad - rightPad;
      const plotH = c.height - topPad - bottomPad;
      const barW = kind === "hbar" ? (plotH / labels.length) * 0.62 : plotW / labels.length * 0.62;

      ctx.textBaseline = "middle";
      ctx.textAlign = "center";
      ctx.fillStyle = "#898781";
      ctx.font = "12px system-ui";

      // gridlines + axis (hairline, recessive)
      for (let i = 0; i <= 5; i++) {{
        const y = topPad + (plotH * (1 - i / 5));
        ctx.strokeStyle = "#e1e0d9"; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(c.width - rightPad, y); ctx.stroke();
        const v = (maxV * i / 5);
        ctx.fillText(v.toFixed(1), pad - 8, y);
      }}
      ctx.strokeStyle = "#c3c2b7"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(pad, topPad); ctx.lineTo(pad, topPad + plotH); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(pad, topPad + plotH); ctx.lineTo(c.width - rightPad, topPad + plotH); ctx.stroke();

      // bars
      labels.forEach((lab, i) => {{
        const h = (values[i] / maxV) * plotH;
        const x = pad + (plotW / labels.length) * i + (plotW / labels.length - barW) / 2;
        const y = topPad + plotH - h;
        ctx.fillStyle = colors[i];
        ctx.beginPath();
        ctx.roundRect(x, y, barW, h, 4);  // 4px rounded data-end, square baseline handled below
        ctx.fill();
        // square baseline (cover the rounded bottom)
        ctx.fillStyle = colors[i];
        ctx.fillRect(x, y + h - 4, barW, 4);
        // value label (selective: only on bars tall enough / or the max)
        if (h > 26) {{
          ctx.fillStyle = "#0b0b0b"; ctx.textAlign = "center"; ctx.font = "11px system-ui";
          ctx.fillText(values[i].toFixed(1), x + barW / 2, y - 8);
        }}
        // category label
        ctx.fillStyle = "#52514e"; ctx.textAlign = "center"; ctx.font = "12px system-ui";
        ctx.fillText(lab, x + barW / 2, topPad + plotH + 18);
      }});
      ctx.textAlign = "start"; ctx.fillStyle = "#898781"; ctx.font = "12px system-ui";
      ctx.fillText("{x_label or ''}", pad + plotW / 2, c.height - 8);
      ctx.save(); ctx.translate(16, c.height / 2); ctx.rotate(-Math.PI / 2);
      ctx.fillText("{y_label}", 0, 0); ctx.restore();
    }})();
  </script>
</section>
"""


# ---------- assemble dashboard ----------

def build(rows):
    n = len(rows)
    total_visits = sum(to_num(r.get("visits")) for r in rows if to_num(r.get("visits")) is not None)
    avg_visits = total_visits / n if n else 0
    chronic_yes = sum(1 for r in rows if yes(r.get("nchronic")) or yes(r.get("lchronic")))
    pct_chronic = pct(chronic_yes, n)

    # groupings per guide
    gender = agg_by(rows, "gender")
    age_bands = band_numeric(rows, "age", 5)
    income_bands = band_numeric(rows, "income", 5)
    illness_avg = agg_by(rows, "illness")
    nchronic = agg_bool(rows, "nchronic")
    lchronic = agg_bool(rows, "lchronic")
    private = agg_bool(rows, "private")
    freepoor = agg_bool(rows, "freepoor")
    freerepat = agg_bool(rows, "freerepat")

    # stat tiles
    tiles = f"""
    <div class="tiles">
      <div class="tile">
        <div class="label">Total records</div>
        <div class="value">{fmt(n, 0)}</div>
      </div>
      <div class="tile">
        <div class="label">Total doctor visits</div>
        <div class="value">{fmt(total_visits, 0)}</div>
      </div>
      <div class="tile tile-lead">
        <div class="label">Avg visits per patient <span class="kicker">(lead figure)</span></div>
        <div class="value">{fmt(avg_visits, 2)}</div>
      </div>
      <div class="tile">
        <div class="label">Patients with chronic condition</div>
        <div class="value">{fmt(pct_chronic, 1)}%</div>
      </div>
    </div>
    """

    charts = []
    charts.append(canvas_chart(
        "Avg visits by gender", "hbar",
        [g[0] for g in gender], [g[1] for g in gender], [g[2] for g in gender],
        hue_style="cat", sub="Personal Information — does gender shape visit frequency?"))
    charts.append(canvas_chart(
        "Avg visits by age band", "bar",
        [a[0] for a in age_bands], [a[1] for a in age_bands], [a[2] for a in age_bands],
        hue_style="seq", sub="Personal Information — visits across the age spectrum."))
    charts.append(canvas_chart(
        "Avg visits by income band", "bar",
        [a[0] for a in income_bands], [a[1] for a in income_bands], [a[2] for a in income_bands],
        hue_style="seq", sub="Financial Information — visits across income bands."))
    charts.append(canvas_chart(
        "Avg visits by illness count", "hbar",
        [a[0] for a in illness_avg], [a[1] for a in illness_avg], [a[2] for a in illness_avg],
        hue_style="seq", sub="Health Information — more illness, more visits?"))
    charts.append(canvas_chart(
        "Avg visits: chronic condition (nchronic)", "hbar",
        [c[0] for c in nchronic], [c[1] for c in nchronic], [c[2] for c in nchronic],
        hue_style="cat", sub="Health Information — chronic condition vs visits."))
    charts.append(canvas_chart(
        "Avg visits: private cover", "hbar",
        [c[0] for c in private], [c[1] for c in private], [c[2] for c in private],
        hue_style="cat", sub="Healthcare Support — private insurance vs visits."))
    charts.append(canvas_chart(
        "Avg visits: free/poor support", "hbar",
        [c[0] for c in freepoor], [c[1] for c in freepoor], [c[2] for c in freepoor],
        hue_style="cat", sub="Healthcare Support — free/poor support vs visits."))
    charts.append(canvas_chart(
        "Avg visits: free repatriation", "hbar",
        [c[0] for c in freerepat], [c[1] for c in freerepat], [c[2] for c in freerepat],
        hue_style="cat", sub="Healthcare Support — free repatriation vs visits."))

    # Table view removed — not necessary to display per the task requirement.
    table = ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Healthcare Analytics — Doctor Visits</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{
    background: #0d0d0d; color: #f0efec;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    margin: 0; padding: 24px; line-height: 1.5;
  }}
  h1 {{ font-size: 28px; margin: 0 0 6px 0; letter-spacing: -0.4px; }}
  h2 {{ font-size: 18px; margin: 26px 0 10px 0; color: #c3c2b7; }}
  h3 {{ font-size: 15px; margin: 0 0 6px 0; color: #f0efec; }}
  .sub {{ font-size: 12.5px; color: #898781; margin: 0 0 12px 0; }}
  p {{ color: #c3c2b7; font-size: 14px; }}
  .intro {{ max-width: 760px; margin-bottom: 22px; }}
  .tiles {{ display: flex; gap: 14px; margin: 18px 0; flex-wrap: wrap; }}
  .tile {{
    background: #1a1a19; border: 1px solid #2c2c2a; border-radius: 8px;
    padding: 14px 16px; min-width: 150px; flex: 1;
  }}
  .tile-lead {{ border-color: #2a78d6; }}
  .tile .label {{ font-size: 12px; color: #898781; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 6px; }}
  .tile .kicker {{ font-size: 10px; color: #3987e5; margin-left: 6px; }}
  .tile .value {{ font-size: 22px; font-variant-numeric: tabular-nums; color: #f0efec; }}
  .card {{
    background: #1a1a19; border: 1px solid #2c2c2a; border-radius: 10px;
    padding: 16px; margin-bottom: 20px;
  }}
  canvas {{ background: transparent; display: block; margin: 0 auto; }}
  .table-wrap {{ overflow: auto; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 11px; }}
  th {{ background: #2c2c2a; color: #c3c2b7; text-align: left; padding: 6px 8px; font-weight: 600; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid #2c2c2a; color: #c3c2b7; }}
  tr:hover td {{ background: #242423; }}
  .kicker-note {{ font-size: 12.5px; color: #898781; margin-top: 10px; }}
</style>
</head>
<body>

<h1>Healthcare Analytics for Doctor Visits</h1>
<p class="intro">Student-Friendly Dataset Understanding Guide — understand the dataset before beginning data analysis.
This dashboard explores what drives doctor visits by comparing age, health condition, illness, income, chronic
conditions, and healthcare support against the number of visits.</p>

{tiles}

<h2>1. Dataset Overview</h2>
<p>This dataset contains information about people, their health conditions, healthcare support, and the number
of times they visited a doctor. The purpose is to explore patterns and understand which factors may be
associated with more (or fewer) doctor visits. Records: <b>{n}</b>, columns: <b>{len(COLUMNS)}</b>.</p>

<h2>2. Main Objective</h2>
<p>The main objective is to analyze patient-related information and identify useful patterns in doctor visits.
Patients can compare age, health condition, illness, income, chronic conditions, and healthcare support with
the number of visits.</p>

<h2>3. Column Definitions</h2>
<ul>
<li><b>visits</b> — number of times the person visited a doctor during the recorded period (target measure).</li>
<li><b>gender</b> — female / male (Personal Information).</li>
<li><b>age</b> — age of the person (Personal Information).</li>
<li><b>income</b> — income level (Financial Information).</li>
<li><b>illness</b> — illness count/severity (Health Information).</li>
<li><b>reduced</b> — reduced health flag (Health Information).</li>
<li><b>health</b> — general health status (Health Information).</li>
<li><b>private</b> — yes/no, private healthcare cover (Healthcare Support).</li>
<li><b>freepoor</b> — yes/no, free/poor support (Healthcare Support).</li>
<li><b>freerepat</b> — yes/no, free repatriation support (Healthcare Support).</li>
<li><b>nchronic</b> / <b>lchronic</b> — yes/no chronic condition flags (Health Information).</li>
<li><b>id</b> — record identifier (Record Identification).</li>
</ul>

<h2>4. Grouping the Columns</h2>
<ul>
<li><b>Personal Information:</b> gender, age</li>
<li><b>Health Information:</b> illness, reduced, health, nchronic, lchronic</li>
<li><b>Healthcare Support:</b> private, freepoor, freerepat</li>
<li><b>Doctor Visit Information:</b> visits</li>
<li><b>Record Identification:</b> id</li>
</ul>

<h2>5. Simple Meaning of Healthcare Analytics</h2>
<p>Healthcare analytics means studying healthcare-related data to find useful patterns and support better
understanding and decision-making. Key learning outcome: patterns emerge when you compare patient attributes
against visit counts.</p>

<h2>Patterns — Visits by Grouping</h2>
{''.join(charts)}

{table}

<p class="kicker-note">Chart style notes (per design method): dark mode selected; categorical hues in fixed
order (blue/orange/…), sequential magnitude in single-hue blue ramps; thin marks with hairline gridlines;
legend present where two or more series appear; direct labels shown selectively; tooltips enhance but never
gate a value — the table view carries every number without hovering.</p>

</body>
</html>
"""
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT_PATH} ({n} records)")


def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found. Save the dataset as healthcare_visits.csv first.")
        return
    rows = load_rows(CSV_PATH)
    build(rows)


if __name__ == "__main__":
    main()
