"""Phase 2 - NHANES 2021–2023 (cycle L)
Topic: Probability and probability distributions for the first-versus-third systolic BP reading.

Run from the repository root:
    python src/phase2.py
Inputs : data/DEMO_L.xpt, data/BPXO_L.xpt, data/BMX_L.xpt (see data/README.md)
Outputs: figures/phase2/*.png, reports/phase2/tables/*.csv, reports/phase2/stats.json
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm, hypergeom, binom, skew, kurtosis
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'reports' / 'phase2'
TAB = OUT / 'tables'
FIG = ROOT / 'figures' / 'phase2'
for p in [TAB, FIG]:
    p.mkdir(parents=True, exist_ok=True)
                                                                          
demo = pd.read_sas(DATA / 'DEMO_L.xpt', format='xport')
bpxo = pd.read_sas(DATA / 'BPXO_L.xpt', format='xport')
bmx = pd.read_sas(DATA / 'BMX_L.xpt', format='xport')
assert all((not x.SEQN.duplicated().any() for x in [demo, bpxo, bmx]))
adults = demo[(demo.RIDAGEYR >= 20) & (demo.RIDSTATR == 2)].copy()
df = adults.merge(bpxo, on='SEQN', how='left').merge(bmx[['SEQN', 'BMXBMI']], on='SEQN', how='left')
SYS = ['BPXOSY1', 'BPXOSY2', 'BPXOSY3']
df['n_valid'] = df[SYS].notna().sum(axis=1)
an = df[df.n_valid == 3].copy()
assert len(an) == 5842 and an.SEQN.nunique() == 5842
an['X'] = an.BPXOSY1 - an.BPXOSY3
an['sex'] = an.RIAGENDR.map({1: 'مرد', 2: 'زن'})
an['age_group'] = pd.cut(an.RIDAGEYR, [19, 39, 59, 200], labels=['۲۰–۳۹', '۴۰–۵۹', '۶۰+'])
an['H1'] = an.BPXOSY1 >= 130
an['H3'] = an.BPXOSY3 >= 130
an['D'] = an.H1 & ~an.H3
an['F'] = an.X >= 5
an['G'] = an.X.abs() >= 5
N = len(an)
n = 50
K = int(an.D.sum())
p = K / N

def dump(df_, name):
    df_.to_csv(TAB / f'{name}.csv', index=False, encoding='utf-8-sig')

def prob(mask):
    return float(np.mean(mask))
                                                     
ct = pd.crosstab(an.H1, an.H3).reindex(index=[False, True], columns=[False, True], fill_value=0)
ct.index = ['H1=0', 'H1=1']
ct.columns = ['H3=0', 'H3=1']
ct.to_csv(TAB / 'T01_H1_H3_crosstab.csv', encoding='utf-8-sig')
events = []
for key, label, mask in [('H1', 'BPXOSY1 >= 130', an.H1), ('H3', 'BPXOSY3 >= 130', an.H3), ('D', 'BPXOSY1 >=130 and BPXOSY3 <130', an.D), ('F', 'X >= 5 mmHg', an.F), ('G', '|X| >= 5 mmHg', an.G), ('B', 'Age >= 60', an.RIDAGEYR >= 60)]:
    events.append(dict(event=key, definition=label, count=int(mask.sum()), n=N, probability=prob(mask), percent=100 * prob(mask)))
dump(pd.DataFrame(events), 'T02_event_probabilities')
cond = [('P(H3|H1)', an.loc[an.H1, 'H3'].mean()), ('P(H3|not H1)', an.loc[~an.H1, 'H3'].mean()), ('P(H1|H3)', an.loc[an.H3, 'H1'].mean()), ('P(H1|not H3)', an.loc[~an.H3, 'H1'].mean()), ('P(D|H1)', an.loc[an.H1, 'D'].mean()), ('P(F|age>=60)', an.loc[an.RIDAGEYR >= 60, 'F'].mean()), ('P(F|age<60)', an.loc[an.RIDAGEYR < 60, 'F'].mean()), ('P(G|age>=60)', an.loc[an.RIDAGEYR >= 60, 'G'].mean()), ('P(G|age<60)', an.loc[an.RIDAGEYR < 60, 'G'].mean())]
dump(pd.DataFrame(cond, columns=['conditional_probability', 'value']), 'T03_conditional_probabilities')
rows = []
for v in ['کل نمونه', 'مرد', 'زن', '۲۰–۳۹', '۴۰–۵۹', '۶۰+']:
    g = an if v == 'کل نمونه' else an[an.sex == v] if v in ['مرد', 'زن'] else an[an.age_group == v]
    for e in ['H1', 'D', 'F', 'G']:
        rows.append(dict(group=v, event=e, n=len(g), count=int(g[e].sum()), probability=float(g[e].mean())))
dump(pd.DataFrame(rows), 'T04_event_by_subgroup')
                                             
pairs = [('H1', 'H3'), ('F', 'age60'), ('F', 'male'), ('H1', 'age60')]
rows = []
for a, b in pairs:
    A = an[a] if a in an else an.RIDAGEYR >= 60 if a == 'age60' else an.RIAGENDR == 1
    B = an[b] if b in an else an.RIDAGEYR >= 60 if b == 'age60' else an.RIAGENDR == 1
    pa, pb, pab = (A.mean(), B.mean(), (A & B).mean())
    rows.append(dict(A=a, B=b, P_A=pa, P_B=pb, P_A_times_P_B=pa * pb, P_joint=pab, ratio_joint_to_product=pab / (pa * pb), expected_joint_count=N * pa * pb, observed_joint_count=int((A & B).sum()), difference=pab - pa * pb))
dump(pd.DataFrame(rows), 'T05_independence_checks')
                                                       
bayes = [('P(H1)', an.H1.mean()), ('P(H1|H3)', an.loc[an.H3, 'H1'].mean()), ('P(H1|not H3)', an.loc[~an.H3, 'H1'].mean()), ('P(H3)', an.H3.mean()), ('P(H3|H1)', an.loc[an.H1, 'H3'].mean()), ('P(H3|not H1)', an.loc[~an.H1, 'H3'].mean()), ('P(age>=60|F)', ((an.RIDAGEYR >= 60) & an.F).sum() / an.F.sum()), ('P(age>=60)', (an.RIDAGEYR >= 60).mean())]
dump(pd.DataFrame(bayes, columns=['quantity', 'value']), 'T06_bayes')
                                                                                
rng = np.random.default_rng(20261110)
sims = rng.hypergeometric(K, N - K, n, size=2000)
M = 100000
sims_large = rng.hypergeometric(K, N - K, n, size=M)
y = np.arange(0, n + 1)
hyp = hypergeom.pmf(y, N, K, n)
bp = binom.pmf(y, n, p)
summary = pd.DataFrame([{'method': 'simulation_2000', 'mean': sims.mean(), 'variance': sims.var(ddof=1), 'sd': sims.std(ddof=1)}, {'method': 'simulation_100000', 'mean': sims_large.mean(), 'variance': sims_large.var(ddof=1), 'sd': sims_large.std(ddof=1)}, {'method': 'hypergeometric_exact', 'mean': n * p, 'variance': n * p * (1 - p) * (N - n) / (N - 1), 'sd': np.sqrt(n * p * (1 - p) * (N - n) / (N - 1))}, {'method': 'binomial_approximation', 'mean': n * p, 'variance': n * p * (1 - p), 'sd': np.sqrt(n * p * (1 - p))}])
dump(summary, 'T07_binomial_hypergeometric_summary')
dump(pd.DataFrame({'k': y, 'hypergeometric_probability': hyp, 'binomial_probability': bp, 'absolute_difference': abs(hyp - bp)}), 'T08_distribution_comparison')
                                                                             
normal_rows = []
for var in ['BPXOSY1', 'X']:
    s = an[var].astype(float)
    mu = s.mean()
    sd = s.std(ddof=1)
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    z = np.abs((s - mu) / sd)
    row = {'variable': var, 'n': len(s), 'mean': mu, 'median': s.median(), 'sd': sd, 'skewness': skew(s, bias=False), 'excess_kurtosis': kurtosis(s, bias=False), 'q1': q1, 'q3': q3, 'iqr': iqr, 'min': s.min(), 'max': s.max(), 'lower_fence': q1 - 1.5 * iqr, 'upper_fence': q3 + 1.5 * iqr, 'outside_iqr_fences': int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()), 'abs_z_gt_3': int((z > 3).sum()), 'abs_z_gt_4': int((z > 4).sum())}
    for k in [1, 2, 3]:
        row[f'within_{k}sd_pct'] = 100 * ((s >= mu - k * sd) & (s <= mu + k * sd)).mean()
    normal_rows.append(row)
dump(pd.DataFrame(normal_rows), 'T09_normality_diagnostics')
normal_compare = []
for label, emp, threshold, mu, sd in [('H1: SBP1>=130', an.H1.mean(), 130, an.BPXOSY1.mean(), an.BPXOSY1.std(ddof=1)), ('F: X>=5', an.F.mean(), 5, an.X.mean(), an.X.std(ddof=1)), ('G: |X|>=5', an.G.mean(), 5, an.X.mean(), an.X.std(ddof=1)), ('|X|>=10', (an.X.abs() >= 10).mean(), 10, an.X.mean(), an.X.std(ddof=1))]:
    if label.startswith('H1'):
        pn = norm.sf((129.5 - mu) / sd)
    elif label.startswith('F'):
        pn = norm.sf((4.5 - mu) / sd)
    else:
        pn = norm.cdf((-4.5 - mu) / sd) + norm.sf((4.5 - mu) / sd)
    normal_compare.append(dict(event=label, empirical_probability=emp, normal_approximation=pn, difference_normal_minus_empirical=pn - emp))
dump(pd.DataFrame(normal_compare), 'T10_empirical_vs_normal')
                                                               
v1 = an.BPXOSY1
v3 = an.BPXOSY3
x = an.X
mom = pd.DataFrame([{'quantity': 'E[BPXOSY1]', 'value': v1.mean(), 'unit': 'mmHg'}, {'quantity': 'E[BPXOSY3]', 'value': v3.mean(), 'unit': 'mmHg'}, {'quantity': 'E[X]', 'value': x.mean(), 'unit': 'mmHg'}, {'quantity': 'Var(BPXOSY1)', 'value': v1.var(ddof=1), 'unit': 'mmHg^2'}, {'quantity': 'Var(BPXOSY3)', 'value': v3.var(ddof=1), 'unit': 'mmHg^2'}, {'quantity': 'Var(X)', 'value': x.var(ddof=1), 'unit': 'mmHg^2'}, {'quantity': 'Cov(BPXOSY1,BPXOSY3)', 'value': v1.cov(v3), 'unit': 'mmHg^2'}, {'quantity': 'SD(X)', 'value': x.std(ddof=1), 'unit': 'mmHg'}])
dump(mom, 'T11_expectation_variance_covariance')
pairs = []
for a, b in [('BPXOSY1', 'BPXOSY3'), ('RIDAGEYR', 'X')]:
    pairs.append(dict(variable_1=a, variable_2=b, n=N, covariance=an[a].cov(an[b]), correlation=an[a].corr(an[b])))
dump(pd.DataFrame(pairs), 'T12_covariance_correlations')
                                                    
w = an.WTMEC2YR
weighted = float(np.average(an.H1.astype(float), weights=w))
weighted_rows = [dict(method='unweighted', numerator=int(an.H1.sum()), denominator=N, probability=float(an.H1.mean())), dict(method='weighted_WTMEC2YR', numerator=float(w[an.H1].sum()), denominator=float(w.sum()), probability=weighted)]
dump(pd.DataFrame(weighted_rows), 'T13_weighted_unweighted_H1')
plt.rcParams.update({'figure.dpi': 130, 'savefig.dpi': 200, 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False})
C1, C2, C3 = '#2b6cb0', '#dd6b20', '#718096'
fig, ax = plt.subplots(figsize=(6.4, 3.8))
vals = np.array([[int((~an.H1 & ~an.H3).sum()), int((~an.H1 & an.H3).sum())], [int((an.H1 & ~an.H3).sum()), int((an.H1 & an.H3).sum())]])
for i in range(2):
    bottom = 0
    for j, c in enumerate([C1, C2]):
        ax.bar(i, vals[i, j], bottom=bottom, color=c, label=['H3<130', 'H3>=130'][j] if i == 0 else None)
        bottom += vals[i, j]
ax.set_xticks([0, 1], ['H1<130', 'H1>=130'])
ax.set_ylabel('Participants')
ax.set_title('Joint distribution of first and third SBP thresholds')
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / 'fig1_H1_H3_joint.png')
plt.close(fig)
fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.hist(x, bins=np.arange(-54, 50, 2), density=True, alpha=0.7, color=C3,
        edgecolor='white', label='Empirical X')
xx = np.linspace(-55, 50, 500)
ax.plot(xx, norm.pdf(xx, x.mean(), x.std(ddof=1)), color=C2, lw=2,
        label='Normal with sample mean/SD')
ax.set(xlabel='X = SBP1 - SBP3 (mmHg)', ylabel='Density', title='Empirical distribution of within-person difference')
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / 'fig2_X_normal_overlay.png')
plt.close(fig)
fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.bar(y - 0.18, hyp, width=0.36, color=C1, label='Hypergeometric exact')
ax.bar(y + 0.18, bp, width=0.36, color=C2, label='Binomial approximation')
ax.set_xlim(-0.7, 14)
ax.set(xlabel='Number of D events in n=50 draws', ylabel='Probability', title='Hypergeometric vs binomial distribution')
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / 'fig3_hypergeom_binom.png')
plt.close(fig)
fig, ax = plt.subplots(figsize=(6.4, 3.8))
vals = [an.H1.mean(), weighted]
ax.bar(['Unweighted', 'Weighted'], vals, color=[C3, C1])
ax.set_ylim(0, max(vals) * 1.25)
ax.set_ylabel('Probability')
ax.set_title('P(BPXOSY1 >= 130): unweighted vs weighted')
for i, v in enumerate(vals):
    ax.text(i, v + 0.005, f'{v:.3f}', ha='center')
fig.tight_layout()
fig.savefig(FIG / 'fig4_weighted_unweighted.png')
plt.close(fig)
fig, ax = plt.subplots(figsize=(6.4, 3.8))
xx = np.arange(4)
emp = [an.H1.mean(), an.F.mean(), an.G.mean(), (an.X.abs() >= 10).mean()]
nor = [float(pd.DataFrame(normal_compare).iloc[i].normal_approximation) for i in range(4)]
ax.bar(xx - 0.18, emp, 0.36, color=C1, label='Empirical')
ax.bar(xx + 0.18, nor, 0.36, color=C2, label='Normal approximation')
ax.set_xticks(xx, ['H1', 'F', 'G', '|X|>=10'])
ax.set_ylabel('Probability')
ax.set_title('Empirical probabilities vs normal approximation')
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG / 'fig5_empirical_normal.png')
plt.close(fig)
stats = {'n': N, 'unique_SEQN': int(an.SEQN.nunique()), 'K_D': K, 'p_D': p, 'n_draws': n, 'seed': 20261110, 'simulation_repetitions': 2000, 'weighted_H1': weighted, 'unweighted_H1': float(an.H1.mean()), 'cov_SBP1_SBP3': float(v1.cov(v3)), 'corr_SBP1_SBP3': float(v1.corr(v3)), 'cov_age_X': float(an.RIDAGEYR.cov(x)), 'corr_age_X': float(an.RIDAGEYR.corr(x)), 'variance_identity_rhs': float(v1.var(ddof=1) + v3.var(ddof=1) - 2 * v1.cov(v3))}
(OUT / 'stats.json').write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(stats, indent=2, ensure_ascii=False))
