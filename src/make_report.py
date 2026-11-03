"""Builds reports/phase1.pdf (Persian, RTL) from tables/figures produced by phase1.py.
Run after phase1.py:  python src/make_report.py   (needs Google Chrome/Chromium; set CHROME_PATH if it is not found automatically)"""
import base64, json, os, shutil, subprocess
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "reports" / "phase1" / "tables"
FIG = ROOT / "figures" / "phase1"
S = json.loads((ROOT / "reports" / "phase1" / "stats.json").read_text())
T = {n: pd.read_csv(TAB / f"{n}.csv") for n in
     ["T1_flow", "T3_frequencies", "T4_numeric_summary", "T5_raw_vs_weighted", "T6_diff_by_sex_age",
      "T6b_diff_by_bmi", "T7_missing_bp"]}

FA = {"Male": "مرد", "Female": "زن", "Sex": "جنس", "Age group": "گروه سنی", "Race/ethnicity": "نژاد/قومیت",
      "BMI category": "دسته‌ی BMI", "Cuff size (coded)": "اندازه‌ی کاف (کد)", "Arm used": "بازوی اندازه‌گیری",
      "Right": "راست", "Left": "چپ", "Missing": "گمشده", "All adults": "کل بزرگسالان",
      "Mexican American": "مکزیکی‌آمریکایی", "Other Hispanic": "سایر هیسپانیک", "NH White": "سفیدپوست غیرهیسپانیک",
      "NH Black": "سیاه‌پوست غیرهیسپانیک", "NH Asian": "آسیایی غیرهیسپانیک", "Other/Multi": "سایر/چندنژادی",
      "Age": "سن", "Sex: Male": "جنس: مرد", "Sex: Female": "جنس: زن",
      "Age: 20-39": "سن ۲۰–۳۹", "Age: 40-59": "سن ۴۰–۵۹", "Age: 60+": "سن ۶۰+"}
fa = lambda x: FA.get(x, x)
f = lambda v, d=1: f"{v:,.{d}f}"


def img(name):
    b = base64.b64encode((FIG / name).read_bytes()).decode()
    return f"data:image/png;base64,{b}"


def table(df, headers, fmts=None, cls=""):
    fmts = fmts or {}
    h = "".join(f"<th>{x}</th>" for x in headers)
    rows = ""
    for _, r in df.iterrows():
        cells = ""
        for c, v in zip(df.columns, r):
            if c in fmts and isinstance(v, (int, float)):
                v = fmts[c](v)
            v = str(v)
            if not any("\u0600" <= ch <= "\u06ff" for ch in v) and "<" not in v:
                v = f'<bdi dir="ltr">{v}</bdi>'
            cells += f"<td>{v}</td>"
        rows += f"<tr>{cells}</tr>"
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{rows}</tbody></table>'


t1 = T["T1_flow"]
flow_fa = {"DEMO_L: all records": "کل رکوردهای DEMO_L", "BPXO_L: all records": "کل رکوردهای BPXO_L",
           "BMX_L: all records": "کل رکوردهای BMX_L", "Age >= 20 (interviewed)": "سن ≥ ۲۰ سال (مصاحبه‌شده)",
           "... and examined in MEC (RIDSTATR=2)": "… و معاینه‌شده در MEC",
           "... after merge with BPXO_L (rows)": "پس از ادغام با BPXO_L (تعداد ردیف)",
           "... after merge with BMX_L (rows)": "پس از ادغام با BMX_L (تعداد ردیف)",
           "... with >= 1 systolic reading": "… با حداقل یک قرائت سیستولیک",
           "... with all 3 systolic readings (ANALYTIC)": "<b>… با هر سه قرائت سیستولیک (جمعیت تحلیلی)</b>"}
t1 = t1.assign(step=t1.step.map(flow_fa))
tab_flow = table(t1, ["مرحله", "تعداد افراد/ردیف"], {"n": lambda v: f"{int(v):,}"})

t3 = T["T3_frequencies"].copy()
t3["variable"] = t3.variable.map(fa); t3["level"] = t3.level.map(fa).str.replace("<18.5", '<bdi dir="ltr">&lt;18.5</bdi>', regex=False)
tab_freq = table(t3, ["متغیر", "سطح", "تعداد", "درصد (بدون وزن)", "درصد (وزن‌دار)"],
                 {"n": lambda v: f"{int(v):,}", "pct_unweighted": f, "pct_weighted": f})

