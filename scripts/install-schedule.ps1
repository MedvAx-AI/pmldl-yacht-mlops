param([int]$Minutes = 5)
$ErrorActionPreference = 'Stop'
if ($Minutes -lt 5) { throw 'The minimum interval is five minutes.' }
$repoRoot = Split-Path -Parent $PSScriptRoot
$pipelinePython = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pipelinePython)) { throw 'Create .venv and install requirements first.' }
$pipelineScript = Join-Path $PSScriptRoot 'run_pipeline.py'
$action = New-ScheduledTaskAction -Execute $pipelinePython -Argument ('"' + $pipelineScript + '" --once') -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $Minutes)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'PMLDL-Yacht-Pipeline' -Description 'Prepare data, train and log model, build and deploy API and app every five minutes.' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Output "Installed PMLDL-Yacht-Pipeline; runs every $Minutes minutes while signed in. Keep Docker Desktop running."
