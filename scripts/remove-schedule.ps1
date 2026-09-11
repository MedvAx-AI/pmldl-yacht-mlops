$ErrorActionPreference = 'Stop'
Unregister-ScheduledTask -TaskName 'PMLDL-Yacht-Pipeline' -Confirm:$false
Write-Output 'Removed PMLDL-Yacht-Pipeline. Existing containers are still running.'