t4 = T["T4_numeric_summary"].copy()
v_fa = {"Age (years)": "سن (سال)", "Systolic reading 1": "سیستولیک قرائت ۱", "Systolic reading 2": "سیستولیک قرائت ۲",
        "Systolic reading 3": "سیستولیک قرائت ۳", "Diastolic reading 1": "دیاستولیک قرائت ۱",
        "Diastolic reading 3": "دیاستولیک قرائت ۳", "Systolic: reading1 - reading3": "<b>سیستولیک: قرائت۱ − قرائت۳</b>",
        "Systolic: reading1 - reading2": "سیستولیک: قرائت۱ − قرائت۲", "Systolic: reading2 - reading3": "سیستولیک: قرائت۲ − قرائت۳",
        "Diastolic: reading1 - reading3": "دیاستولیک: قرائت۱ − قرائت۳", "BMI (kg/m2)": "BMI (kg/m²)"}
t4["variable"] = t4.variable.map(v_fa)
tab_num = table(t4, ["متغیر", "n", "میانگین", "میانه", "SD", "Q1", "Q3", "IQR", "min", "max"],
                {"n": lambda v: f"{int(v):,}", **{c: f for c in ["mean", "median", "sd", "q1", "q3", "iqr", "min", "max"]}})

t5 = T["T5_raw_vs_weighted"].copy(); t5["group"] = t5.group.map(fa)
tab_rw = table(t5, ["گروه", "n", "میانگین SBP1\nبدون وزن", "میانگین SBP1\nوزن‌دار", "میانگین (۱−۳)\nبدون وزن",
                    "میانگین (۱−۳)\nوزن‌دار", "٪ قرائت۱>۳\nبدون وزن", "٪ قرائت۱>۳\nوزن‌دار"],
               {"n": lambda v: f"{int(v):,}", **{c: (lambda v: f"{v:.2f}") for c in t5.columns[2:6]},
                "pct_first_higher_raw": f, "pct_first_higher_wtd": f})

t6 = T["T6_diff_by_sex_age"].copy(); t6["sex"] = t6.sex.map(fa)
tab_sa = table(t6, ["جنس", "گروه سنی", "n", "میانگین (۱−۳)", "میانه", "SD", "میانگین وزن‌دار", "٪ قرائت۱>۳"],
               {"n": lambda v: f"{int(v):,}", "mean_diff13": lambda v: f"{v:.2f}", "median_diff13": f,
                "sd_diff13": f, "mean_diff13_wtd": lambda v: f"{v:.2f}", "pct_first_higher": f})
t6b = T["T6b_diff_by_bmi"].copy(); t6b["bmi_group"] = t6b.bmi_group.str.replace("<18.5", '<bdi dir="ltr">&lt;18.5</bdi>', regex=False)
tab_bmi = table(t6b, ["دسته‌ی BMI", "n", "میانگین (۱−۳)", "میانه", "SD", "میانگین وزن‌دار"],
                {"n": lambda v: f"{int(v):,}", "mean_diff13": lambda v: f"{v:.2f}", "median_diff13": f,
                 "sd_diff13": f, "mean_diff13_wtd": lambda v: f"{v:.2f}"})

t7 = T["T7_missing_bp"].copy(); t7["variable"] = t7.variable.map(fa); t7["level"] = t7.level.map(fa)
tab_miss = table(t7, ["متغیر", "سطح", "معاینه‌شدگان", "٪ دارای ۳ قرائت", "٪ دارای ۱–۲ قرائت", "٪ بدون فشارخون"],
                 {"n_examined": lambda v: f"{int(v):,}", "pct_3_readings": f, "pct_1_2_readings": f, "pct_no_bp": f})

m = S["miss_other"]
n_exam = int(T["T1_flow"].n[4]); n_any = int(T["T1_flow"].n[7]); n_an = S["n_analytic"]
n_nobp = n_exam - n_any; n_part = n_any - n_an
a = T["T4_numeric_summary"].set_index("variable")
d13 = a.loc["Systolic: reading1 - reading3"]
dia = a.loc["Diastolic: reading1 - reading3"]
rw = T["T5_raw_vs_weighted"].set_index("group")
fq = T["T3_frequencies"]
p60u = fq[(fq.level == "60+")].pct_unweighted.iloc[0]; p60w = fq[(fq.level == "60+")].pct_weighted.iloc[0]
p2039u = fq[(fq.level == "20-39")].pct_unweighted.iloc[0]; p2039w = fq[(fq.level == "20-39")].pct_weighted.iloc[0]

