[CmdletBinding()]
param(
    [ValidateSet('Codex', 'Claude', 'Both', 'None')]
    [string]$Client = 'None',
    [switch]$NoBackground,
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if ($Client -in @('Codex', 'Both')) { Get-Command codex -ErrorAction Stop | Out-Null }
if ($Client -in @('Claude', 'Both')) { Get-Command claude -ErrorAction Stop | Out-Null }

$venv = Join-Path $root '.venv'
& $Python -c 'import sys, tkinter; assert sys.version_info >= (3, 11), "Python 3.11 or later is required"'
if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 or later with Tcl/Tk and add it to PATH.' }
& $Python -m venv $venv
if ($LASTEXITCODE -ne 0) { throw 'Could not create the virtual environment.' }

$exe = Join-Path $venv 'Scripts/python.exe'
$server = Join-Path $root 'mcp_server.py'
& $exe -m pip install --requirement (Join-Path $root 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not install the MCP dependencies.' }

$inbox = Join-Path $env:LOCALAPPDATA 'LineExportArchive/inbox'
New-Item -ItemType Directory -Path $inbox -Force | Out-Null
if ($Client -in @('Codex', 'Both')) {
    & codex mcp add line-export-archive -- $exe $server
    if ($LASTEXITCODE -ne 0) { throw 'Codex MCP registration failed. See README for the manual setup.' }
}
if ($Client -in @('Claude', 'Both')) {
    & claude mcp add --transport stdio --scope user line-export-archive -- $exe $server
    if ($LASTEXITCODE -ne 0) { throw 'Claude Code MCP registration failed. See README for the manual setup.' }
}
if (!$NoBackground) {
    & (Join-Path $PSScriptRoot 'Manage-Service.ps1') Install
}
Write-Host "Inbox: $inbox"
Write-Host 'Restart your MCP client after registration. Use scripts/Open-Viewer.ps1 to open the local viewer.'
