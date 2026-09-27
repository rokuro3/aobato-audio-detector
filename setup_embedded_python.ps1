$ErrorActionPreference = "Stop"

$pythonVersion = "3.12.10"
$pythonTag = "3.12.10"
$root = (Resolve-Path $PSScriptRoot).Path
$pythonDir = Join-Path $root "python"
$archive = Join-Path $root "python-embed.zip"
$pythonExe = Join-Path $pythonDir "python.exe"
$sitePackages = Join-Path $pythonDir "Lib\site-packages"
$assetsDir = Join-Path $root "assets"
$modelFilename = "BirdNET+_V3.0-preview3.1_Global_11K_FP16_pruned.onnx"
$labelsFilename = "BirdNET+_V3.0-preview3.1_Global_11K_Labels.csv"
$modelUrl = "https://zenodo.org/records/20703646/files/$modelFilename`?download=1"
$labelsUrl = "https://zenodo.org/records/20703646/files/$labelsFilename`?download=1"
$modelPath = Join-Path $assetsDir $modelFilename
$labelsPath = Join-Path $assetsDir $labelsFilename
$pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonTag-embed-amd64.zip"
$getPip = Join-Path $root "get-pip.py"

function Download-WithProgress([string]$url, [string]$destination, [int]$startPercent, [int]$endPercent) {
    if ((Test-Path $destination) -and (Get-Item $destination).Length -gt 0) {
        Write-Progress -Activity "Setup" -Status "Using existing file: $(Split-Path $destination -Leaf)" -PercentComplete $endPercent
        return
    }

    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    $temporary = "$destination.download"
    try {
        Invoke-WebRequest -Uri $url -OutFile $temporary -UseBasicParsing -TimeoutSec 1800
        Write-Progress -Activity "Setup" -Status "Downloaded: $(Split-Path $destination -Leaf)" -PercentComplete $endPercent
        Move-Item -Path $temporary -Destination $destination -Force
    } catch {
        Remove-Item $temporary -Force -ErrorAction SilentlyContinue
        throw
    }
}

Write-Progress -Activity "Setup" -Status "Preparing..." -PercentComplete 0

if (-not (Test-Path $pythonExe)) {
    Write-Host "Downloading embedded Python $pythonVersion..."
    Download-WithProgress $pythonUrl $archive 0 25
    New-Item -ItemType Directory -Path $pythonDir -Force | Out-Null
    Expand-Archive -Path $archive -DestinationPath $pythonDir -Force
    Remove-Item $archive -Force
}
Write-Progress -Activity "Setup" -Status "Embedded Python ready" -PercentComplete 30

$pth = Get-ChildItem $pythonDir -Filter "python*._pth" | Select-Object -First 1
if ($null -eq $pth) { throw "Python *_._pth was not found." }
$pthText = Get-Content $pth.FullName -Raw
if ($pthText -notmatch "(?m)^Lib\\site-packages\s*$") {
    Add-Content -Path $pth.FullName -Value "Lib\site-packages"
}
if ($pthText -notmatch "(?m)^import site\s*$") {
    Add-Content -Path $pth.FullName -Value "import site"
}
New-Item -ItemType Directory -Path $sitePackages -Force | Out-Null

if (-not (Test-Path $getPip)) {
    Write-Host "Downloading pip..."
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
}
Write-Progress -Activity "Setup" -Status "Preparing pip..." -PercentComplete 35
& $pythonExe $getPip --disable-pip-version-check
Write-Progress -Activity "Setup" -Status "Installing required packages..." -PercentComplete 40
& $pythonExe -m pip install --disable-pip-version-check --upgrade --target $sitePackages -r (Join-Path $root "requirements.txt")
& $pythonExe -c "import streamlit; print('Streamlit import OK:', streamlit.__version__)"
Write-Progress -Activity "Setup" -Status "Preparing BirdNET V3.0 model..." -PercentComplete 75
Download-WithProgress $modelUrl $modelPath 75 95
Download-WithProgress $labelsUrl $labelsPath 95 100
Write-Progress -Activity "Setup" -Status "Complete" -PercentComplete 100
Write-Progress -Activity "Setup" -Completed
Write-Host "Embedded Python, libraries, BirdNET V3.0 model, and labels setup completed."
Write-Host "Run run_app.bat to start the app."