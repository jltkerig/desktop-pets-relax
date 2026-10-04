# Finds a working Python 3.9 or newer on any Windows 10 or 11 computer. start.ps1 loads this with ". find-python.ps1".
# Tries, in order:
#   1. the newest Python 3 installed for this user or for everyone (python.org installer folders)
#   2. the "py" launcher
#   3. python.exe on PATH, including the Microsoft Store version
# Every candidate is test-run first, so the Store's "python" placeholder (which only opens the Store) is
# never picked by mistake. Returns $null when none works.
function Test-Python($path) {
    if (-not $path -or -not (Test-Path $path)) { return $false }
    try {
        $ok = & $path -c "import sys; print(sys.version_info >= (3, 9))" 2>$null | Select-Object -First 1
        return $ok -eq "True"
    } catch { return $false }
}

function Find-Python {
    $folders = @((Join-Path $env:LOCALAPPDATA "Programs\Python"), $env:ProgramFiles, ${env:ProgramFiles(x86)}) | Where-Object { $_ }
    $installed = foreach ($folder in $folders) {
        Get-ChildItem -Path $folder -Directory -Filter "Python3*" -ErrorAction SilentlyContinue
    }
    $installed = $installed | Sort-Object { [int]($_.Name -replace '\D', '') } -Descending |
        ForEach-Object { Join-Path $_.FullName "python.exe" }
    foreach ($candidate in $installed) {
        if (Test-Python $candidate) { return $candidate }
    }

    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        try {
            $fromLauncher = (& py.exe -3 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
            if (Test-Python $fromLauncher) { return $fromLauncher }
        } catch { }
    }

    foreach ($command in (Get-Command python.exe, python3.exe -All -ErrorAction SilentlyContinue)) {
        if (Test-Python $command.Source) { return $command.Source }
    }
    return $null
}
