# watchdog_loop.ps1 - runs forever, checking every 90s that orb_auto.py and
# orb_ui.py are alive; restarts whichever died. Replaces the Task Scheduler
# approach, whose "repeat every N minutes" trigger did not reliably
# self-fire in this environment (worked when manually invoked via
# `schtasks /Run`, but the recurring trigger never fired on its own -
# a known quirk with Interactive-logon scheduled tasks in some sandboxed/
# remote-desktop contexts). This loop is simpler to verify directly and
# doesn't depend on Task Scheduler's trigger-condition subtleties.
#
# Auto-started on every logon via a shortcut in the Startup folder (see
# setup - a .lnk in shell:startup running this hidden), so it survives
# reboots too, not just this session.

$Project = "C:\Code\Trade\TradePlan"
$Py = Join-Path $Project ".venv\Scripts\python.exe"
$LogFile = Join-Path $Project "watchdog.log"

function Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $LogFile -Value $line
}

function Test-Running($scriptName) {
    try {
        $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction Stop |
            Where-Object { $_.CommandLine -match [regex]::Escape($scriptName) }
        return $procs.Count -gt 0
    } catch {
        Log "Test-Running($scriptName) ERROR: $_"
        return $true   # fail safe: assume running rather than risk a duplicate launch on a transient WMI error
    }
}

function Start-OrbProcess($scriptName, $logName) {
    $logPath = Join-Path $Project $logName
    try {
        Start-Process -FilePath $Py -ArgumentList $scriptName -WorkingDirectory $Project `
            -RedirectStandardOutput $logPath -RedirectStandardError "$logPath.err" -WindowStyle Hidden
        Log "Restarted $scriptName (was not running)."
    } catch {
        Log "Start-OrbProcess($scriptName) ERROR: $_"
    }
}

Log "watchdog_loop started (pid $PID)."

while ($true) {
    if (-not (Test-Path $Py)) {
        Log "ERROR: venv python not found at $Py - cannot restart anything."
    } else {
        if (-not (Test-Running "orb_auto.py")) { Start-OrbProcess "orb_auto.py" "orb_auto_run.log" }
        if (-not (Test-Running "orb_ui.py"))   { Start-OrbProcess "orb_ui.py" "ui_run.log" }
    }
    Start-Sleep -Seconds 90
}
