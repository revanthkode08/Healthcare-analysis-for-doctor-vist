"""Generate a realistic healthcare_visits.csv dataset (5,190 records).

Matches the schema in dataset-schema.md:
  id, visits, gender, age, income, illness, reduced, health,
  private, freepoor, freerepat, nchronic, lchronic

Distributions are chosen to be plausible for a doctor-visits study and to
contain real signal (older age -> more chronic conditions -> more visits,
lower income -> more free/poor support, etc.) so the dashboard's patterns
are meaningful. Pure stdlib Python.
"""

import csv
import os
import random

random.seed(42)

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "healthcare_visits.csv")
N = 5190

GENDERS = ["female", "male"]


def sample_age():
    """Skewed toward older adults (more healthcare utilization)."""
    # Rough mix: young 20%, mid 35%, older 30%, elderly 15%
    r = random.random()
    if r < 0.20:
        return int(random.uniform(18, 40))
    elif r < 0.55:
        return int(random.uniform(40, 60))
    elif r < 0.85:
        return int(random.uniform(60, 78))
    else:
        return int(random.uniform(78, 90))


def sample_income(age):
    """Income rises with age somewhat, then plateaus/declines."""
    base = 30000 + age * 1200
    if age > 65:
        base *= 0.75  # retirement
    return int(max(8000, random.gauss(base, base * 0.28)))


def sample_illness(age, nchronic):
    """Illness count rises with age and chronic conditions."""
    base = 0.8 + age * 0.05 + nchronic * 1.4
    return max(0, int(random.gauss(base, 1.1)))


def sample_health(age, nchronic, illness):
    """Health status 1-5 (1=poor, 5=excellent), worse with age/chronic."""
    base = 4.6 - age * 0.028 - nchronic * 0.55 - illness * 0.18
    v = int(round(random.gauss(base, 0.7)))
    return max(1, min(5, v))


def sample_reduced(health, nchronic):
    """Reduced activity: more likely with poor health / chronic conditions."""
    p = 0.06 + (5 - health) * 0.09 + nchronic * 0.16
    return "yes" if random.random() < p else "no"


def sample_visits(age, illness, health, nchronic, reduced, freepoor):
    """Doctor visits: Poisson-like count driven by health needs."""
    lam = 0.9 + age * 0.022 + illness * 0.42 + (5 - health) * 0.22
    lam += nchronic * 0.55
    if reduced == "yes":
        lam += 0.5
    if freepoor == "yes":
        lam += 0.35  # free/poor support -> easier access
    # Poisson via inverse-CDF
    L = 2.718281828 ** (-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


rows = []
for i in range(1, N + 1):
    gender = random.choice(GENDERS)
    age = sample_age()
    income = sample_income(age)
    nchronic = 1 if random.random() < (0.06 + age * 0.0045) else 0
    lchronic = 1 if random.random() < (0.04 + age * 0.0035) else 0
    illness = sample_illness(age, nchronic)
    health = sample_health(age, nchronic, illness)
    reduced = sample_reduced(health, nchronic)
    private = "yes" if random.random() < (0.42 + age * -0.0008) else "no"
    freepoor = "yes" if random.random() < (0.08 + (5 - health) * 0.03) else "no"
    freerepat = "yes" if random.random() < 0.03 else "no"
    visits = sample_visits(age, illness, health, nchronic, reduced, freepoor)
    rows.append([i, visits, gender, age, income, illness, reduced, health,
                 private, freepoor, freerepat, nchronic, lchronic])

with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "visits", "gender", "age", "income", "illness", "reduced",
                "health", "private", "freepoor", "freerepat", "nchronic", "lchronic"])
    w.writerows(rows)

print(f"Wrote {OUT_PATH} ({len(rows)} records)")