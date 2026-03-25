$ErrorActionPreference = 'Stop'

$taskName = 'PersonalBlog'
$taskDescription = 'Start the PersonalBlog FastAPI server when the current user logs on.'
$repoRoot = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $repoRoot 'start_blog.bat'
$cmdExe = Join-Path $env:SystemRoot 'System32\cmd.exe'
$startupShortcut = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\PersonalBlog.lnk'
$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

if (-not (Test-Path -LiteralPath $startScript)) {
    throw "start_blog.bat not found: $startScript"
}

if (-not (Test-Path -LiteralPath $cmdExe)) {
    throw "cmd.exe not found: $cmdExe"
}

$actionArgument = '/c ""{0}""' -f $startScript
$action = New-ScheduledTaskAction -Execute $cmdExe -Argument $actionArgument -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -Hidden -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds 0)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description $taskDescription `
    -Force | Out-Null

if (Test-Path -LiteralPath $startupShortcut) {
    Remove-Item -LiteralPath $startupShortcut -Force
    Write-Host "Removed startup shortcut: $startupShortcut"
}

$task = Get-ScheduledTask -TaskName $taskName
Write-Host "Registered scheduled task: $($task.TaskName)"
Write-Host "Task path: $($task.TaskPath)"
Write-Host "Task state: $($task.State)"
