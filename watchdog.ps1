# watchdog.ps1 - checks orb_auto.py and orb_ui.py are running; restarts
# whichever has died. Intended to run on a recurring Windows Scheduled Task
# (see setup_watchdog_task.ps1) so it survives independently of any chat
# session, terminal window, or process crash - the exact failure mode that
# silently took both processes down earlier today.

$Project = "C:\Code\Trade\TradePlan"
$Py = Join-Path $Project ".venv\Scripts\python.exe"
$LogFile = Join-Path $Project "watchdog.log"

function Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $LogFile -Value $line
}

function Test-Running($scriptName) {
    $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match [regex]::Escape($scriptName) }
    return $procs.Count -gt 0
}

function Start-OrbProcess($scriptName, $logName) {
    $logPath = Join-Path $Project $logName
    Start-Process -FilePath $Py -ArgumentList $scriptName -WorkingDirectory $Project `
        -RedirectStandardOutput $logPath -RedirectStandardError "$logPath.err" -WindowStyle Hidden
    Log "Restarted $scriptName (was not running)."
}

if (-not (Test-Path $Py)) {
    Log "ERROR: venv python not found at $Py - cannot restart anything."
    exit 1
}

if (-not (Test-Running "orb_auto.py")) {
    Start-OrbProcess "orb_auto.py" "orb_auto_run.log"
}

if (-not (Test-Running "orb_ui.py")) {
    Start-OrbProcess "orb_ui.py" "ui_run.log"
}
