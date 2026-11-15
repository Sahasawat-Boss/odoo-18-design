# Clone / update Odoo 18 + third-party addon repos (OCA, Ecosoft) into .\odoo and .\external
# Usage:  .\scripts\get-addons.ps1          (clone missing, pull existing)
$ErrorActionPreference = 'Continue'   # git writes progress to stderr; check $LASTEXITCODE instead
$root = Split-Path $PSScriptRoot -Parent
$branch = '18.0'

$repos = [ordered]@{
    'odoo'                         = 'https://github.com/odoo/odoo.git'
    # --- budget control (Thai public-sector budgeting, by Ecosoft) ---
    'budgeting'                    = 'https://github.com/ecosoft-odoo/budgeting.git'
    # --- Thai localization: VAT, WHT, tax reports, gov procurement ---
    'l10n-thailand'                = 'https://github.com/OCA/l10n-thailand.git'
    # --- advance / clearing, petty cash ---
    'hr-expense'                   = 'https://github.com/OCA/hr-expense.git'
    # --- fixed assets (Enterprise-only in standard Odoo) ---
    'account-financial-tools'      = 'https://github.com/OCA/account-financial-tools.git'
    'account-financial-reporting'  = 'https://github.com/OCA/account-financial-reporting.git'
    # --- purchase request, work acceptance (ตรวจรับ) ---
    'purchase-workflow'            = 'https://github.com/OCA/purchase-workflow.git'
    # --- multi-level approval (tier validation) ---
    'server-ux'                    = 'https://github.com/OCA/server-ux.git'
    # --- dependencies: matrix widget (budget_control), xlsx reports ---
    'web'                          = 'https://github.com/OCA/web.git'
    'reporting-engine'             = 'https://github.com/OCA/reporting-engine.git'
    # --- dependencies: base_exception (gov PR), partner_firstname/company_type (l10n_th_partner) ---
    'server-tools'                 = 'https://github.com/OCA/server-tools.git'
    'partner-contact'              = 'https://github.com/OCA/partner-contact.git'
}

foreach ($name in $repos.Keys) {
    $dest = if ($name -eq 'odoo') { Join-Path $root 'odoo' } else { Join-Path $root "external\$name" }
    if (Test-Path (Join-Path $dest '.git')) {
        Write-Host "update $name"
        git -C $dest pull --ff-only --depth 1
        if ($LASTEXITCODE) { throw "pull failed: $name" }
    } else {
        Write-Host "clone  $name"
        git clone --depth 1 --branch $branch $repos[$name] $dest
        if ($LASTEXITCODE) { throw "clone failed: $name" }
    }
}
