# Agent 1 Discovery - PowerShell Orchestrator
# Executes Agent 1 discovery and scoping workflow

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoPath,
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "..\..\..\config\config.yaml",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = ""
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Agent 1: Discovery & Scoping" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Validate repository path
if (-not (Test-Path $RepoPath)) {
    Write-Error "Repository path not found: $RepoPath"
    exit 1
}

# Validate config path
if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config file not found: $ConfigPath"
    exit 1
}

# Get absolute paths
$RepoPath = Resolve-Path $RepoPath
$ConfigPath = Resolve-Path $ConfigPath

Write-Host "Repository: $RepoPath" -ForegroundColor Green
Write-Host "Config: $ConfigPath" -ForegroundColor Green
Write-Host ""

# Set Python script path (relative to this script)
$pythonScript = Join-Path $PSScriptRoot "agent_1_discovery.py"

if (-not (Test-Path $pythonScript)) {
    Write-Error "Python implementation not found: $pythonScript"
    exit 1
}

# Determine output path
if (-not $OutputPath) {
    $repoName = Split-Path $RepoPath -Leaf
    $OutputPath = Join-Path (Split-Path $ConfigPath -Parent | Split-Path -Parent) "KB" $repoName
}

# Build Python command with named arguments
$pythonArgs = @(
    $pythonScript,
    $RepoPath,
    "--config", $ConfigPath,
    "--output", $OutputPath
)

# Execute Python agent
Write-Host "Executing Agent 1 discovery..." -ForegroundColor Cyan
Write-Host ""

try {
    $startTime = Get-Date
    
    # Run Python script
    & python @pythonArgs
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Green
    Write-Host "Agent 1 Execution Complete" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Green
    Write-Host "Duration: $($duration.TotalMinutes.ToString('F2')) minutes" -ForegroundColor Green
    
    # Check for outputs
    $outputDir = if ($OutputPath) { $OutputPath } else { "..\..\..\KB\$repoName" }
    Write-Host ""
    Write-Host "Checking outputs in: $outputDir" -ForegroundColor Cyan
    
    $expectedOutputs = @(
        "scope_definition.json",
        "artifact_catalog.json",
        "dependency_map.json"
    )
    
    $foundOutputs = 0
    foreach ($output in $expectedOutputs) {
        $outputPath = Join-Path $outputDir $output
        if (Test-Path $outputPath) {
            Write-Host "  [OK] $output" -ForegroundColor Green
            $foundOutputs++
        } else {
            Write-Host "  [MISSING] $output" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "Outputs found: $foundOutputs / $($expectedOutputs.Count)" -ForegroundColor $(if ($foundOutputs -eq $expectedOutputs.Count) { "Green" } else { "Yellow" })
    
    exit 0
}
catch {
    Write-Host ""
    Write-Host "==================================" -ForegroundColor Red
    Write-Host "Agent 1 Execution Failed" -ForegroundColor Red
    Write-Host "==================================" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "  1. Check that Python dependencies are installed: pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "  2. Verify .env file exists with ANTHROPIC_API_KEY" -ForegroundColor Yellow
    Write-Host "  3. Check config.yaml is valid" -ForegroundColor Yellow
    Write-Host "  4. Run with -Verbose for more details" -ForegroundColor Yellow
    
    exit 1
}
