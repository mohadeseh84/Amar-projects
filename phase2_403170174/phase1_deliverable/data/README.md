# داده‌های پروژه

## منبع رسمی
CDC/NCHS — NHANES 2021–2023 (چرخه L):
https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023

## فایل‌های لازم برای بازتولید
- `DEMO_L.xpt` — اطلاعات جمعیت‌شناختی، وزن MEC (`WTMEC2YR`)، طبقه (`SDMVSTRA`) و PSU (`SDMVPSU`)
- `BPXO_L.xpt` — سه قرائت فشارخون سیستولیک و دیاستولیک
- `BMX_L.xpt` — اندازه‌گیری‌های بدنی از جمله BMI

لینک دریافت مستقیم:
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.xpt
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.xpt
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.xpt

فایل‌های خام در ZIP تحویل قرار داده نشده‌اند. آن‌ها را بدون تغییر در همین پوشه ذخیره کنید.

## ساخت نمونه تحلیلی
از ریشه پروژه اجرا کنید:
```bash
python src/phase1.py
```
کد فایل‌ها را با `SEQN` ادغام می‌کند و افراد ۲۰ ساله و بالاتر، معاینه‌شده در MEC (`RIDSTATR=2`) و دارای هر سه قرائت سیستولیک معتبر را نگه می‌دارد. تعداد مورد انتظار نمونه تحلیلی ۵٬۸۴۲ نفر یکتا از ۶٬۰۶۴ فرد معاینه‌شده است. کد فاز دوم همین فرایند را مجدداً انجام می‌دهد و کنترل تعداد و یکتایی شناسه‌ها را اجرا می‌کند.
