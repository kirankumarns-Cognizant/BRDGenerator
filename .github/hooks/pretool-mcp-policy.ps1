# Pre-Tool MCP Policy Enforcer
# Enforces Model Context Protocol (MCP) policies before tool execution

param(
    [Parameter(Mandatory=$true)]
    [string]$ToolName,
    
    [Parameter(Mandatory=$true)]
    [string]$AgentName,
    
    [Parameter(Mandatory=$false)]
    [hashtable]$ToolParameters,
    
    [Parameter(Mandatory=$false)]
    [string]$PolicyConfigPath = ".\config\config.yaml"
)

# Load policy configuration
function Get-ToolPolicy {
    param([string]$ConfigPath, [string]$Agent, [string]$Tool)
    
    # In a real implementation, this would parse config.yaml
    # For now, return a default policy structure
    return @{
        enabled = $true
        max_execution_time_seconds = 300
        requires_confirmation = $false
        allowed_resources = @()
        rate_limit_per_minute = 10
    }
}

# Validate tool execution
function Test-ToolPolicy {
    param($Policy, $Tool, $Agent, $Parameters)
    
    $violations = @()
    
    # Check if tool is enabled
    if (-not $Policy.enabled) {
        $violations += "Tool '$Tool' is disabled in configuration for agent '$Agent'"
    }
    
    # Check resource access if specified
    if ($Parameters -and $Parameters.ContainsKey('resource_path')) {
        $requestedPath = $Parameters.resource_path
        $allowed = $false
        foreach ($allowedPath in $Policy.allowed_resources) {
            if ($requestedPath -like "$allowedPath*") {
                $allowed = $true
                break
            }
        }
        if (-not $allowed -and $Policy.allowed_resources.Count -gt 0) {
            $violations += "Resource access to '$requestedPath' not allowed by policy"
        }
    }
    
    # Check rate limiting (simplified - would need state tracking in real implementation)
    # This is a placeholder for rate limit checking logic
    
    return $violations
}

# Main execution
Write-Host "Pre-Tool Policy Check: $ToolName for $AgentName" -ForegroundColor Cyan

$policy = Get-ToolPolicy -ConfigPath $PolicyConfigPath -Agent $AgentName -Tool $ToolName
$violations = Test-ToolPolicy -Policy $policy -Tool $ToolName -Agent $AgentName -Parameters $ToolParameters

if ($violations.Count -gt 0) {
    Write-Host "POLICY VIOLATIONS DETECTED:" -ForegroundColor Red
    foreach ($violation in $violations) {
        Write-Host "  - $violation" -ForegroundColor Red
    }
    
    # Log the violation
    $logEntry = @{
        timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff")
        tool = $ToolName
        agent = $AgentName
        violations = $violations
        action = "blocked"
    }
    
    $logPath = ".\kb_store\logs\policy_violations.log"
    $logDir = Split-Path -Parent $logPath
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    $logEntry | ConvertTo-Json -Compress | Add-Content -Path $logPath
    
    # Return error code
    exit 1
}

Write-Host "  Policy check passed" -ForegroundColor Green

# Check if confirmation required
if ($policy.requires_confirmation) {
    Write-Host "  Tool execution requires confirmation" -ForegroundColor Yellow
    $response = Read-Host "Proceed with $ToolName execution? (Y/N)"
    if ($response -ne 'Y' -and $response -ne 'y') {
        Write-Host "  Execution cancelled by user" -ForegroundColor Yellow
        exit 2
    }
}

# Log successful policy check
$logEntry = @{
    timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff")
    tool = $ToolName
    agent = $AgentName
    action = "approved"
}

$logPath = ".\kb_store\logs\tool_executions.log"
$logDir = Split-Path -Parent $logPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logEntry | ConvertTo-Json -Compress | Add-Content -Path $logPath

exit 0
