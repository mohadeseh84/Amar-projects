"""Build Persian phase2.pdf and standalone HTML report from phase2 outputs."""
from pathlib import Path
import pandas as pd, json, base64, subprocess, os, shutil
from weasyprint import HTML
ROOT=Path(__file__).resolve().parents[1]; TAB=ROOT/'reports'/'phase2'/'tables'; FIG=ROOT/'figures'/'phase2'; OUT=ROOT/'reports'/'phase2'
S=json.loads((OUT/'stats.json').read_text(encoding='utf-8'))
def read(n): return pd.read_csv(TAB/f'{n}.csv')
def fmt(v):
 if pd.isna(v): return '—'
 if isinstance(v,(int,float)):
  if abs(v-round(v)) < 1e-9 and abs(v) >= 10: return f'{int(round(v)):,}'
  return f'{v:,.3f}'
 return str(v)
HEADER_FA = {
    "event": "رویداد", "definition": "تعریف رویداد", "count": "تعداد",
    "n": "حجم نمونه", "probability": "احتمال تجربی", "percent": "درصد",
    "conditional_probability": "احتمال شرطی", "value": "مقدار",
    "group": "گروه",
    "A": "رویداد A", "B": "رویداد B", "P_A": "P(A)", "P_B": "P(B)",
    "P_A_times_P_B": "P(A) × P(B)", "P_joint": "P(A ∩ B)",
    "ratio_joint_to_product": "نسبت احتمال مشترک به حاصل‌ضرب",
    "expected_joint_count": "تعداد مورد انتظار", "observed_joint_count": "تعداد مشاهده‌شده",
    "difference": "اختلاف", "quantity": "کمیت", "method": "روش محاسبه",
    "mean": "میانگین", "variance": "واریانس", "sd": "انحراف معیار",
    "variable": "متغیر", "median": "میانه", "skewness": "چولگی",
    "excess_kurtosis": "کشیدگی اضافی", "q1": "چارک اول", "q3": "چارک سوم",
    "iqr": "دامنه بین‌چارکی", "min": "کمینه", "max": "بیشینه",
    "lower_fence": "حد پایین حصار", "upper_fence": "حد بالای حصار",
    "outside_iqr_fences": "خارج از حصار IQR", "abs_z_gt_3": "تعداد |z|>3",
    "abs_z_gt_4": "تعداد |z|>4", "within_1sd_pct": "درون ۱ SD (٪)",
    "within_2sd_pct": "درون ۲ SD (٪)", "within_3sd_pct": "درون ۳ SD (٪)",
    "empirical_probability": "احتمال تجربی", "normal_approximation": "تقریب نرمال",
    "difference_normal_minus_empirical": "اختلاف تقریب نرمال و تجربی",
    "unit": "واحد", "variable_1": "متغیر اول", "variable_2": "متغیر دوم",
    "covariance": "کوواریانس", "correlation": "همبستگی پیرسون",
    "numerator": "صورت", "denominator": "مخرج", "k": "تعداد رخداد D در نمونه",
    "hypergeometric_probability": "احتمال فوق‌هندسی", "binomial_probability": "احتمال دوجمله‌ای",
    "absolute_difference": "قدر مطلق اختلاف",
}
VALUE_FA = {
    "simulation_2000": "شبیه‌سازی (۲٬۰۰۰ تکرار)",
    "simulation_100000": "شبیه‌سازی (۱۰۰٬۰۰۰ تکرار)",
    "hypergeometric_exact": "توزیع فوق‌هندسی دقیق",
    "binomial_approximation": "تقریب دوجمله‌ای",
    "unweighted": "بدون وزن", "weighted_WTMEC2YR": "وزن‌دار با WTMEC2YR",
    "BPXOSY1": "قرائت اول فشار سیستولیک", "BPXOSY3": "قرائت سوم فشار سیستولیک",
    "RIDAGEYR": "سن (سال)", "X": "اختلاف قرائت اول و سوم (X)",
    "H1": "H1", "H3": "H3", "D": "D", "F": "F", "G": "G",
    "age60": "سن ۶۰ سال و بالاتر", "male": "مرد بودن",
    "P(H3|H1)": "P(H3|H1)", "P(H3|not H1)": "P(H3|¬H1)",
    "P(H1|H3)": "P(H1|H3)", "P(H1|not H3)": "P(H1|¬H3)",
    "P(D|H1)": "P(D|H1)", "P(F|age>=60)": "P(F|سن ۶۰+)",
    "P(F|age<60)": "P(F|سن زیر ۶۰)", "P(G|age>=60)": "P(G|سن ۶۰+)",
    "P(G|age<60)": "P(G|سن زیر ۶۰)",
    "H1: SBP1>=130": "H1: قرائت اول ≥ ۱۳۰", "F: X>=5": "F: اختلاف ≥ ۵",
    "G: |X|>=5": "G: قدر مطلق اختلاف ≥ ۵", "|X|>=10": "قدر مطلق اختلاف ≥ ۱۰",
    "mmHg": "میلی‌متر جیوه", "mmHg^2": "میلی‌متر جیوه مربع",
    "H1=0": "H1: کمتر از ۱۳۰", "H1=1": "H1: حداقل ۱۳۰",
    "H3=0": "H3: کمتر از ۱۳۰", "H3=1": "H3: حداقل ۱۳۰",
    "BPXOSY1 >= 130": "قرائت اول سیستولیک حداقل ۱۳۰",
    "BPXOSY3 >= 130": "قرائت سوم سیستولیک حداقل ۱۳۰",
    "BPXOSY1 >=130 and BPXOSY3 <130": "قرائت اول حداقل ۱۳۰ و قرائت سوم کمتر از ۱۳۰",
    "X >= 5 mmHg": "اختلاف قرائت اول و سوم حداقل ۵ میلی‌متر جیوه",
    "|X| >= 5 mmHg": "قدر مطلق اختلاف حداقل ۵ میلی‌متر جیوه",
    "Age >= 60": "سن حداقل ۶۰ سال",
}