decisions = pd.DataFrame([
    ("نبود هر سه قرائت فشارخون", f"{n_nobp} نفر بدون هیچ قرائت، {n_part} نفر با ۱–۲ قرائت",
     "از جمعیت تحلیلی اصلی کنار گذاشته می‌شوند (قرائت اول و سوم هر دو لازم است). افراد با ۲ قرائت در فاز ۵ برای حساسیت‌سنجی قابل استفاده‌اند."),
    ("مقادیر غیرممکن", f"دیاستولیک ≥ سیستولیک: {m['any diastolic >= systolic (3 readings)']} مورد؛ مقادیر منفی/صفر: ۰",
     "اقدامی لازم نیست."),
    ("اختلاف‌های بزرگ بین قرائت‌ها", f"|قرائت۱ − قرائت۳| ≥ ۳۰ mmHg: {m['|reading1-reading3| >= 30 mmHg']} نفر",
     "حذف نمی‌شوند؛ از نظر فیزیولوژیک ممکن‌اند (حرکت بازو، اضطراب، خطای دستگاه). در فاز ۵ حساسیت‌سنجی می‌شوند."),
    ("سه قرائت کاملاً یکسان", f"{m['exactly identical 3 systolic readings']} نفر",
     "حفظ می‌شوند؛ مقدار یکسان نشانه‌ی خطا نیست."),
    ("BMI گمشده", f"{m['BMI missing among analytic']} نفر از جمعیت تحلیلی",
     "حذف نمی‌شوند (BMI در سؤال اصلی نیست)؛ فقط در جدول‌های BMI «گمشده» محسوب می‌شوند."),
    ("سن ۸۰ (کدگذاری ‌۸۰+)", f"{m['age=80 (top-coded 80+) among analytic']} نفر",
     "در گروه ۶۰+ می‌مانند؛ سن عددی برای این افراد دقیق نیست."),
    ("وزن گمشده یا صفر", f"{m['weight missing/zero among analytic']} نفر", "اقدامی لازم نیست."),
    ("رکورد تکراری (SEQN)", "۰ در هر سه فایل", "هر فرد دقیقاً یک ردیف دارد؛ مشکل مراجعه‌ی تکراری وجود ندارد."),
], columns=["مسئله", "یافته", "تصمیم و دلیل"])
tab_dec = table(decisions, list(decisions.columns))

vars_tab = pd.DataFrame([
    ("SEQN", "شناسه‌ی شرکت‌کننده", "شناسه (کلید ادغام)", "—"),
    ("BPXOSY1/2/3", "فشارخون سیستولیک قرائت ۱ تا ۳ (mmHg)", "کمی پیوسته (در عمل عدد صحیح)", "پاسخ (در قالب اختلاف)"),
    ("BPXODI1/2/3", "فشارخون دیاستولیک قرائت ۱ تا ۳ (mmHg)", "کمی پیوسته (در عمل عدد صحیح)", "پاسخ فرعی"),
    ("d13 = SY1 − SY3", "اختلاف درون‌فردی قرائت اول و سوم (mmHg)", "کمی پیوسته", "<b>پاسخ اصلی</b>"),
    ("first_higher", "آیا قرائت اول بزرگ‌تر از سوم است؟", "دودویی", "پاسخ توصیفی (فاز ۲)"),
    ("RIAGENDR", "جنس", "اسمی دوحالته", "متغیر گروه‌بندی"),
    ("RIDAGEYR → گروه سنی", "سن به سال؛ گروه‌ها: ۲۰–۳۹، ۴۰–۵۹، ۶۰+", "کمی گسسته → ترتیبی", "متغیر گروه‌بندی"),
    ("RIDRETH3", "نژاد/قومیت", "اسمی", "توصیفی/تعدیل"),
    ("BMXBMI → دسته‌ی BMI", "شاخص توده بدنی؛ دسته‌ها: &lt;۱۸٫۵، ۱۸٫۵–۲۴٫۹، ۲۵–۲۹٫۹، ≥۳۰", "کمی پیوسته → ترتیبی", "توصیفی/تعدیل"),
    ("BPAOCSZ", "اندازه‌ی کاف (کد؛ بزرگ‌تر = کاف بزرگ‌تر)", "ترتیبی", "کنترل کیفیت"),
    ("BPAOARM", "بازوی اندازه‌گیری (راست/چپ)", "اسمی", "کنترل کیفیت"),
    ("WTMEC2YR", "وزن نمونه‌گیری معاینه (MEC)", "کمی پیوسته", "وزن"),
    ("SDMVSTRA, SDMVPSU", "طبقه و واحد نمونه‌گیری اولیه", "اسمی", "طرح نمونه‌گیری"),
], columns=["متغیر", "توضیح", "نوع/مقیاس", "نقش"])
tab_vars = table(vars_tab, list(vars_tab.columns))

