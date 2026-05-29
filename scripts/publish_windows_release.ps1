param(
    [Parameter(Mandatory=$true)]
    [string]$Tag,
    [int]$TimeoutMinutes = 20,
    [int]$PollSeconds = 15
)

Set-StrictMode -Version Latest

function ExitWithError($msg, $code=1) {
    Write-Error $msg
    exit $code
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    ExitWithError "GitHub CLI 'gh' not found. Install from https://cli.github.com/"
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    ExitWithError "git not found in PATH."
}

Push-Location (Split-Path -Path $MyInvocation.MyCommand.Path -Parent) > $null
Pop-Location > $null

# Ensure we're in repo root
$repoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) { ExitWithError "Not inside a git repository." }
Set-Location $repoRoot

# Create or push the tag
$existing = git tag --list $Tag
if ($existing) {
    Write-Output "Tag $Tag already exists locally; pushing to origin..."
    git push origin $Tag
    if ($LASTEXITCODE -ne 0) { ExitWithError "Failed to push existing tag $Tag." }
} else {
    Write-Output "Creating and pushing tag $Tag..."
    git tag -a $Tag -m "Release $Tag"
    if ($LASTEXITCODE -ne 0) { ExitWithError "Failed to create tag $Tag." }
    git push origin $Tag
    if ($LASTEXITCODE -ne 0) { ExitWithError "Failed to push tag $Tag." }
}

$endTime = (Get-Date).AddMinutes($TimeoutMinutes)
Write-Output "Waiting up to $TimeoutMinutes minutes for release and asset..."
while ((Get-Date) -lt $endTime) {
    gh release view $Tag > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Output "Release $Tag exists. Attempting to download EXE asset..."
        New-Item -ItemType Directory -Force -Path dist | Out-Null
        gh release download $Tag --pattern "IndentAnalyzer-*.exe" -D dist 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Output "Downloaded EXE to dist\"
            exit 0
        } else {
            Write-Output "Release exists but asset not yet available. Waiting..."
        }
    } else {
        Write-Output "Release not created yet. Waiting..."
    }
    Start-Sleep -Seconds $PollSeconds
}

ExitWithError "Timed out waiting for release/asset after $TimeoutMinutes minutes." 2
