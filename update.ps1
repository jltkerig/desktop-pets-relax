# Checks GitHub for a newer Pixel Fox and installs it. start.ps1 loads this with ". update.ps1" and calls
# Update-PixelFox before starting. Never stops Pixel Fox from starting: offline, GitHub down, or anything
# else going wrong just means it runs the version you have.
#
#   - The version is __version__ in pet\__init__.py; the newest is the one on GitHub's main branch.
#   - A copy made with "git clone" is updated with "git pull". A downloaded ZIP is updated by downloading
#     the newest ZIP and copying it over the top. Your settings in user-data are never touched.
#   - If Pixel Fox is running and there's an update, it's closed first and started again afterwards.
#   - Skipped if a file named "no-update" is in the app's folder.
$PixelFoxRepo = "jltkerig/desktop-pets-relax"
$PixelFoxBranch = "main"

function Get-PixelFoxVersion([string]$text) {
    if ($text -match '__version__\s*=\s*"(\d+\.\d+\.\d+)"') { return [version]$Matches[1] }
    return $null
}

function Get-PixelFoxRunning {
    # the desktop pets (not the screen saver, which runs with --scr)
    try {
        return @(Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction Stop |
            Where-Object { $_.CommandLine -like "*pixelfox.py*" -and $_.CommandLine -notlike "*--scr*" })
    } catch { return @() }
}

# Returns $true if it installed an update (start.ps1 then starts again, so the new start.ps1 is used).
function Update-PixelFox([string]$ProjectPath) {
    if (Test-Path (Join-Path $ProjectPath "no-update")) { return $false }
    try {
        # GitHub needs TLS 1.2, which older Windows PowerShell doesn't use by default
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        $local = Get-PixelFoxVersion (Get-Content -Raw (Join-Path $ProjectPath "pet\__init__.py"))
        $url = "https://raw.githubusercontent.com/$PixelFoxRepo/$PixelFoxBranch/pet/__init__.py"
        $remote = Get-PixelFoxVersion (Invoke-WebRequest -Uri "$($url)?t=$([DateTime]::UtcNow.Ticks)" -UseBasicParsing -TimeoutSec 8).Content  # (?t= : not a cached copy)
        if (-not $remote -or ($local -and $remote -le $local)) {
            Write-Host "Pixel Fox $local is up to date."
            return $false
        }
        Write-Host "Updating Pixel Fox from $local to $remote..."
        # don't swap files under a running copy: close it first (it starts again, updated, straight after)
        $running = Get-PixelFoxRunning
        if ($running.Count -gt 0) {
            Write-Host "Closing the running Pixel Fox so it can be updated..."
            foreach ($p in $running) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
            Start-Sleep -Milliseconds 800
        }

        if ((Test-Path (Join-Path $ProjectPath ".git")) -and (Get-Command git -ErrorAction SilentlyContinue)) {
            # a git that crashed once leaves .git\index.lock behind, and every pull after fails: if no git is
            # running now, that lock is left over, so clear it
            $lock = Join-Path $ProjectPath ".git\index.lock"
            if ((Test-Path $lock) -and -not (Get-Process git -ErrorAction SilentlyContinue)) {
                Remove-Item $lock -Force -ErrorAction SilentlyContinue
            }
            & git -C $ProjectPath pull --ff-only origin $PixelFoxBranch | Out-Host
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Couldn't update with git (local changes?). Starting the version you have."
                return $false
            }
        } else {
            $temp = Join-Path ([IO.Path]::GetTempPath()) ("pixelfox-update-" + [guid]::NewGuid())
            New-Item -ItemType Directory -Path $temp | Out-Null
            try {
                $zip = Join-Path $temp "pixelfox.zip"
                $zipUrl = "https://github.com/$PixelFoxRepo/archive/refs/heads/$PixelFoxBranch.zip"
                Invoke-WebRequest -Uri $zipUrl -OutFile $zip -UseBasicParsing -TimeoutSec 120
                Expand-Archive -Path $zip -DestinationPath $temp -Force
                $source = Get-ChildItem -Path $temp -Directory | Select-Object -First 1  # desktop-pets-relax-main
                if (-not $source -or -not (Test-Path (Join-Path $source.FullName "pixelfox.py"))) {
                    throw "the download didn't look like Pixel Fox"
                }
                Get-ChildItem -Path $source.FullName -Force | Where-Object { $_.Name -ne "user-data" } |
                    Copy-Item -Destination $ProjectPath -Recurse -Force
                # files from before 1.14.0, when these were split into folders: copying over leaves them behind
                foreach ($old in "pet\world.py", "pet\items.py", "pet\visitors.py", "pet\view.py", "art\world_art.py",
                                 "tests\test_pixelfox.py") {
                    Remove-Item -Path (Join-Path $ProjectPath $old) -Force -ErrorAction SilentlyContinue
                }
            } finally {
                Remove-Item -Path $temp -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
        Write-Host "Updated to Pixel Fox $remote."
        return $true
    } catch {
        Write-Warning "Couldn't check for updates ($($_.Exception.Message)). Starting the version you have."
        return $false
    }
}