structure = pd.DataFrame([
    ("DEMO_L", "فرد", "۱ ردیف", f"{int(T['T1_flow'].n[0]):,}", "جمعیت‌شناختی، وزن، طرح نمونه‌گیری"),
    ("BPXO_L", "فرد", "۱ ردیف (سه قرائت در سه ستون)", f"{int(T['T1_flow'].n[1]):,}", "فشارخون و ضربان"),
    ("BMX_L", "فرد", "۱ ردیف", f"{int(T['T1_flow'].n[2]):,}", "قد، وزن، BMI، دور کمر"),
], columns=["فایل", "واحد", "ساختار", "تعداد ردیف", "محتوا"])
tab_struct = table(structure, list(structure.columns))

def find_chrome():
    """Locate Chrome/Chromium on Windows, macOS or Linux (or use the CHROME_PATH env var)."""
    env = os.environ.get("CHROME_PATH")
    if env and Path(env).exists():
        return env
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise FileNotFoundError("Chrome/Chromium not found. Install Google Chrome or set the CHROME_PATH environment variable.")


CSS = """
@page { size: A4; margin: 18mm 15mm; }
body { font-family: 'DejaVu Sans', sans-serif; direction: rtl; font-size: 10.2pt; line-height: 1.85; color:#1a202c; }
h1 { font-size: 20pt; margin: 0 0 4px; color:#1a365d; } h2 { font-size: 13.5pt; color:#2b6cb0; border-bottom:2px solid #bee3f8; padding-bottom:3px; margin-top:22px; page-break-after: avoid;}
h3 { font-size: 11.2pt; color:#2c5282; margin-bottom:2px; page-break-after: avoid;}
table { border-collapse: collapse; width:100%; margin:8px 0 12px; font-size: 8.6pt; direction: rtl; page-break-inside: avoid; }
th { background:#2b6cb0; color:white; padding:4px 5px; white-space: pre-line; } td { border:1px solid #cbd5e0; padding:3px 5px; text-align:center; }
tr:nth-child(even) td { background:#f7fafc; } td:first-child { text-align:right; }
.fig { text-align:center; page-break-inside: avoid; margin: 10px 0; } .fig img { width: 86%; } .cap { font-size:9pt; color:#4a5568; }
.box { background:#ebf8ff; border-right:4px solid #3182ce; padding:6px 12px; margin:8px 0; page-break-inside: avoid;}
.warn { background:#fffaf0; border-right:4px solid #dd6b20; padding:6px 12px; margin:8px 0; page-break-inside: avoid;}
.cover { text-align:center; padding: 120px 0 30px; page-break-after: always; } .cover p { margin:4px; }
code { direction:ltr; unicode-bidi: embed; font-size:9pt; background:#edf2f7; padding:0 3px; }
.ltr { direction:ltr; unicode-bidi: embed; }
"""

html = f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>{CSS}</style></head><body>

<div class="cover">
<p style="font-size:11pt;color:#4a5568">پروژه‌ی درس آمار — فاز اول</p>
<h1>فاز ۱: شناخت مطالعه، داده و آمار توصیفی</h1>
<p style="font-size:14pt">مقایسه‌ی قرائت اول و سوم فشارخون سیستولیک</p>
<p style="font-size:11pt">بررسی تفاوت درون‌فردی قرائت‌های متوالی فشارخون سیستولیک در بزرگسالان آمریکایی</p>
<p style="font-size:11pt">NHANES 2021–2023 (چرخه‌ی L) — مسیر الف</p>
<p style="margin-top:30px;color:#4a5568">نام : محدثه رضوی &nbsp;&nbsp; شماره‌ی دانشجویی: 403170174</p>
</div>

