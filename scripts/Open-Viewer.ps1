$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Start-Process -FilePath (Join-Path $root '.venv/Scripts/pythonw.exe') -ArgumentList ('"{0}"' -f (Join-Path $root 'viewer.py')) -WindowStyle Hidden