def display_cell(value):
    if pd.isna(value):
        return "—"
    if isinstance(value, str):
        if value in VALUE_FA:
            value = VALUE_FA[value]
        elif value.startswith("BPXOSY") or value.startswith("RIDAGEYR") or value.startswith("P("):
            return f'<span class="ltr">{value}</span>'
        elif any(ch.isascii() and ch.isalpha() for ch in value) and not any("\u0600" <= ch <= "\u06ff" for ch in value):
            return f'<span class="ltr">{value}</span>'
        return str(value)
    return fmt(value)

def table(df, headers=None, limit=None):
    if limit:
        df = df.head(limit)
    headers = headers or list(df.columns)
    translated_headers = [HEADER_FA.get(str(h), str(h)) for h in headers]
    head = "".join(f"<th>{h}</th>" for h in translated_headers)
    rows = "".join(
        "<tr>" + "".join(f"<td>{display_cell(v)}</td>" for v in row) + "</tr>"
        for row in df.itertuples(index=False, name=None)
    )
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
def img(n,caption):
 b=base64.b64encode((FIG/n).read_bytes()).decode()
 return f'<figure><img src="data:image/png;base64,{b}"><figcaption>{caption}</figcaption></figure>'
E=read('T02_event_probabilities'); C=read('T03_conditional_probabilities'); SG=read('T04_event_by_subgroup'); IND=read('T05_independence_checks'); BAY=read('T06_bayes'); SIM=read('T07_binomial_hypergeometric_summary'); NORM=read('T09_normality_diagnostics'); NC=read('T10_empirical_vs_normal'); MOM=read('T11_expectation_variance_covariance'); COV=read('T12_covariance_correlations'); WT=read('T13_weighted_unweighted_H1')
                              