<h2>۱. خلاصه و سؤال پژوهش</h2>
<div class="box"><b>سؤال آماری اصلی:</b> در بزرگسالان ≥ ۲۰ سال شرکت‌کننده در NHANES 2021–2023 که هر سه قرائت فشارخون را دارند،
اختلاف درون‌فردی فشارخون سیستولیک قرائت اول و سوم (قرائت اول منهای سوم) چقدر است و آیا این اختلاف بین مردان و زنان و
گروه‌های سنی ۲۰–۳۹، ۴۰–۵۹ و ۶۰+ متفاوت است؟</div>
<p>در NHANES فشارخون هر فرد سه بار پشت سر هم اندازه‌گیری می‌شود. این ایده‌ی رایج وجود دارد که قرائت اول به‌دلیل اضطراب یا
«آرام نگرفتن» فرد بالاتر است. در این فاز بدون هیچ استنباطی فقط می‌فهمیم داده از کجا آمده، چه واحدی دارد، چقدر کامل است و
اختلاف قرائت‌ها به‌صورت توصیفی چگونه است.</p>
<p><b>مهم‌ترین یافته‌های توصیفی:</b> از {int(T['T1_flow'].n[4]):,} بزرگسال معاینه‌شده، {n_an:,} نفر هر سه قرائت را دارند (جمعیت تحلیلی).
میانگین اختلاف قرائت اول و سوم {d13['mean']:.2f} mmHg، میانه {d13['median']:.0f} و SD برابر {d13['sd']:.1f} است؛ یعنی
در میانگین اختلاف بسیار کوچک و در سطح فرد پراکنده است. قرائت اول در {S['pct_first_higher']:.1f}٪ افراد بالاتر از سوم،
در {S['pct_first_lower']:.1f}٪ پایین‌تر و در {S['pct_equal']:.1f}٪ برابر است. در این فاز ادعای استنباطی نمی‌شود.</p>

<h2>۲. منشأ داده و سازوکار جمع‌آوری</h2>
<p>NHANES (پیمایش ملی سلامت و تغذیه) را مرکز ملی آمار سلامت آمریکا (CDC/NCHS) اجرا می‌کند. هر شرکت‌کننده ابتدا مصاحبه‌ی خانگی
می‌شود و سپس در یک مرکز معاینه‌ی سیار (MEC) معاینه می‌شود؛ فشارخون و اندازه‌گیری‌های بدنی در همین معاینه ثبت می‌شوند.
چرخه‌ی ۲۰۲۱–۲۰۲۳ (پسوند L) نخستین انتشار ملی NHANES پس از وقفه‌ی کرونا است. داده‌ی ما نتیجه‌ی یک <b>پیمایش مقطعی با
نمونه‌گیری احتمالی چندمرحله‌ای</b> است، نه آزمایش تصادفی؛ فشارخون با دستگاه اسیلومتریک و در سه قرائت متوالی ثبت شده است.
منبع رسمی: وب‌سایت داده‌ی NHANES در CDC (فایل‌های عمومی، بدون محدودیت دسترسی).</p>
<p><b>فایل‌های استفاده‌شده:</b> <span class="ltr">DEMO_L.xpt, BPXO_L.xpt, BMX_L.xpt</span>؛ کلید ادغام: <span class="ltr">SEQN</span>.</p>

<h2>۳. واحد مشاهده و ساختار داده</h2>
{tab_struct}
<p>در هر سه فایل، هر ردیف یک نفر است و هیچ <span class="ltr">SEQN</span> تکراری وجود ندارد؛ بنابراین ساختار سلسله‌مراتبی یا مراجعه‌ی
تکراری نداریم. سه قرائت فشارخون به‌صورت «عریض» (سه ستون) ذخیره شده‌اند. <b>واحد تحلیل: هر فرد بزرگسال معاینه‌شده.</b></p>

<h2>۴. نمونه‌گیری، انتخاب و قابلیت تعمیم</h2>
<p>NHANES نمونه‌ی تصادفی ساده نیست؛ نمونه‌گیری چندمرحله‌ای با طبقه‌بندی و خوشه‌بندی است و برخی گروه‌ها عمداً
بیش‌نمونه‌گیری می‌شوند. اثر آن در داده‌ی ما دیده می‌شود: افراد ۶۰+ سال {p60u:.1f}٪ فایل ولی فقط {p60w:.1f}٪ جمعیت
(وزن‌دار) را تشکیل می‌دهند و افراد ۲۰–۳۹ ساله {p2039u:.1f}٪ فایل ولی {p2039w:.1f}٪ جمعیت‌اند.</p>
<p><b>قابلیت تعمیم:</b> نتایج بدون وزن فقط درباره‌ی همین {n_an:,} نفر معنا دارند. برآوردهای وزن‌دار با استفاده از وزن نمونه‌گیری MEC (<span class="ltr">WTMEC2YR</span>) محاسبه شده‌اند و با هدف توصیف جمعیت بزرگسالان غیرنهادی (غیرساکن مراکز مثل زندان یا آسایشگاه) آمریکا تفسیر می‌شوند. با این حال، این وزن‌ها عدم‌پاسخ در سطح معاینه را تعدیل می‌کنند و ناقص‌بودن قرائت‌های فشارخون را اصلاح نمی‌کنند؛ پس انتخاب افراد دارای هر سه قرائت معتبر (حدود ۳٫۷٪ معاینه‌شدگان حذف شده‌اند) ممکن است بر قابلیت تعمیم نتایج اثر بگذارد. تعمیم به خارج از آمریکا یا به زمان‌های دیگر مجاز نیست.</p>

