# Starts Pixel Fox with no console window. Run it again any time; a second copy just exits.
# First it checks GitHub for a newer version and installs it (see update.ps1). -NoUpdate skips that.
param([switch]$NoUpdate)
$ErrorActionPreference = "Stop"
$ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $NoUpdate -and (Test-Path (Join-Path $ProjectPath "update.ps1"))) {
    . (Join-Path $ProjectPath "update.ps1")
    if (Update-PixelFox $ProjectPath) {
        # start again with the freshly updated start.ps1, in case it changed too
        & (Join-Path $ProjectPath "start.ps1") -NoUpdate
        return
    }
}

. (Join-Path $ProjectPath "find-python.ps1")
$PythonPath = Find-Python
if (-not $PythonPath) { throw "Python was not found. Install Python 3.12+ and try again." }

& $PythonPath -c "import PySide6, PIL, astral, tzlocal" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PySide6 and Pillow..."
    & $PythonPath -m pip install -r (Join-Path $ProjectPath "requirements.txt")
    if ($LASTEXITCODE -ne 0) {  # no permission to install for everyone: install just for this user
        & $PythonPath -m pip install --user -r (Join-Path $ProjectPath "requirements.txt")
    }
}
if (-not (Test-Path (Join-Path $ProjectPath "art\sprites\fox_orange_idle.png"))) {
    & $PythonPath (Join-Path $ProjectPath "art\make_art.py")
}

# pythonw.exe sits next to python.exe and runs without a console window.
$Windowless = Join-Path (Split-Path $PythonPath -Parent) "pythonw.exe"
if (-not (Test-Path $Windowless)) { $Windowless = $PythonPath }
Start-Process -FilePath $Windowless -ArgumentList "pixelfox.py" -WorkingDirectory $ProjectPath
Write-Host "Pixel Fox is running. Right-click the fox icon in the system tray for the toy box."
