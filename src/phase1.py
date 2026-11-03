"""
Phase 1 - NHANES 2021-2023 (cycle L)
Topic: How much do the three consecutive oscillometric systolic BP readings differ
       (first vs third reading) in U.S. adults, and does the gap vary by sex / age?

Run from the repository root:
    python src/phase1.py
Inputs : data/DEMO_L.xpt, data/BPXO_L.xpt, data/BMX_L.xpt   (download from CDC, see data/README.md)
Outputs: figures/phase1/*.png, reports/phase1/tables/*.csv, reports/phase1/stats.json
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures" / "phase1"
TAB = ROOT / "reports" / "phase1" / "tables"
for p in (FIG, TAB):
    p.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 200, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})
C1, C2, C3 = "#2b6cb0", "#dd6b20", "#718096"

demo = pd.read_sas(DATA / "DEMO_L.xpt", format="xport")
bpxo = pd.read_sas(DATA / "BPXO_L.xpt", format="xport")
bmx = pd.read_sas(DATA / "BMX_L.xpt", format="xport")

flow = []  # (step, n)
flow.append(("DEMO_L: all records", len(demo)))
flow.append(("BPXO_L: all records", len(bpxo)))
flow.append(("BMX_L: all records", len(bmx)))
assert not demo.SEQN.duplicated().any() and not bpxo.SEQN.duplicated().any() and not bmx.SEQN.duplicated().any()

adults = demo[demo.RIDAGEYR >= 20]
flow.append(("Age >= 20 (interviewed)", len(adults)))
adults = adults[adults.RIDSTATR == 2]
flow.append(("... and examined in MEC (RIDSTATR=2)", len(adults)))

df = (adults.merge(bpxo, on="SEQN", how="left", indicator="m_bp")
            .merge(bmx[["SEQN", "BMXBMI", "BMXWT", "BMXHT"]], on="SEQN", how="left", indicator="m_bmx"))
flow.append(("... after merge with BPXO_L (rows)", int((df.m_bp == "both").sum())))
flow.append(("... after merge with BMX_L (rows)", int((df.m_bmx == "both").sum())))

SYS, DIA = ["BPXOSY1", "BPXOSY2", "BPXOSY3"], ["BPXODI1", "BPXODI2", "BPXODI3"]
df["n_valid_bp"] = df[SYS].notna().sum(axis=1)
flow.append(("... with >= 1 systolic reading", int((df.n_valid_bp >= 1).sum())))
flow.append(("... with all 3 systolic readings (ANALYTIC)", int((df.n_valid_bp == 3).sum())))
df["sex"] = df.RIAGENDR.map({1: "Male", 2: "Female"})
df["age_grp"] = pd.cut(df.RIDAGEYR, [19, 39, 59, 200], labels=["20-39", "40-59", "60+"])
race_map = {1: "Mexican American", 2: "Other Hispanic", 3: "NH White", 4: "NH Black", 6: "NH Asian", 7: "Other/Multi"}
df["race"] = df.RIDRETH3.map(race_map)
df["bmi_grp"] = pd.cut(df.BMXBMI, [0, 18.5, 25, 30, 200], right=False,
                       labels=["<18.5", "18.5-24.9", "25-29.9", ">=30"])
df["cuff"] = df.BPAOCSZ.map(lambda v: f"code {int(v)}" if pd.notna(v) else np.nan)
df["arm"] = df.BPAOARM.map(lambda b: b.decode() if isinstance(b, bytes) else b).replace({"": np.nan, "R": "Right", "L": "Left"})

df["d13"] = df.BPXOSY1 - df.BPXOSY3      # first minus third (key quantity)
df["d12"] = df.BPXOSY1 - df.BPXOSY2
df["d23"] = df.BPXOSY2 - df.BPXOSY3
df["dia_d13"] = df.BPXODI1 - df.BPXODI3
df["first_higher"] = np.where(df.d13.notna(), (df.d13 > 0).astype(float), np.nan)

an = df[df.n_valid_bp == 3].copy()
w = "WTMEC2YR"
def wmean(x, wt):
    m = x.notna() & wt.notna()
    return np.average(x[m], weights=wt[m])


def summ(s):
    s = s.dropna()
    q1, q3 = s.quantile([.25, .75])
    return dict(n=len(s), mean=s.mean(), median=s.median(), sd=s.std(), q1=q1, q3=q3,
                iqr=q3 - q1, min=s.min(), max=s.max())


def save(t, name):
    t.to_csv(TAB / f"{name}.csv", index=False, encoding="utf-8-sig")


t1 = pd.DataFrame(flow, columns=["step", "n"])
save(t1, "T1_flow")

rows = []
for var, lab in [("sex", "Sex"), ("age_grp", "Age group"), ("race", "Race/ethnicity"),
                 ("bmi_grp", "BMI category"), ("cuff", "Cuff size (coded)"), ("arm", "Arm used")]:
    cnt = an[var].value_counts(dropna=False)
    wsum = an.groupby(var, dropna=False)[w].sum()
    for k in cnt.index:
        rows.append(dict(variable=lab, level="Missing" if pd.isna(k) else str(k), n=int(cnt[k]),
                         pct_unweighted=100 * cnt[k] / len(an),
                         pct_weighted=100 * wsum[k] / an[w].sum()))
t3 = pd.DataFrame(rows)
save(t3, "T3_frequencies")

numvars = {"RIDAGEYR": "Age (years)", "BPXOSY1": "Systolic reading 1", "BPXOSY2": "Systolic reading 2",
           "BPXOSY3": "Systolic reading 3", "BPXODI1": "Diastolic reading 1", "BPXODI3": "Diastolic reading 3",
           "d13": "Systolic: reading1 - reading3", "d12": "Systolic: reading1 - reading2",
           "d23": "Systolic: reading2 - reading3", "dia_d13": "Diastolic: reading1 - reading3",
           "BMXBMI": "BMI (kg/m2)"}
t4 = pd.DataFrame([dict(variable=lab, **summ(an[v])) for v, lab in numvars.items()])
save(t4, "T4_numeric_summary")

rows = []
groups = [("All adults", an)] + [(f"Sex: {s}", an[an.sex == s]) for s in ["Male", "Female"]] \
         + [(f"Age: {a}", an[an.age_grp == a]) for a in ["20-39", "40-59", "60+"]]
for lab, g in groups:
    rows.append(dict(group=lab, n=len(g),
                     mean_SBP1_raw=g.BPXOSY1.mean(), mean_SBP1_wtd=wmean(g.BPXOSY1, g[w]),
                     mean_diff13_raw=g.d13.mean(), mean_diff13_wtd=wmean(g.d13, g[w]),
                     pct_first_higher_raw=100 * g.first_higher.mean(),
                     pct_first_higher_wtd=100 * wmean(g.first_higher, g[w])))
t5 = pd.DataFrame(rows)
save(t5, "T5_raw_vs_weighted")

rows = []
for (s, a), g in an.groupby(["sex", "age_grp"], observed=True):
    rows.append(dict(sex=s, age_group=a, n=len(g), mean_diff13=g.d13.mean(), median_diff13=g.d13.median(),
                     sd_diff13=g.d13.std(), mean_diff13_wtd=wmean(g.d13, g[w]),
                     pct_first_higher=100 * g.first_higher.mean()))
t6 = pd.DataFrame(rows)
save(t6, "T6_diff_by_sex_age")

rows = []
for b, g in an.groupby("bmi_grp", observed=True):
    rows.append(dict(bmi_group=b, n=len(g), mean_diff13=g.d13.mean(), median_diff13=g.d13.median(),
                     sd_diff13=g.d13.std(), mean_diff13_wtd=wmean(g.d13, g[w])))
save(pd.DataFrame(rows), "T6b_diff_by_bmi")

df["bp_status"] = np.select([df.n_valid_bp == 3, df.n_valid_bp == 0], ["3 readings", "no BP"], "1-2 readings")
rows = []
for lab, key in [("Sex", "sex"), ("Age group", "age_grp")]:
    for lv, g in df.groupby(key, observed=True):
        rows.append(dict(variable=lab, level=str(lv), n_examined=len(g),
                         pct_3_readings=100 * (g.n_valid_bp == 3).mean(),
                         pct_1_2_readings=100 * g.n_valid_bp.isin([1, 2]).mean(),
                         pct_no_bp=100 * (g.n_valid_bp == 0).mean()))
t7 = pd.DataFrame(rows)
save(t7, "T7_missing_bp")

miss_other = {
    "BMI missing among analytic": int(an.BMXBMI.isna().sum()),
    "cuff size missing among analytic": int(an.cuff.isna().sum()),
    "arm missing among analytic": int(an.arm.isna().sum()),
    "weight missing/zero among analytic": int((an[w].isna() | (an[w] <= 0)).sum()),
    "any diastolic >= systolic (3 readings)": int((df[DIA].values >= df[SYS].values).any(axis=1).sum()),
    "age=80 (top-coded 80+) among analytic": int((an.RIDAGEYR >= 80).sum()),
    "exactly identical 3 systolic readings": int(((an.BPXOSY1 == an.BPXOSY2) & (an.BPXOSY2 == an.BPXOSY3)).sum()),
    "|reading1-reading3| >= 30 mmHg": int((an.d13.abs() >= 30).sum()),
}

fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.hist(an.BPXOSY1, bins=np.arange(60, 235, 5), color=C1, edgecolor="white")
ax.axvline(an.BPXOSY1.mean(), color=C2, lw=2, label=f"Mean = {an.BPXOSY1.mean():.1f}")
ax.axvline(an.BPXOSY1.median(), color="k", ls="--", lw=1.5, label=f"Median = {an.BPXOSY1.median():.0f}")
ax.set(xlabel="First systolic BP reading (mmHg)", ylabel="Number of adults",
       title="Distribution of the first systolic reading (adults >= 20 y, n=%d)" % len(an))
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "fig1_hist_sbp1.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.8))
bp = ax.boxplot([an.BPXOSY1, an.BPXOSY2, an.BPXOSY3], tick_labels=["Reading 1", "Reading 2", "Reading 3"],
                patch_artist=True, showmeans=True, flierprops=dict(markersize=2, alpha=.4),
                meanprops=dict(marker="D", markerfacecolor=C2, markeredgecolor=C2, markersize=5))
for p in bp["boxes"]:
    p.set(facecolor="#bee3f8", edgecolor=C1)
ax.set(ylabel="Systolic BP (mmHg)", title="Systolic BP by consecutive reading (diamond = mean)")
fig.tight_layout(); fig.savefig(FIG / "fig2_box_readings.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.hist(an.d13, bins=np.arange(-40.5, 41.5, 2), color=C3, edgecolor="white")
ax.axvline(0, color="k", lw=1)
ax.axvline(an.d13.mean(), color=C2, lw=2, label=f"Mean = {an.d13.mean():.2f}")
ax.set(xlabel="Reading 1 minus reading 3, systolic (mmHg)", ylabel="Number of adults",
       title="Within-person difference between first and third reading")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "fig3_hist_diff13.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.8, 4))
ages = ["20-39", "40-59", "60+"]
x = np.arange(len(ages)); bw = 0.19
for i, (s, col) in enumerate([("Male", C1), ("Female", C2)]):
    raw = [an[(an.sex == s) & (an.age_grp == a)].d13.mean() for a in ages]
    wt = [wmean(an[(an.sex == s) & (an.age_grp == a)].d13, an[(an.sex == s) & (an.age_grp == a)][w]) for a in ages]
    ax.bar(x + (2 * i - 1.5) * bw, raw, bw, color=col, label=f"{s} - unweighted")
    ax.bar(x + (2 * i - 0.5) * bw, wt, bw, color=col, alpha=.45, hatch="//", label=f"{s} - weighted")
ax.axhline(0, color="k", lw=.8)
ax.set_xticks(x, ages)
ax.set(xlabel="Age group (years)", ylabel="Mean (reading 1 - reading 3), mmHg",
       title="Mean first-minus-third systolic difference: raw vs survey-weighted")
ax.legend(frameon=False, fontsize=8, ncol=2)
fig.tight_layout(); fig.savefig(FIG / "fig4_diff_by_sex_age.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.8))
m = df.groupby("age_grp", observed=True).apply(lambda g: 100 * (g.n_valid_bp < 3).mean(), include_groups=False)
ax.bar(m.index.astype(str), m.values, color=C3)
for i, v in enumerate(m.values):
    ax.text(i, v + .2, f"{v:.1f}%", ha="center")
ax.set(xlabel="Age group (years)", ylabel="Examined adults lacking 3 valid readings (%)",
       title="Missing blood-pressure data by age group")
fig.tight_layout(); fig.savefig(FIG / "fig5_missing_by_age.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.8))
g = an.groupby("bmi_grp", observed=True).d13.agg(["mean", "count"])
ax.bar(g.index.astype(str), g["mean"], color=C1)
for i, (v, n) in enumerate(zip(g["mean"], g["count"])):
    ax.text(i, v + (0.03 if v >= 0 else -0.12), f"n={n}", ha="center", fontsize=8)
ax.axhline(0, color="k", lw=.8)
ax.set_ylim(min(0, g["mean"].min() * 1.2), g["mean"].max() * 1.25)
ax.set(xlabel="BMI category (kg/m$^2$)", ylabel="Mean (reading 1 - reading 3), mmHg",
       title="Mean first-minus-third difference by BMI category")
fig.tight_layout(); fig.savefig(FIG / "fig6_diff_by_bmi.png"); plt.close(fig)

stats = dict(
    n_analytic=len(an), sum_weights_analytic=float(an[w].sum()),
    weights_min=float(an[w].min()), weights_max=float(an[w].max()),
    weight_ratio=float(an[w].max() / an[w].min()),
    n_psu=int(an.groupby(["SDMVSTRA", "SDMVPSU"]).ngroups), n_strata=int(an.SDMVSTRA.nunique()),
    pct_first_higher=100 * an.first_higher.mean(),
    pct_equal=100 * (an.d13 == 0).mean(), pct_first_lower=100 * (an.d13 < 0).mean(),
    corr_d13_age=float(an[["d13", "RIDAGEYR"]].corr().iloc[0, 1]),
    miss_other=miss_other,
)
(ROOT / "reports" / "phase1" / "stats.json").write_text(json.dumps(stats, indent=2, default=float))

(DATA / "processed").mkdir(exist_ok=True)
an[["SEQN", "sex", "RIDAGEYR", "age_grp", "race", "BMXBMI", "bmi_grp", "cuff", "arm", *SYS, *DIA,
    "d13", "d12", "d23", w, "SDMVSTRA", "SDMVPSU"]].to_csv(DATA / "processed" / "analytic_bp_readings.csv", index=False)

pd.set_option("display.width", 200, "display.max_columns", 30)
for n, t in [("T1", t1), ("T3", t3), ("T4", t4), ("T5", t5), ("T6", t6), ("T7", t7)]:
    print(n); print(t.round(3).to_string(index=False)); print()
print(json.dumps(stats, indent=2, default=float))
