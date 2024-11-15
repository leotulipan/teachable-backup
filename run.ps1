$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
& ..\.venv\Scripts\Activate.ps1
python $args 