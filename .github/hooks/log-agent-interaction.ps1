# Agent Interaction Logger
# Logs all agent interactions, tool executions, and HITL events

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('pre_agent', 'post_agent', 'hitl_trigger', 'error')]
    [string]$HookType,
    
    [Parameter(Mandatory=$false)]
    [string]$AgentName,
    
    [Parameter(Mandatory=$false)]
    [hashtable]$Context,
    
    [Parameter(Mandatory=$false)]
    [string]$LogPath = ".\kb_store\logs\agent_interactions.log"
)

# Ensure log directory exists
$logDir = Split-Path -Parent $LogPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Build log entry
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
$logEntry = @{
    timestamp = $timestamp
    hook_type = $HookType
    agent_name = $AgentName
    context = $Context
}

# Convert to JSON and append to log file
$logJson = $logEntry | ConvertTo-Json -Compress -Depth 10
Add-Content -Path $LogPath -Value $logJson

# Also write to console for visibility
Write-Host "[$timestamp] $HookType - $AgentName" -ForegroundColor Cyan

# Hook-specific actions
switch ($HookType) {
    'pre_agent' {
        Write-Host "  Starting agent execution..." -ForegroundColor Green
        # Could add pre-execution validation here
    }
    'post_agent' {
        Write-Host "  Agent execution completed" -ForegroundColor Green
        if ($Context -and $Context.ContainsKey('confidence')) {
            $confidence = $Context.confidence
            $color = if ($confidence -gt 0.8) { 'Green' } elseif ($confidence -gt 0.6) { 'Yellow' } else { 'Red' }
            Write-Host "  Confidence: $confidence" -ForegroundColor $color
        }
    }
    'hitl_trigger' {
        Write-Host "  HITL interaction required" -ForegroundColor Yellow
        if ($Context -and $Context.ContainsKey('trigger_reason')) {
            Write-Host "  Reason: $($Context.trigger_reason)" -ForegroundColor Yellow
        }
    }
    'error' {
        Write-Host "  ERROR occurred" -ForegroundColor Red
        if ($Context -and $Context.ContainsKey('error_message')) {
            Write-Host "  Message: $($Context.error_message)" -ForegroundColor Red
        }
    }
}

# Return success
exit 0
