# Double-click launcher (used by the Desktop shortcut):
# start Odoo in its own window if it is not running yet, wait until it answers, then open the browser.
param([int]$Port = 8070, [string]$Title = 'HRDI Odoo 18')

function Test-Port([int]$p) {
    $client = New-Object Net.Sockets.TcpClient
    try { $client.ConnectAsync('127.0.0.1', $p).Wait(300) -and $client.Connected } catch { $false } finally { $client.Close() }
}

if (-not (Test-Port $Port)) {
    # -NoExit: if Odoo crashes, the window stays open so the error can be read
    Start-Process powershell.exe -WorkingDirectory $PSScriptRoot -ArgumentList @(
        '-NoExit', '-ExecutionPolicy', 'Bypass', '-Command',
        "`$Host.UI.RawUI.WindowTitle = '$Title (port $Port) - close this window to stop Odoo'; & '$PSScriptRoot\start.ps1'"
    )
    $deadline = (Get-Date).AddSeconds(180)
    while (-not (Test-Port $Port)) {
        if ((Get-Date) -gt $deadline) {
            Add-Type -AssemblyName PresentationFramework
            [System.Windows.MessageBox]::Show("Odoo did not start on port $Port within 3 minutes.`nCheck the Odoo window for errors.", $Title) | Out-Null
            exit 1
        }
        Start-Sleep -Milliseconds 700
    }
}
Start-Process "http://localhost:$Port/odoo"
