# پروژه‌ی درس آمار — پاییز ۱۴۰۵ (مسیر الف: NHANES 2021–2023)

**موضوع:** آیا قرائت اول فشارخون بالاتر از قرائت سوم است؟ (تفاوت درون‌فردی قرائت‌های متوالی فشارخون سیستولیک)

## وضعیت فازها
| فاز | وضعیت |
|---|---|
| 1 — شناخت داده و آمار توصیفی | ✅ انجام شد (`reports/phase1.pdf`) |
| 2–5 | — |

## بازتولید فاز ۱
1. فایل‌های `DEMO_L.xpt`, `BPXO_L.xpt`, `BMX_L.xpt` را مطابق `data/README.md` داخل `data/` بگذارید.
2. `pip install -r requirements.txt`
3. `python src/phase1.py` (جدول‌ها و شکل‌ها) سپس `python src/make_report.py` (گزارش PDF؛ نیازمند Google Chrome یا Chromium. مسیر Chrome در ویندوز، مک و لینوکس خودکار پیدا می‌شود؛ اگر پیدا نشد، متغیر محیطی `CHROME_PATH` را برابر مسیر آن بگذارید).

## ساختار
`PROJECT_CARD.md` · `data/README.md` · `src/` · `figures/phase1/` · `reports/phase1.pdf` · `reports/phase1/tables/`
