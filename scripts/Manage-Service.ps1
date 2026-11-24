[CmdletBinding()]
param(
    [ValidateSet('Install', 'Start', 'Stop', 'Status', 'Uninstall')]
    [string]$Action = 'Status'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$user = [Security.Principal.WindowsIdentity]::GetCurrent()
$name = "LINE Export Archive ($($user.User.Value))"
switch ($Action) {
    'Install' {
        $python = Join-Path $root '.venv/Scripts/pythonw.exe'
        $importer = Join-Path $root 'archive.py'
        if (!(Test-Path -LiteralPath $python -PathType Leaf)) {
            throw 'Run scripts/Setup.ps1 first.'
        }
        $taskAction = New-ScheduledTaskAction -Execute $python -Argument ('"{0}"' -f $importer) -WorkingDirectory $root
        $logon = New-ScheduledTaskTrigger -AtLogOn -User $user.Name
        $daily = New-ScheduledTaskTrigger -Daily -At '00:00'
        $repeat = New-ScheduledTaskTrigger -Once -At '00:00' -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 1)
        $daily.Repetition = $repeat.Repetition
        $principal = New-ScheduledTaskPrincipal -UserId $user.Name -LogonType Interactive -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
        Register-ScheduledTask -TaskName $name -Action $taskAction -Trigger @($logon, $daily) -Principal $principal -Settings $settings -Force | Out-Null
        Start-ScheduledTask -TaskName $name
    }
    'Start' {
        Enable-ScheduledTask -TaskName $name | Out-Null
        Start-ScheduledTask -TaskName $name
    }
    'Stop' {
        Disable-ScheduledTask -TaskName $name | Out-Null
        Stop-ScheduledTask -TaskName $name
    }
    'Status' {
        Get-ScheduledTask -TaskName $name | Select-Object TaskName, State
        Get-ScheduledTaskInfo -TaskName $name | Select-Object LastRunTime, LastTaskResult, NextRunTime
    }
    'Uninstall' {
        Disable-ScheduledTask -TaskName $name | Out-Null
        Stop-ScheduledTask -TaskName $name
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
    }
}
