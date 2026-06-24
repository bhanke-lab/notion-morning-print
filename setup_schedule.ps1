<#
  Registers the morning-print scheduled task.
  Uses Interactive logon (no stored password) so it works on locked-down
  domain PCs. Runs while you are logged on, including a locked screen.

  Examples:
    .\setup_schedule.ps1                              # weekdays at 5:15 AM (default)
    .\setup_schedule.ps1 -Time "6:30AM"               # different time
    .\setup_schedule.ps1 -Days Monday,Wednesday,Friday -Time "5:00AM"
#>
param(
    [string]   $Time = "5:15AM",
    [string[]] $Days = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"),
    [string]   $TaskName = "Notion Morning Print",
    [string]   $Path = $PSScriptRoot          # the repo folder this script lives in
)

$py = Join-Path $Path ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $py)) {
    Write-Error "Could not find $py . Create the venv first (python -m venv .venv)."
    exit 1
}

$action = New-ScheduledTaskAction -Execute $py `
    -Argument "morning_tasks_print.py --quiet" -WorkingDirectory $Path
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Days -At $Time
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "Registered '$TaskName' for $($Days -join ', ') at $Time" -ForegroundColor Green