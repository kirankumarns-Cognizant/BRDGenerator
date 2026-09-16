# Agent 4: Gap Analysis - PowerShell Orchestrator

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoPath,
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "..\..\..\config\config.yaml",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Agent 4: Gap Analysis" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Validate paths
if (-not (Test-Path $RepoPath)) {
    Write-Error "Repository path not found: $RepoPath"
    exit 1
}

if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config file not found: $ConfigPath"
    exit 1
}

# Get absolute paths
$RepoPath = Resolve-Path $RepoPath
$ConfigPath = Resolve-Path $ConfigPath

# Determine KB/output path
if (-not $OutputPath) {
    $repoName = Split-Path $RepoPath -Leaf
    $OutputPath = Join-Path (Split-Path $ConfigPath -Parent | Split-Path -Parent) "KB" $repoName
}

Write-Host "Repository: $RepoPath" -ForegroundColor Green
Write-Host "Config: $ConfigPath" -ForegroundColor Green
Write-Host "KB Path: $OutputPath" -ForegroundColor Green
Write-Host ""

# Set Python script path
$pythonScript = Join-Path $PSScriptRoot "agent_4_gap_analysis.py"

if (-not (Test-Path $pythonScript)) {
    Write-Error "Python implementation not found: $pythonScript"
    exit 1
}

# Execute Python agent
Write-Host "Executing Agent 4..." -ForegroundColor Cyan
Write-Host ""

try {
    $startTime = Get-Date
    & python $pythonScript $RepoPath --config $ConfigPath --output $OutputPath
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Host "Agent 4 completed in $($duration.ToString('F2')) seconds" -ForegroundColor Green
        exit 0
    } else {
        Write-Error "Agent 4 failed with exit code: $exitCode"
        exit $exitCode
    }
} catch {
    Write-Error "Agent 4 execution error: $_"
    exit 1
}
