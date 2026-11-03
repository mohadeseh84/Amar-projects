# داده

## منبع داده
داده‌های این پروژه از وب‌سایت رسمی مرکز ملی آمار سلامت آمریکا (CDC/NCHS) و مجموعه‌ی NHANES مربوط به سال‌های ۲۰۲۱ تا ۲۰۲۳ (چرخه‌ی L) دریافت شده‌اند.
صفحه‌ی اصلی داده: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023

## فایل‌های لازم
- `DEMO_L.xpt` — اطلاعات جمعیت‌شناختی، وزن‌های نمونه‌گیری (`WTMEC2YR`)، طبقه و PSU
- `BPXO_L.xpt` — فشارخون اسیلومتریک (سه قرائت)
- `BMX_L.xpt` — اندازه‌گیری‌های بدنی (BMI و غیره)

دانلود مستقیم:
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.xpt
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.xpt
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.xpt

**تاریخ دریافت:** ۹ آبان ۱۴۰۵ (۳۱ اکتبر ۲۰۲۶)

این فایل‌های خام به‌دلیل حجم، در مخزن گیت‌هاب و فایل ZIP قرار داده نشده‌اند.

## بازسازی مجموعه‌ی تحلیلی
1. سه فایل بالا را داخل پوشه‌ی `data/` قرار دهید.
2. `pip install -r requirements.txt`
3. `python src/phase1.py`

کد، فایل‌ها را با شناسه‌ی مشترک `SEQN` به هم متصل می‌کند و افراد ۲۰ ساله و بالاتر را که در مرکز معاینه (MEC) معاینه شده‌اند و هر سه قرائت فشارخون سیستولیک را دارند نگه می‌دارد (n = 5,842 از 6,064 فرد معاینه‌شده). جریان کامل حذف‌ها در `reports/phase1/tables/T1_flow.csv` آمده است.