<h2>۵. طبقه‌بندی متغیرها</h2>
{tab_vars}

<h2>۶. جمعیت تحلیلی، ادغام و کیفیت داده</h2>
<h3>۶-۱. جریان داده (قبل و بعد از ادغام)</h3>
{tab_flow}
<p><b>تعریف جمعیت تحلیلی:</b> سن ≥ ۲۰ سال، معاینه‌شده در MEC (<span class="ltr">RIDSTATR=2</span>)، و دارای هر سه قرائت سیستولیک
. ادغام بر پایه‌ی <span class="ltr">SEQN</span> با پیوند چپ (left join) از DEMO انجام شد؛ تعداد ردیف‌ها پس از هر ادغام ۶٬۰۶۴ ماند
و ردیف مفقودی از ادغام ایجاد نشد. برای سادگی ردیف‌های دارای <i>هیچ</i> قرائت ({n_nobp}) و ردیف‌های ۱–۲ قرائت ({n_part}) از تحلیل اصلی حذف شدند.</p>
<h3>۶-۲. گمشدگی فشارخون بر حسب جنس و سن</h3>
{tab_miss}
<p>درصد نبود قرائت کامل کوچک (حدود ۳–۵٪) و در جنس‌ها و گروه‌های سنی نزدیک به هم است؛ بیشترین نبود در ۲۰–۳۹ ساله‌ها
(حدود ۴٫۶٪) و زنان (حدود ۴٫۱٪) دیده می‌شود. نبود داده کاملاً تصادفی فرض نمی‌شود (در بخش محدودیت‌ها).</p>
<h3>۶-۳. تصمیم‌های پاک‌سازی و دلیل آن‌ها</h3>
{tab_dec}

<h2>۷. جدول‌های فراوانی</h2>
<p>درصدها در جمعیت تحلیلی ({n_an:,} نفر) هم بدون وزن و هم با وزن <span class="ltr">WTMEC2YR</span> آمده‌اند.</p>
{tab_freq}
<p>الگوهای مهم: تفاوت درصد سنی بدون وزن و وزن‌دار (به‌خاطر بیش‌نمونه‌گیری سالمندان)، و اینکه قریب‌به‌اتفاق اندازه‌گیری‌ها روی بازوی راست
و با کاف‌های کد ۳ و ۴ انجام شده است. فقط ۱۷ نفر کاف کد ۲ دارند؛ زیرگروه‌ها بر پایه‌ی کاف بی‌ثبات می‌شوند.</p>

<h2>۸. مرکز و پراکندگی</h2>
{tab_num}
<p>توجیه معیارها: سن و فشارخون تقریباً متقارن‌اند و میانگین با SD مناسب است. اما برای <b>اختلاف (۱−۳)</b>
(میانگین {d13['mean']:.2f}، میانه {d13['median']:.0f}) توزیع در مرکز بسیار متراکم با دم‌های بلند است (بازه‌ی <bdi dir="ltr">[{d13['min']:.0f}, {d13['max']:.0f}]</bdi> در برابر
IQR برابر {d13['iqr']:.0f}). پس برای آن میانه و IQR گزارش مرجع‌اند و میانگین/SD فقط برای مقایسه با فازهای بعد ذکر می‌شوند.
برای BMI چولگی به راست دیده می‌شود (میانگین بالاتر از میانه)، پس میانه/IQR مناسب‌تر است.
همچنین اختلاف دیاستولیک (۱−۳) میانگین {dia['mean']:.2f} دارد، بزرگ‌تر از اختلاف سیستولیک نسبت به پراکندگی‌اش ({dia['sd']:.1f})، که در فازهای بعد قابل بررسی است.</p>

