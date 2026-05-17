Param(
    [string]$CardRepoPath = $env:CARD_REPO_PATH
)

if (-not $CardRepoPath) {
    $CardRepoPath = "../../../../kobrax-lan-hass-card"
}

$source = Join-Path $PSScriptRoot "../dist/kobrax-lan-card.js"
$targetDir = Resolve-Path -Path $CardRepoPath -ErrorAction SilentlyContinue
if (-not $targetDir) {
    throw "Card repo path not found: $CardRepoPath"
}
$target = Join-Path $targetDir.Path "kobrax-lan-card.js"

if (-not (Test-Path $source)) {
    throw "Build artifact not found: $source"
}

Copy-Item -Path $source -Destination $target -Force
Write-Host "Exported card artifact to $target"