E2=E[['event','definition','count','probability']].copy(); E2.columns=['رویداد','تعریف','تعداد','احتمال تجربی']
C2=C.copy()
C2['conditional_probability']=C2['conditional_probability'].map({
    'P(H3|H1)': 'احتمال قرائت سوم حداقل ۱۳۰، به شرط قرائت اول حداقل ۱۳۰',
    'P(H3|not H1)': 'احتمال قرائت سوم حداقل ۱۳۰، به شرط قرائت اول کمتر از ۱۳۰',
    'P(H1|H3)': 'احتمال قرائت اول حداقل ۱۳۰، به شرط قرائت سوم حداقل ۱۳۰',
    'P(H1|not H3)': 'احتمال قرائت اول حداقل ۱۳۰، به شرط قرائت سوم کمتر از ۱۳۰',
    'P(D|H1)': 'احتمال رویداد D، به شرط H1',
    'P(F|age>=60)': 'احتمال رویداد F در افراد ۶۰ سال و بالاتر',
    'P(F|age<60)': 'احتمال رویداد F در افراد زیر ۶۰ سال',
    'P(G|age>=60)': 'احتمال رویداد G در افراد ۶۰ سال و بالاتر',
    'P(G|age<60)': 'احتمال رویداد G در افراد زیر ۶۰ سال',
})
C2.columns=['احتمال شرطی','مقدار']
SG2=SG.copy(); SG2.columns=['گروه','رویداد','n','تعداد','احتمال']
IND2=IND[['A','B','P_A_times_P_B','P_joint','ratio_joint_to_product','expected_joint_count','observed_joint_count']].copy(); IND2.columns=['A','B','P(A)P(B)','P(A∩B)','نسبت مشترک به حاصل‌ضرب','مورد انتظار','مشاهده‌شده']
SIM2=SIM.copy(); SIM2.columns=['روش','میانگین','واریانس','انحراف معیار']
NORM2=NORM[['variable','mean','median','sd','skewness','excess_kurtosis','outside_iqr_fences','abs_z_gt_3','abs_z_gt_4','within_1sd_pct','within_2sd_pct','within_3sd_pct']].copy(); NORM2.columns=['متغیر','میانگین','میانه','SD','چولگی','کشیدگی اضافی','بیرون حصار IQR','|z|>3','|z|>4','درون ۱SD٪','درون ۲SD٪','درون ۳SD٪']
NC2=NC.copy(); NC2.columns=['رویداد','تجربی','تقریب نرمال','اختلاف']
MOM2=MOM.copy(); MOM2.columns=['کمیت','مقدار','واحد']
COV2=COV.copy(); COV2.columns=['متغیر اول','متغیر دوم','n','کوواریانس','همبستگی پیرسون']
WT2=WT.copy(); WT2['probability']=WT2['probability'].map(lambda x: f'{x:.4f}'); WT2.columns=['روش','صورت','مخرج','احتمال']
html=f'''<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 18mm 15mm; }}
body {{ font-family: 'DejaVu Sans', sans-serif; direction: rtl; font-size: 10.2pt; line-height: 1.85; color:#1a202c; }}
h1 {{ font-size: 20pt; margin: 0 0 4px; color:#1a365d; }}
h2 {{ font-size: 13.5pt; color:#2b6cb0; border-bottom:2px solid #bee3f8; padding-bottom:3px; margin-top:22px; page-break-after: avoid; }}
h3 {{ font-size: 11.2pt; color:#2c5282; margin-bottom:2px; page-break-after: avoid; }}
table {{ border-collapse: collapse; width:100%; margin:8px 0 12px; font-size: 8.6pt; direction: rtl; page-break-inside: avoid; }}
th {{ background:#2b6cb0; color:white; padding:4px 5px; white-space: pre-line; }}
td {{ border:1px solid #cbd5e0; padding:3px 5px; text-align:center; }}
tr:nth-child(even) td {{ background:#f7fafc; }}
td:first-child {{ text-align:right; }}
.tbl {{ overflow:visible; margin:3mm 0 5mm; }}
figure {{ text-align:center; page-break-inside:avoid; margin:10px 0; }}
figure img {{ width:86%; }}
figcaption {{ font-size:9pt; color:#4a5568; }}
.ltr {{ direction:ltr; unicode-bidi:embed; }}
.small {{ font-size:8.5pt; color:#667085; }}
.equation {{ direction:ltr; text-align:center; font-family:'DejaVu Sans',sans-serif; margin:4mm 0; background:#edf2f7; padding:3mm; }}
.callout {{ background:#ebf8ff; border-right:4px solid #3182ce; padding:6px 12px; margin:8px 0; page-break-inside:avoid; }}
.warn {{ background:#fffaf0; border-right:4px solid #dd6b20; padding:6px 12px; margin:8px 0; page-break-inside:avoid; }}
.cover {{ text-align:center; padding:120px 0 30px; page-break-after:always; }}
.cover p {{ margin:4px; }}
.eyebrow {{ font-size:11pt; color:#4a5568; }}
.cover h1 {{ font-size:20pt; color:#1a365d; margin:8px 0 4px; }}
.sub {{ font-size:14pt; color:#1a202c; }}
.meta {{ margin:10mm auto 0; line-height:2.0; color:#4a5568; }}
</style></head><body>
<div class="cover">
<p class="eyebrow">پروژه‌ی درس آمار — فاز دوم</p>
<h1>فاز ۲: احتمال و توزیع‌های احتمالی</h1>
<p class="sub">مقایسه‌ی قرائت اول و سوم فشارخون سیستولیک</p>
<p>تحلیل احتمال‌ها و توزیع‌های مرتبط با اختلاف درون‌فردی فشارخون در بزرگسالان</p>
<p>NHANES 2021–2023 (چرخه‌ی L) — مسیر الف</p>
<p class="meta">نام : محدثه رضوی &nbsp;&nbsp; شماره‌ی دانشجویی: 403170174</p>
</div>
<h2>خلاصه اجرایی</h2><p>این فاز، احتمال رخدادهای مرتبط با فشارخون سیستولیک، احتمال‌های شرطی، استقلال و قاعده بیز، تقریب دوجمله‌ای، مقایسه توزیع تجربی با نرمال، امید ریاضی، واریانس و کوواریانس را بررسی می‌کند. تحلیل روی همان نمونه فردمحور فاز اول انجام شده است؛ هر ردیف یک شرکت‌کننده یکتا است و هر سه قرائت سیستولیک او معتبرند.</p>
<div class="callout"><b>نتایج کلیدی:</b> احتمال تجربی فشار سیستولیک قرائت اول حداقل ۱۳۰ برابر ۳۱٫۳٪ است؛ احتمال اینکه قرائت اول حداقل ۵ mmHg بیشتر از قرائت سوم باشد ۲۳٫۲۵٪ است. همبستگی قرائت اول و سوم قوی (۰٫۹۲۷) و همبستگی سن با اختلاف دو قرائت بسیار ضعیف (۰٫۰۴۷) است. تقریب نرمال برای دنباله‌های مورد بررسی احتمال‌ها را بیش‌برآورد می‌کند.</div>
<h2>۱. داده‌ها، جامعه تحلیلی و تعریف متغیرها</h2><p>داده‌های <span class="ltr">DEMO_L</span>، <span class="ltr">BPXO_L</span> و <span class="ltr">BMX_L</span> با شناسه <span class="ltr">SEQN</span> ادغام شدند. معیارهای ورود همان معیارهای فاز اول است: سن حداقل ۲۰ سال، معاینه‌شده در مرکز <span class="ltr">MEC</span> (کد <span class="ltr">RIDSTATR=2</span>) و داشتن هر سه قرائت سیستولیک معتبر. تعداد رکوردهای نهایی {S['n']:,} و تعداد شناسه‌های یکتا نیز {S['unique_SEQN']:,} است.</p><p>متغیر کلیدی اختلاف درون‌فردی به صورت <span class="ltr">X = BPXOSY1 − BPXOSY3</span> تعریف شده است. همچنین <span class="ltr">H1: BPXOSY1≥130</span>، <span class="ltr">H3: BPXOSY3≥130</span>، رویداد <span class="ltr">D=H1∩¬H3</span> و رویداد <span class="ltr">F: X≥5</span> تعریف شدند. رویداد <span class="ltr">G: |X|≥5</span> اختلاف بزرگ در هر دو جهت را پوشش می‌دهد.</p>
<h2>۲. تسک‌های ۱ تا ۳: احتمال‌های تجربی و شرطی</h2><p>احتمال تجربی هر رویداد از تقسیم تعداد افراد واجد رویداد بر کل نمونه به دست آمده است. جدول زیر فراوانی و احتمال‌های اصلی را نشان می‌دهد.</p>{table(E2)}
<h3>۲-۱. جدول مشترک H1 و H3</h3><p>از ۵٬۸۴۲ نفر، ۱٬۵۰۱ نفر در هر دو قرائت حداقل ۱۳۰، ۳٬۷۷۸ نفر در هر دو کمتر از ۱۳۰، ۲۳۸ نفر فقط در قرائت سوم و ۳۲۵ نفر فقط در قرائت اول در سطح حداقل ۱۳۰ قرار گرفته‌اند.</p>{table(pd.DataFrame([['کمتر از ۱۳۰','کمتر از ۱۳۰',3778],['کمتر از ۱۳۰','حداقل ۱۳۰',238],['حداقل ۱۳۰','کمتر از ۱۳۰',325],['حداقل ۱۳۰','حداقل ۱۳۰',1501]],columns=['وضعیت قرائت اول','وضعیت قرائت سوم','count']))}{img('fig1_H1_H3_joint.png','شکل ۱. توزیع مشترک وضعیت آستانه ۱۳۰ در قرائت اول و سوم.')}
<h3>۲-۲. احتمال‌های شرطی</h3>{table(C2)}<p>برای نمونه، احتمال قرارگرفتن قرائت سوم در سطح حداقل ۱۳۰ در میان افرادی که قرائت اولشان حداقل ۱۳۰ است، حدود ۰٫۸۲۲ است؛ در مقابل این احتمال در میان افراد با قرائت اول کمتر از ۱۳۰ حدود ۰٫۰۵۹ است. این وابستگی با تکراری بودن اندازه‌گیری‌ها در یک فرد سازگار است.</p>
<h3>۲-۳. تفکیک بر حسب جنس و سن</h3>{table(SG2)}<p>احتمال H1 با افزایش گروه سنی بیشتر است (حدود ۱۰٫۴٪ در ۲۰–۳۹ سال، ۲۶٫۸٪ در ۴۰–۵۹ سال و ۴۵٫۶٪ در ۶۰ سال به بالا). احتمال F نیز از ۱۶٫۱٪ در گروه ۲۰–۳۹ به ۲۷٫۸٪ در گروه ۶۰+ می‌رسد. این مقایسه‌ها توصیفی‌اند و به‌تنهایی رابطه علّی یا معناداری آماری را نشان نمی‌دهند.</p>
<h2>۳. تسک ۴: بررسی استقلال رویدادها</h2><p>برای دو رویداد مستقل باید <span class="ltr">P(A∩B)=P(A)P(B)</span> برقرار باشد. نسبت احتمال مشترک مشاهده‌شده به حاصل‌ضرب احتمال‌های حاشیه‌ای، میزان فاصله از استقلال را به‌صورت توصیفی نشان می‌دهد.</p>{table(IND2)}<p>وابستگی H1 و H3 مثبت و قوی است: احتمال مشترک ۰٫۲۵۷ در برابر حاصل‌ضرب ۰٫۰۹۳ است (نسبت حدود ۲٫۷۶). وابستگی F با سن ۶۰+ نیز مثبت اما محدودتر است (نسبت ۱٫۲۰). زوج F و مرد بودن به استقلال نزدیک‌تر است (نسبت ۱٫۰۶)، اما این نزدیکی اثبات استقلال نیست.</p>
<h2>۴. تسک ۹: قاعده بیز و قانون احتمال کل</h2><p>با درنظرگرفتن H1 و H3، احتمال حاشیه‌ای H1 را می‌توان از قانون احتمال کل بازسازی کرد:</p><div class="equation">P(H1)=P(H1|H3)P(H3)+P(H1|¬H3)P(¬H3)</div><p>مقادیر محاسبه‌شده برای احتمال‌های شرطی و حاشیه‌ای در جدول آمده‌اند.</p>{table(BAY)}<p>همچنین احتمال اینکه فردی که رویداد F را دارد در گروه سنی ۶۰+ باشد، حدود ۰٫۵۴۸ است؛ این مقدار از سهم پایه گروه ۶۰+ در کل نمونه (۰٫۴۵۸) بیشتر است. قرائت سوم در این پروژه «مرجع مقایسه» است، نه حقیقت طلایی یا تشخیص قطعی؛ بنابراین D را نباید خطای طبقه‌بندی نامید.</p>
<h2>۵. الزام الف۲: مدل دوجمله‌ای و مقایسه با فوق‌هندسی</h2><p>رویداد D دارای K={S['K_D']:,} مورد در جامعه محدود N={S['n']:,} نفر است؛ بنابراین p=K/N={S['p_D']:.5f}. اندازه نمونه n=۵۰ انتخاب شد تا مقایسه دو مدل در یک نمونه کوچک و قابل‌تفسیر انجام شود. نسبت n/N حدود ۰٫۸۶٪ است؛ در این اندازه، اثر محدود بودن جامعه اندک است و تقریب دوجمله‌ای به توزیع فوق‌هندسی نزدیک می‌ماند. چون انتخاب درون هر نمونه بدون جایگذاری است، مدل دقیق شمارش D فوق‌هندسی است و مدل دوجمله‌ای تقریب آن خواهد بود.</p><div class="equation">Y ~ Hypergeometric(N={S['n']}, K={S['K_D']}, n=50) ≈ Binomial(n=50, p={S['p_D']:.5f})</div>{table(SIM2)}<p>ضریب تصحیح جامعه محدود برابر <span class="ltr">(N−n)/(N−1)</span> و حدود ۰٫۹۹۱۶ است؛ بنابراین واریانس فوق‌هندسی اندکی کمتر از واریانس دوجمله‌ای است. نسبت نمونه به جامعه فقط ۰٫۸۶٪ است و تقریب دوجمله‌ای در این مسئله مناسب است. شبیه‌سازی اصلی با ۲٬۰۰۰ تکرار و بذر ثابت ۲۰۲۶۱۱۱۰ انجام شد؛ شبیه‌سازی ۱۰۰٬۰۰۰ تکراری صرفاً برای بررسی پایداری مونت‌کارلو افزوده شده است.</p>{img('fig3_hypergeom_binom.png','شکل ۲. مقایسه جرم احتمال توزیع فوق‌هندسی دقیق و تقریب دوجمله‌ای.')}
<h2>۶. تسک ۶ و الزام الف۳: بررسی تقریب نرمال</h2><p>برای قرائت اول و اختلاف X، میانگین، انحراف معیار، چولگی، کشیدگی اضافی، چارک‌ها و شمار نقاط بیرون حصارهای ۱٫۵×IQR محاسبه شدند. درصد مقادیر در فاصله یک، دو و سه انحراف معیار نیز با قاعده تجربی نرمال مقایسه شد.</p>{table(NORM2)}<p>توزیع BPXOSY1 راست‌چوله است (چولگی حدود ۰٫۹۳). توزیع X از نظر چولگی تقریباً متقارن است، اما کشیدگی اضافی بالا (حدود ۳٫۴۳) و دامنه مقادیر حدی نشان می‌دهد دم‌ها سنگین‌تر از نرمال‌اند. درصدهای درون یک SD برای هر دو متغیر از ۶۸٫۳٪ قاعده نرمال بیشتر است و در سه SD نیز پوشش کمی کمتر از ۹۹٫۷٪ است.</p>{img('fig2_X_normal_overlay.png','شکل ۳. چگالی تجربی اختلاف X در کنار منحنی نرمال با میانگین و انحراف معیار نمونه.')}
<h3>۶-۱. مقایسه احتمال تجربی با تقریب نرمال</h3>{table(NC2)}<p>برای رویدادهای گسسته با آستانه صحیح، تصحیح پیوستگی به کار رفته است؛ برای مثال آستانه H1 به ۱۲۹٫۵ و آستانه F به ۴٫۵ تبدیل شده است. تقریب نرمال برای رویدادهای بررسی‌شده احتمال‌ها را بیش‌برآورد می‌کند. بنابراین تقریب نرمال برای این دنباله‌ها مناسب نیست و توزیع تجربی باید مبنای اصلی گزارش احتمال باشد.</p>{img('fig5_empirical_normal.png','شکل ۴. احتمال‌های تجربی و تقریب نرمال با تصحیح پیوستگی.')}
<h2>۷. تسک ۷: امید ریاضی، واریانس و کوواریانس</h2>{table(MOM2)}<p>با استفاده از هویت واریانس اختلاف:</p><div class="equation">Var(X)=Var(Y1)+Var(Y3)−2Cov(Y1,Y3)</div><p>مقدار سمت راست برابر {S['variance_identity_rhs']:.3f} و با واریانس مستقیم X برابر {float(MOM.loc[MOM.quantity=='Var(X)','value'].iloc[0]):.3f} است؛ اختلاف فقط ناشی از گرد کردن نمایش است. SD اختلاف حدود ۷٫۰۷ mmHg است؛ یعنی پراکندگی X حول میانگین کوچک ۰٫۳۲، نه اینکه اختلاف هر فرد الزاماً ۷ واحد باشد.</p>
<h2>۸. تسک ۸: کوواریانس و همبستگی</h2>{table(COV2)}<p>کوواریانس قرائت اول و سوم مثبت و بزرگ است و همبستگی ۰٫۹۲۷ رابطه خطی مثبت قوی را نشان می‌دهد. کوواریانس سن و X مثبت است، اما همبستگی ۰٫۰۴۷ بسیار ضعیف است؛ این نتیجه به معنای رابطه علّی یا تفاوت معنادار آماری نیست. سن در NHANES برای افراد ۸۰ سال به بالا top-code شده است؛ بنابراین مقدار ۸۰ الزاماً سن دقیق ۸۰ نیست.</p>
<h2>۹. الزام الف۴: احتمال وزن‌دار در برابر بدون وزن</h2><p>رویداد H1 انتخاب شده است. احتمال خام، نسبت تعداد افراد H1 به کل نمونه است. احتمال وزن‌دار با وزن معاینه MEC یعنی <span class="ltr">WTMEC2YR</span> محاسبه شده است.</p>{table(WT2)}<p>برآورد وزن‌دار ۴٫۳۰ واحد درصد کمتر از نسبت خام است (۲۶٫۹۶٪ در برابر ۳۱٫۳٪). وزن‌ها سهم‌های متفاوت افراد در نمونه‌گیری را بازتاب می‌دهند.</p>{img('fig4_weighted_unweighted.png','شکل ۵. مقایسه احتمال H1 بدون وزن و با وزن WTMEC2YR.')}
<div class="warn"><b>محدودیت مهم:</b> وزن‌دار کردن نسبت در زیرنمونه کامل‌موارد ۵٬۸۴۲ نفری، به‌تنهایی اثر انتخاب‌شدن در این زیرنمونه را رفع نمی‌کند؛ بنابراین ۲۶٫۹۶٪ فقط یک برآورد توصیفی وزن‌دار در همین زیرنمونه است، نه برآورد رسمی و قطعی شیوع ملی. در این گزارش خطای معیار، فاصله اطمینان یا آزمون فرض طراحیمحور محاسبه نشده است. برای استنباط جمعیتی باید وزن، طبقه‌ها (<span class="ltr">SDMVSTRA</span>)، خوشه‌ها (<span class="ltr">SDMVPSU</span>) و تحلیل زیرجمعیت هم‌زمان لحاظ شوند.</div>
<h2>۱۰. جمع‌بندی و محدودیت‌ها</h2><ul><li>H1 و H3 به‌شدت وابسته‌اند؛ دو قرائت از یک فرد مستقل نیستند.</li><li>رویداد D در ۵٫۵۶٪ نمونه رخ داده است؛ این به معنی تغییر وضعیت بین دو قرائت است، نه اثبات خطای اندازه‌گیری یا تشخیص.</li><li>تقریب دوجمله‌ای برای شمارش D در نمونه ۵۰تایی به دلیل کوچک بودن نسبت نمونه به جامعه، تقریب مناسبی برای فوق‌هندسی است.</li><li>توزیع اختلاف X متقارن‌تر از قرائت اول است، اما دم‌های سنگین دارد؛ تقریب نرمال برای احتمال‌های دنباله‌ای گزارش‌شده مناسب نیست.</li><li>تمام احتمال‌های خام و بیشتر محاسبات این فاز توصیفی و بدون وزن هستند؛ تعمیم به جمعیت آمریکا نیازمند تحلیل طرح‌محور NHANES است.</li><li>داده‌های خام NHANES در ZIP تحویل قرار داده نشده‌اند؛ دستور دریافت و اجرای مجدد در README ثبت شده است.</li></ul>
<h2>۱۱. بازتولیدپذیری و ساختار خروجی</h2><p>کد <span class="ltr">src/phase2.py</span> داده‌ها را از سه فایل XPT می‌خواند، نمونه تحلیلی را بازسازی می‌کند، کنترل ۵٬۸۴۲ شناسه یکتا را انجام می‌دهد و جدول‌ها، آمارها و شکل‌ها را تولید می‌کند. کد <span class="ltr">src/make_phase2_report.py</span> گزارش PDF و HTML را می‌سازد. جزئیات اجرای پروژه و منابع داده در README آمده است.</p><p class="small">منبع داده: CDC/NCHS, NHANES 2021–2023, چرخه L. این گزارش تحلیل توصیفی/احتمالاتی بر نمونه تحلیلی تعریف‌شده را ارائه می‌کند و جایگزین برآورد رسمی طراحی‌محور CDC نیست.</p>
</body></html>'''
html_path=OUT/'phase2.html'; html_path.write_text(html,encoding='utf-8')
pdf=OUT/'phase2.pdf'
HTML(filename=str(html_path)).write_pdf(str(pdf))
print(pdf, pdf.stat().st_size)