<h2>۹. مصورسازی</h2>
<div class="fig"><img src="{img('fig1_hist_sbp1.png')}"><div class="cap">شکل ۱. هیستوگرام فشارخون سیستولیک قرائت اول (mmHg). توزیع کمی چوله به راست؛ میانگین ({f(a.loc['Systolic reading 1']['mean'])}) کمی بالاتر از میانه ({f(a.loc['Systolic reading 1']['median'],0)}).</div></div>
<div class="fig"><img src="{img('fig2_box_readings.png')}"><div class="cap">شکل ۲. جعبه‌نمودار سه قرائت سیستولیک. سه توزیع تقریباً یکسان‌اند؛ میانگین‌ها ({f(a.loc['Systolic reading 1']['mean'])}، {f(a.loc['Systolic reading 2']['mean'])}، {f(a.loc['Systolic reading 3']['mean'])}) به‌طور جزئی کاهش می‌یابند.</div></div>
<div class="fig"><img src="{img('fig3_hist_diff13.png')}"><div class="cap">شکل ۳. هیستوگرام اختلاف درون‌فردی (قرائت۱ − قرائت۳). تقریباً متقارن و متمرکز روی صفر با دم‌های بلند.</div></div>
<div class="fig"><img src="{img('fig4_diff_by_sex_age.png')}"><div class="cap">شکل ۴. میانگین اختلاف (۱−۳) بر حسب سن و جنس، بدون وزن و وزن‌دار. مقدارها همگی نزدیک صفرند (کمتر از ۱٫۱ mmHg در قدر مطلق)؛ بزرگ‌ترین مقدار در مردان ۶۰+ است.</div></div>
<div class="fig"><img src="{img('fig5_missing_by_age.png')}"><div class="cap">شکل ۵. درصد معاینه‌شدگان فاقد سه قرائت معتبر بر حسب گروه سنی.</div></div>
<div class="fig"><img src="{img('fig6_diff_by_bmi.png')}"><div class="cap">شکل ۶. میانگین اختلاف (۱−۳) بر حسب دسته‌ی BMI (با تعداد در هر دسته). تفاوت‌ها کوچک‌اند و دسته‌ی کم‌وزن فقط ۷۷ نفر دارد.</div></div>
<p style="font-size:9pt;color:#4a5568">توجه: برچسب محورها و عنوان داخل شکل‌ها انگلیسی است و واحد (mmHg) روی محورها آمده است؛ توضیح فارسی در عنوان زیر هر شکل است.</p>

<h2>۱۰. اثر نمونه‌گیری: خلاصه‌ی خام در برابر وزن‌دار</h2>
{tab_rw}
<p>میانگین قرائت اول در کل بزرگسالان بدون وزن {rw.loc['All adults','mean_SBP1_raw']:.1f} و وزن‌دار {rw.loc['All adults','mean_SBP1_wtd']:.1f} mmHg است،
یعنی بدون وزن حدود {rw.loc['All adults','mean_SBP1_raw']-rw.loc['All adults','mean_SBP1_wtd']:.1f} mmHg بیش‌برآورد می‌کند. دلیل: سالمندان با فشار بالاتر در فایل بیش‌نماینده‌اند. اما برای
<b>اختلاف (۱−۳)</b> تفاوت وزن‌دار و بدون وزن بسیار کوچک است ({rw.loc['All adults','mean_diff13_raw']:.2f} در برابر {rw.loc['All adults','mean_diff13_wtd']:.2f})، چون این اختلاف
چندان به سن وابسته نیست. وزن‌ها {S['weight_ratio']:.0f} برابر تغییر می‌کنند (کمینه {S['weights_min']:,.0f}، بیشینه {S['weights_max']:,.0f})؛ مجموع وزن جمعیت تحلیلی حدود {S['sum_weights_analytic']/1e6:.0f} میلیون نفر است.
طرح شامل {S['n_strata']} طبقه و {S['n_psu']} واحد نمونه‌گیری اولیه است. در این فاز فقط برآورد نقطه‌ای وزن‌دار گزارش می‌شود؛ خطای استاندارد درستِ
طرح پیچیده در فازهای بعد (به‌ویژه فاز ۳ و ۵) مطرح می‌شود.</p>
<p><b>چرا هر فرد نماینده‌ی تعداد متفاوتی از جمعیت است؟</b> چون احتمال انتخاب افراد برابر نیست (بیش‌نمونه‌گیری برخی گروه‌ها)، و وزن
تقریباً معکوس احتمال انتخاب (با اصلاح برای عدم‌پاسخ) است: فرد با وزن بالاتر تعداد بیشتری از جمعیت را نمایندگی می‌کند.</p>

<h2>۱۱. مقایسه‌ی توصیفی اولیه </h2>
<h3>۱۱-۱. بر حسب جنس و گروه سنی</h3>
{tab_sa}
<h3>۱۱-۲. بر حسب دسته‌ی BMI</h3>
{tab_bmi}
<div class="warn">در همه‌ی زیرگروه‌ها میانگین اختلاف در قدر مطلق کمتر از ۱٫۱ mmHg است و علامتش در برخی زیرگروه‌ها عوض می‌شود، در حالی که SD حدود ۶ تا ۸ است. بزرگ‌ترین
مقدار (مردان ۶۰+ با {t6[(t6.sex=='مرد')&(t6.age_group=='60+')].mean_diff13.iloc[0]:.2f}) و کمترین مقدار (BMI ≥ ۳۰) شایسته‌ی بررسی بیشترند، ولی اینجا
فقط توصیف می‌کنیم؛ آیا این تفاوت‌ها فراتر از نوسان نمونه‌گیری‌اند در فاز ۳ بررسی می‌شود.</div>

