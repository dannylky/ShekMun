<#
.SYNOPSIS
    Safely changes a monitoring config value: bumps the config version,
    appends a CHANGELOG.md entry, and commits the change to git.

.DESCRIPTION
    Use this instead of editing config.json by hand so every change is
    versioned and traceable. Supported properties (top-level of
    config.json):
      masterIntervalSeconds, jitterFraction, minIntervalSeconds,
      timeoutMs, logRetentionDays

.EXAMPLE
    .\update-config.ps1 -Property masterIntervalSeconds -Value 15 -Message "Switch to 15s master interval"
    .\update-config.ps1 -Property jitterFraction -Value 0.3 -Message "Reduce jitter to 30%" -Minor
    .\update-config.ps1 -Property timeoutMs -Value 5000 -Message "Longer ping timeout" -NoCommit
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('masterIntervalSeconds', 'jitterFraction', 'minIntervalSeconds', 'timeoutMs', 'logRetentionDays')]
    [string]$Property,

    [Parameter(Mandatory = $true)]
    [string]$Value,

    [Parameter(Mandatory = $true)]
    [string]$Message,

    [switch]$Minor,
    [switch]$Major,
    [switch]$NoCommit
)

$ErrorActionPreference = 'Stop'

$configPath = Join-Path $PSScriptRoot 'config.json'
$changelogPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'CHANGELOG.md'
$rootDir = Split-Path $PSScriptRoot -Parent

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$oldValue = $config.$Property

# --------------------------------------------------------- validation ----
$numericProps = @('masterIntervalSeconds', 'jitterFraction', 'minIntervalSeconds', 'timeoutMs', 'logRetentionDays')
if ($Property -in $numericProps) {
    if ($Value -notmatch '^[0-9]+(\.[0-9]+)?$') { throw "Property '$Property' expects a numeric value, got '$Value'" }
    $num = [double]$Value
    if ($Property -eq 'jitterFraction' -and ($num -lt 0 -or $num -gt 1)) { throw 'jitterFraction must be between 0 and 1' }
    if ($Property -eq 'masterIntervalSeconds' -and $num -lt 1) { throw 'masterIntervalSeconds must be >= 1' }
    if ($Property -eq 'minIntervalSeconds' -and $num -lt 1) { throw 'minIntervalSeconds must be >= 1' }
    if ($Property -eq 'timeoutMs' -and $num -lt 100) { throw 'timeoutMs must be >= 100' }
    if ($Property -eq 'logRetentionDays' -and $num -lt 1) { throw 'logRetentionDays must be >= 1' }
    if ($Property -eq 'minIntervalSeconds' -and $num -gt $config.masterIntervalSeconds) {
        throw "minIntervalSeconds ($num) cannot exceed masterIntervalSeconds ($($config.masterIntervalSeconds))"
    }
    $newValue = $num
} else {
    $newValue = $Value
}

if ($oldValue -eq $newValue) { Write-Host "No change: $Property already equals $newValue"; exit 0 }

# --------------------------------------------------------- version bump ---
$parts = ($config.version -split '\.')
if ($Major) { $newVersion = "$([int]$parts[0] + 1).0.0" }
elseif ($Minor) { $newVersion = "$($parts[0]).$([int]$parts[1] + 1).0" }
else { $newVersion = "$($parts[0]).$($parts[1]).$([int]$parts[2] + 1)" }

$config.version = $newVersion
$config.$Property = $newValue
$config | ConvertTo-Json -Depth 5 | Set-Content -Path $configPath -Encoding UTF8

Write-Host "config.json updated: $Property = $oldValue -> $newValue (v$newVersion)"

# -------------------------------------------------------------- changelog --
$entry = @"

## [$newVersion] - $(Get-Date -Format 'yyyy-MM-dd')
- **$Property**: $oldValue -> $newValue - $Message

"@
if (Test-Path $changelogPath) {
    $content = Get-Content $changelogPath -Raw
    $content = $content.Replace("`n## [", "$entry`n## [")
    Set-Content -Path $changelogPath -Value $content -Encoding UTF8
} else {
    Set-Content -Path $changelogPath -Value "# Changelog`n$entry" -Encoding UTF8
}

# ------------------------------------------------------------------ git --
if (-not $NoCommit) {
    git -C $rootDir add "monitoring/config.json" CHANGELOG.md
    if ($LASTEXITCODE -ne 0) { throw 'git add failed - aborting' }
    git -C $rootDir commit -m "config: $Property = $newValue (v$newVersion) - $Message"
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }
    Write-Host "Committed: config $Property = $value (v$newVersion)"
}
