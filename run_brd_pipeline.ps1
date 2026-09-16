# BRD Pipeline Orchestrator with GitNexus Integration
# Runs the complete BRD generation pipeline on a repository

param(
    [Parameter(Mandatory=$true)]
    [string]$RepoPath,
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "config\config.yaml",
    
    [switch]$UseGitNexus
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  BRD Pipeline - Agent Orchestrator" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Validate paths
$RepoPath = Resolve-Path $RepoPath
$ConfigPath = Resolve-Path $ConfigPath

Write-Host "Repository: $RepoPath" -ForegroundColor Green
Write-Host "Config: $ConfigPath" -ForegroundColor Green
Write-Host "GitNexus: $(if ($UseGitNexus) { 'Enabled' } else { 'Disabled' })" -ForegroundColor Green
Write-Host ""

# Setup KB directory
$repoName = Split-Path $RepoPath -Leaf
$kbDir = Join-Path (Split-Path $ConfigPath -Parent | Split-Path -Parent) "KB"
$kbRepoDir = Join-Path $kbDir $repoName

if (-not (Test-Path $kbRepoDir)) {
    Write-Host "Creating KB directory: $kbRepoDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $kbRepoDir -Force | Out-Null
}

# Step 0: Run GitNexus analysis if enabled
if ($UseGitNexus) {
    Write-Host "================================================" -ForegroundColor Magenta
    Write-Host "  Step 0: GitNexus Analysis" -ForegroundColor Magenta
    Write-Host "================================================" -ForegroundColor Magenta
    Write-Host ""
    
    Push-Location $RepoPath
    try {
        # Check if .git exists
        if (-not (Test-Path ".git")) {
            Write-Host "Initializing git repository..." -ForegroundColor Yellow
            git init | Out-Null
        }
        
        Write-Host "Running GitNexus analysis..." -ForegroundColor Cyan
        npx gitnexus analyze
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "GitNexus analysis complete" -ForegroundColor Green
        } else {
            Write-Warning "GitNexus analysis failed, continuing with standard analysis"
        }
    } finally {
        Pop-Location
    }
    Write-Host ""
}

# Agent execution order
$agents = @(
    @{ Number = 1; Name = "Discovery and Scoping"; Script = ".github\skills\agent-1-discovery\agent_1_discovery.ps1" },
    @{ Number = 2; Name = "Journey Mapping"; Script = ".github\skills\agent-2-journey-mapping\agent_2_journey_mapping.ps1" },
    @{ Number = 3; Name = "Business Rules"; Script = ".github\skills\agent-3-business-rules\agent_3_business_rules.ps1" },
    @{ Number = 4; Name = "Gap Analysis"; Script = ".github\skills\agent-4-gap-analysis\agent_4_gap_analysis.ps1" },
    @{ Number = 5; Name = "Synthesis"; Script = ".github\skills\agent-5-synthesis\agent_5_synthesis.ps1" },
    @{ Number = 6; Name = "Acceptance Criteria"; Script = ".github\skills\agent-6-acceptance-criteria\agent_6_acceptance_criteria.ps1" },
    @{ Number = 7; Name = "Risk and Dependency"; Script = ".github\skills\agent-7-risk-dependency\agent_7_risk_dependency.ps1" },
    @{ Number = 8; Name = "BRD Summarizer"; Script = ".github\skills\agent-8-summarizer\agent_8_summarizer.ps1" },
    @{ Number = 9; Name = "KB Store Sync"; Script = ".github\skills\agent-9-kb-store-sync\agent_9_kb_store_sync.ps1" }
)

$overallStartTime = Get-Date
$results = @()

# Execute agents sequentially
foreach ($agent in $agents) {
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "  Agent $($agent.Number): $($agent.Name)" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $agentStartTime = Get-Date
    
    if (Test-Path $agent.Script) {
        try {
            # Execute agent - use full path to avoid parameter binding issues
            $agentScriptPath = Resolve-Path $agent.Script
            $kbOutputPath = Join-Path $kbDir $repoName
            
            & $agentScriptPath -RepoPath $RepoPath -ConfigPath $ConfigPath -OutputPath $kbOutputPath
            $exitCode = $LASTEXITCODE
            
            $agentEndTime = Get-Date
            $duration = ($agentEndTime - $agentStartTime).TotalMinutes
            
            $results += @{
                Agent = "Agent $($agent.Number)"
                Name = $agent.Name
                Status = if ($exitCode -eq 0) { "Success" } else { "Failed" }
                Duration = "$($duration.ToString('F2')) min"
            }
            
            if ($exitCode -ne 0) {
                Write-Warning "Agent $($agent.Number) exited with code $exitCode"
                Write-Host "Do you want to continue with remaining agents? (Y/N): " -NoNewline -ForegroundColor Yellow
                $response = Read-Host
                if ($response -ne "Y" -and $response -ne "y") {
                    Write-Host "Pipeline execution aborted." -ForegroundColor Red
                    exit 1
                }
            }
            
        } catch {
            Write-Error "Agent $($agent.Number) execution failed: $_"
            
            $results += @{
                Agent = "Agent $($agent.Number)"
                Name = $agent.Name
                Status = "Error"
                Duration = "N/A"
            }
        }
    } else {
        Write-Warning "Agent script not found: $($agent.Script)"
        Write-Host "Skipping Agent $($agent.Number)..." -ForegroundColor Yellow
        
        $results += @{
            Agent = "Agent $($agent.Number)"
            Name = $agent.Name
            Status = "Skipped"
            Duration = "N/A"
        }
    }
    
    Write-Host ""
}

# Final summary
$overallEndTime = Get-Date
$totalDuration = ($overallEndTime - $overallStartTime).TotalMinutes

Write-Host "================================================" -ForegroundColor Green
Write-Host "  BRD Pipeline Execution Summary" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

$results | Format-Table -AutoSize

Write-Host ""
Write-Host "Total Duration: $($totalDuration.ToString('F2')) minutes" -ForegroundColor Cyan
Write-Host "Output Directory: $kbRepoDir" -ForegroundColor Cyan
Write-Host ""

# Check for final BRD
$finalBrd = Join-Path $kbRepoDir "final_brd.md"
if (Test-Path $finalBrd) {
    Write-Host "Final BRD generated: $finalBrd" -ForegroundColor Green
} else {
    Write-Warning "Final BRD not found - check Agent 8 output"
}

Write-Host ""
Write-Host "BRD Pipeline Complete!" -ForegroundColor Green