<h2>۱۲. نهایی‌سازی سؤال آماری</h2>
<p><b>سؤال نهایی:</b> در بزرگسالان آمریکایی ≥ ۲۰ ساله (NHANES 2021–2023)، میانگین اختلاف درون‌فردی فشارخون سیستولیک قرائت اول و سوم چقدر است
و آیا بین مردان و زنان یا گروه‌های سنی متفاوت است؟ داده‌ی موجود برای این سؤال مناسب است چون هر فرد سه قرائت متوالی دارد
(طرح درون‌فردی/زوجی)، نمونه به‌قدر کافی بزرگ است و وزن‌ها اجازه‌ی تعمیم به جمعیت را می‌دهند.</p>
<p><b>فرضیه‌ی علمی اولیه :</b> با توجه به فیزیولوژی (اثر آرام‌گرفتن و اضطراب در ابتدای اندازه‌گیری)، انتظار می‌رود قرائت اول به‌طور میانگین
اندکی بیشتر از قرائت سوم باشد، و شاید این تفاوت در سالمندان بزرگ‌تر باشد. فرمول دقیق H₀/H₁ در فاز ۳ نوشته می‌شود.</p>
<p><b>نقشه‌ی فازها:</b> فاز ۲: احتمال «قرائت اول بالاتر است»، احتمال شرطی در زیرگروه‌ها، مدل دوجمله‌ای، توزیع نرمال اختلاف؛
فاز ۳: آزمون t زوجی، فاصله‌ی اطمینان، bootstrap، مقایسه‌ی مردان و زنان، ANOVA بین گروه‌های سنی؛
فاز ۴: رگرسیون اختلاف روی سن و جنس و BMI و نمودار باقیمانده؛ فاز ۵: حساسیت‌سنجی (ردیف‌های ۲ قرائت، حذف اختلاف‌های بزرگ، وزن‌دار/بدون وزن).</p>

<h2>۱۳. محدودیت‌های اولیه</h2>
<ul>
<li><b>طرح نمونه‌گیری پیچیده:</b> آزمون‌ها و فاصله‌های اطمینان استاندارد با فرض نمونه‌ی ساده‌ی تصادفی دقیق نیستند و باید طرح را در نظر گرفت.</li>
<li><b>داده‌ی گمشده:</b> حدود {100*(n_nobp+n_part)/n_exam:.1f}٪ معاینه‌شدگان قرائت کامل ندارند؛ ممکن است دلیل نبود با سن، جنس یا شرایط اندازه‌گیری مرتبط باشد.</li>
<li><b>کیفیت اندازه‌گیری:</b> نوسان طبیعی فشارخون، خطای دستگاه و رفتار فرد (حرکت، صحبت) روی اختلاف قرائت‌ها اثر دارد؛ داده فقط یک روز و یک نوبت اندازه‌گیری است. اندازه‌ی کاف نیز می‌تواند بر قرائت اثر بگذارد.</li>
<li><b>دقت اعداد:</b> قرائت‌ها عدد صحیح‌اند و بخشی از اختلاف‌ها دقیقاً صفر است ({S['pct_equal']:.1f}٪).</li>
<li><b>ماهیت مشاهده‌ای:</b> نتایج درباره‌ی قرائت‌های متوالی هستند، نه علت تفاوت.</li>
</ul>
<h2>۱۴. خروجی‌ها و بازتولید</h2>
<p>کد: <span class="ltr">src/phase1.py</span> (تحلیل، جدول‌ها و شکل‌ها) و <span class="ltr">src/make_report.py</span> (ساخت این گزارش). جدول‌ها: <span class="ltr">reports/phase1/tables/*.csv</span>؛
شکل‌ها: <span class="ltr">figures/phase1/*.png</span>. اجرا از ریشه‌ی مخزن: <span class="ltr">python src/phase1.py &amp;&amp; python src/make_report.py</span> (فایل‌های xpt داخل <span class="ltr">data/</span>).</p>
</body></html>"""

out_html = ROOT / "reports" / "phase1" / "phase1.html"
out_html.write_text(html, encoding="utf-8")
pdf = ROOT / "reports" / "phase1.pdf"
chrome_path = find_chrome()

subprocess.run([chrome_path, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", out_html.as_uri()], check=True, capture_output=True)
