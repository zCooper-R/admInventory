# ============================================================
# IT Inventory Agent — PowerShell
# ============================================================
# Collects hardware info from this Windows PC and sends it
# to the IT Inventory system via the /api/v1/devices/sync/ API.
#
# Configuration: edit the variables in the CONFIGURATION block below.
# ============================================================

# -- CONFIGURATION --------------------------------------------
$API_URL   = "http://127.0.0.1:8000/api/v1/devices/sync/"
$API_KEY   = "demo-agent-key-change-in-production"
$LOCATION_ID = $null          # optional: set to your Location ID (integer) from the system
$LOG_FILE  = "$env:TEMP\it_inventory_agent.log"
# -------------------------------------------------------------

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LOG_FILE -Value "[$ts] $msg" -Encoding UTF8
    Write-Host "[$ts] $msg"
}

Write-Log "Starting IT Inventory Agent..."

# -- Collect system information --------------------------------
try {
    $cpu = (Get-WmiObject Win32_Processor | Select-Object -First 1).Name.Trim()
} catch { $cpu = "Unknown" }

try {
    $ramBytes = (Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory
    $ramGB    = [math]::Round($ramBytes / 1GB)
} catch { $ramGB = $null }

try {
    $os = (Get-WmiObject Win32_OperatingSystem).Caption.Trim()
} catch { $os = "Unknown" }

try {
    $sn = (Get-WmiObject Win32_BIOS).SerialNumber.Trim()
    # Some vendors return "Default string" or similar junk
    if ($sn -match "Default|To be filled|None|System Serial") { $sn = "" }
} catch { $sn = "" }

try {
    $disk     = Get-PhysicalDisk | Select-Object -First 1
    $diskSize = [math]::Round($disk.Size / 1GB)
    $ssdCount = (Get-PhysicalDisk | Where-Object MediaType -eq 'SSD').Count
    $hddCount = (Get-PhysicalDisk | Where-Object MediaType -eq 'HDD').Count
    if ($ssdCount -gt 0 -and $hddCount -gt 0) { $storageType = "Mixed" }
    elseif ($ssdCount -gt 0)                   { $storageType = "SSD"   }
    else                                        { $storageType = "HDD"  }
} catch {
    try {
        $disk = Get-WmiObject Win32_DiskDrive | Select-Object -First 1
        $diskSize = [math]::Round($disk.Size / 1GB)
    } catch { $diskSize = $null }
    $storageType = "HDD"
}

$hostname = $env:COMPUTERNAME
$invNumber = "AUTO-$hostname"

Write-Log "Hostname: $hostname | CPU: $cpu | RAM: ${ramGB}GB | Storage: ${storageType} ${diskSize}GB | OS: $os"

# -- Build payload ---------------------------------------------
$payload = @{
    inventory_number = $invNumber
    name             = $hostname
    hostname         = $hostname
    cpu              = $cpu
    ram              = $ramGB
    os               = $os
    storage_type     = $storageType
    storage_size     = $diskSize
    serial_number    = $sn
}

if ($LOCATION_ID) {
    $payload.location_id = $LOCATION_ID
}

$body    = $payload | ConvertTo-Json -Depth 2
$headers = @{
    "X-Api-Key"    = $API_KEY
    "Content-Type" = "application/json"
}

# -- Send to API -----------------------------------------------
try {
    $response = Invoke-RestMethod -Uri $API_URL -Method POST -Body $body -Headers $headers -TimeoutSec 30
    $action   = if ($response.created) { "CREATED" } else { "UPDATED" }
    Write-Log "SUCCESS ($action): Device ID $($response.device.id)"
} catch {
    $err = $_.Exception.Message
    Write-Log "ERROR: $err"
    exit 1
}
