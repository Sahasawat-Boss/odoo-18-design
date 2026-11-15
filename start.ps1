# Start HRDI Odoo 18 (http://localhost:8070). Extra args pass through, e.g.:
#   .\start.ps1 -d hrdi18 -u hrdi_xxx
$env:PYTHONUTF8 = '1'
Set-Location $PSScriptRoot
& .\venv\Scripts\python.exe .\odoo\odoo-bin -c .\odoo.conf @args
