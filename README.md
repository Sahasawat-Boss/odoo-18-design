# HRDI ERP — SAP → Odoo 18 (Community + OCA/Ecosoft)

แนวคิดหลัก: **งบประมาณคุมทุกการใช้เงิน (กันงบตั้งแต่ PR / PO / ยืมเงิน) แล้วทุกอย่างลง GL**

## ทำไม Odoo 18 (ไม่ใช่ 20)
ตรวจเมื่อ 2026-11-15: โมดูลที่ระบบนี้พึ่งพายังไม่ถูกย้ายไป 20.0

| แหล่ง | 20.0 | 18.0 |
|---|---|---|
| ecosoft-odoo/budgeting (budget_control) | 5 โมดูลฐาน (ยังกันงบไม่ได้) | 34 โมดูล |
| OCA/l10n-thailand | 2 (utils) | 15 (VAT, WHT, 50 ทวิ, รายงานภาษี, ครุภัณฑ์, PR ราชการ) |
| OCA/hr-expense (ยืมเงิน, เงินสดย่อย) | 0 | มี |
| OCA/account-financial-tools (ครุภัณฑ์) | 0 | มี |
| OCA/purchase-workflow (PR, ตรวจรับ) | 0 | มี |

## Fit-gap
| ความต้องการ | ใช้ | สถานะ |
|---|---|---|
| ขาย / ขายหน้าร้าน | sale_management, point_of_sale | มาตรฐาน |
| โรงแรม / สถานที่ | — | **custom** (ต้องประเมิน OCA/pms แยก) |
| บัญชีลูกหนี้ | account (Customer Invoices) | มาตรฐาน |
| รับเงิน / เช็ครับ | account (Payments) | มาตรฐาน; การติดตามสถานะเช็ค **ต้องตรวจเพิ่ม** |
| แผนและงบประมาณ, กันงบ PR/PO/ยืมเงิน | budget_control, budget_activity, budget_control_purchase_request / _purchase / _expense / _advance_clearing | OCA/Ecosoft |
| ยืมเงิน → จ่าย → เคลียร์ | hr_expense_advance_clearing | OCA |
| เงินสดย่อย | hr_expense_petty_cash, budget_control_petty_cash | OCA |
| จัดซื้อจัดจ้าง / สัญญา | purchase, purchase_request, l10n_th_gov_purchase_request | OCA; วิธีจัดซื้อตาม พ.ร.บ. / e-GP **ต้องตรวจ gap** |
| ตรวจรับงาน + คณะกรรมการ | purchase_work_acceptance | OCA + **custom คณะกรรมการ** |
| เจ้าหนี้ → จ่ายเงิน | account (Bills, Payments) | มาตรฐาน |
| พัสดุ | stock | มาตรฐาน |
| ครุภัณฑ์ | account_asset_management, l10n_th_account_asset_management, budget_control_account_asset_management | OCA (Assets มาตรฐานเป็น Enterprise) |
| แจ้งซ่อมครุภัณฑ์ | maintenance | มาตรฐาน; ผูกกับทะเบียนครุภัณฑ์อาจต้อง custom |
| ยานพาหนะ | fleet | มาตรฐาน |
| GL + Analytic + ภาษีซื้อ/ขาย/หัก ณ ที่จ่าย | account, analytic, l10n_th, l10n_th_account_tax, _wht_cert_form, _tax_report, account_financial_report | มาตรฐาน + OCA |
| ย้ายข้อมูลจาก SAP | ผังบัญชี, ยอดยกมา, AR/AP ค้าง, ทะเบียนครุภัณฑ์, ยอดงบคงเหลือ | **custom / งานใหญ่สุด** |

## โครงสร้าง
```
odoo/            Odoo 18.0 (ไม่ commit — ดึงด้วย scripts/get-addons.ps1)
external/        OCA + Ecosoft repos @18.0 (ไม่ commit)
custom_addons/   โมดูล hrdi_* ที่เขียนเอง  <- งานของเราอยู่ที่นี่
scripts/         get-addons.ps1
```

## ติดตั้ง (Windows)
```powershell
.\scripts\get-addons.ps1
py -3.13 -m venv venv
# รวม requirements ของ Odoo (ตัด rl-renderPM ที่ไม่มี wheel บน Py3.13/Windows) + ของ OCA
$req = Get-Content .\odoo\requirements.txt | Where-Object { $_ -notmatch '^rl-renderPM' }
$extra = Get-ChildItem .\external\*\requirements.txt | ForEach-Object { Get-Content $_ } | Where-Object { $_ -and $_ -notmatch '^\s*#' }
($req + $extra + 'watchdog') | Set-Content -Encoding ascii req-win.txt
.\venv\Scripts\pip install -r req-win.txt

Copy-Item odoo.conf.example odoo.conf   # แก้รหัสผ่าน
# Postgres (superuser): CREATE DATABASE hrdi18 OWNER odoo ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C' TEMPLATE template0;
.\start.ps1      # http://localhost:8070
```

## หมายเหตุ Windows
- `odoo.conf` ต้องเป็น ASCII ล้วน
- Postgres บน Windows: สร้าง DB ด้วย LC_COLLATE/LC_CTYPE = C ทั้งคู่ (หรือ `db_template = template1`)
- อย่าใช้ `dev_mode = xml,qweb` (ช้าลง ~15 เท่า)
