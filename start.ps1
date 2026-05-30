#Requires -Version 5.1
<#
.SYNOPSIS
    Starts the full GAME stack in development mode.

.DESCRIPTION
    First run: copies .env, builds Docker images and starts all services.
    Subsequent runs: starts services directly (no rebuild).

    Supports Docker installed in three ways (without requiring Docker Desktop):
      - Native Docker CLI in PATH (Rancher Desktop, any native installation)
      - Docker CLI in known installation paths
      - Docker Engine inside WSL2 (Ubuntu/Debian via apt)

.PARAMETER Force
    Forces a full rebuild of the images even if the environment is already initialized.

.PARAMETER Down
    Stops all containers and networks (does not remove volumes).

.PARAMETER Clean
    Stops containers AND removes data volumes (PostgreSQL, Keycloak, etc.).
    WARNING: deletes all persisted data.

.PARAMETER Logs
    Shows real-time logs after starting the services.

.PARAMETER Timeout
    Maximum seconds to wait for the API to be ready. Default: 300.

.EXAMPLE
    .\start.ps1                 # First run or normal start
    .\start.ps1 -Force          # Forced rebuild
    .\start.ps1 -Down           # Stop services
    .\start.ps1 -Clean          # Stop services + delete data
    .\start.ps1 -Logs           # Start and view logs
#>

param(
    [switch]$Force,
    [switch]$Down,
    [switch]$Clean,
    [switch]$Logs,
    [int]$Timeout = 300
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$COMPOSE_FILE   = "docker-compose-dev.yml"
$ENV_FILE       = ".env"
$ENV_SAMPLE     = ".env.sample"
$MARKER_FILE    = ".game_initialized"
$API_HEALTH_URL = "http://localhost:8000/api/v1/kpi"

# "native" | "wsl" — set in Check-Docker
$script:DockerMode = "native"

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "==> $Text" -ForegroundColor Cyan
}

function Write-Ok   { param([string]$Text); Write-Host "  [OK]  $Text" -ForegroundColor Green }
function Write-Warn { param([string]$Text); Write-Host "  [!]   $Text" -ForegroundColor Yellow }
function Write-Err  { param([string]$Text); Write-Host "  [ERR] $Text" -ForegroundColor Red }
function Write-Info { param([string]$Text); Write-Host "        $Text" -ForegroundColor Gray }

function Exit-WithError {
    param([string]$Message)
    Write-Err $Message
    exit 1
}

# ---------------------------------------------------------------------------
# Wrapper: runs docker regardless of whether it is native or WSL
# Usage: Invoke-Docker compose -f foo.yml up -d
#        Invoke-Docker info
# ---------------------------------------------------------------------------
function Invoke-Docker {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$ArgList)

    if ($script:DockerMode -eq "wsl") {
        # Convert the Windows project path to a WSL path (/mnt/...)
        $wslProjectPath = (wsl wslpath -u "$PSScriptRoot").Trim()
        # Build the full command for bash
        $escaped = $ArgList | ForEach-Object { $_ -replace "'", "'\\''"}
        $cmdStr = "cd '$wslProjectPath' && docker $($escaped -join ' ')"
        wsl bash -c $cmdStr
    } else {
        & docker @ArgList
    }
    return $LASTEXITCODE
}

# ---------------------------------------------------------------------------
# 1. Detect Docker (native -> known paths -> WSL)
# ---------------------------------------------------------------------------
function Check-Docker {
    Write-Header "Checking Docker"

    # --- Attempt 1: docker is already in PATH ---
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $script:DockerMode = "native"
        Write-Ok "docker found in PATH (native mode)"
    } else {
        # --- Attempt 2: common native installation paths ---
        $candidates = @(
            # Rancher Desktop
            "$env:LOCALAPPDATA\Programs\Rancher Desktop\resources\resources\win32\bin",
            # Docker Desktop (in case it is installed but not in PATH)
            "$env:ProgramFiles\Docker\Docker\resources\bin",
            "$env:LOCALAPPDATA\Programs\Docker\Docker\resources\bin"
        )
        $found = $false
        foreach ($dir in $candidates) {
            if (Test-Path "$dir\docker.exe") {
                $env:PATH = "$dir;$env:PATH"
                $script:DockerMode = "native"
                Write-Ok "docker.exe found in: $dir"
                $found = $true
                break
            }
        }

        if (-not $found) {
            # --- Attempt 3: Docker inside WSL2 ---
            Write-Info "docker not found natively, looking in WSL2..."
            $wslAvailable = Get-Command wsl -ErrorAction SilentlyContinue
            if ($wslAvailable) {
                $wslDockerPath = wsl which docker 2>&1
                if ($LASTEXITCODE -eq 0 -and "$wslDockerPath" -match "docker") {
                    $script:DockerMode = "wsl"
                    Write-Ok "Docker found in WSL2: $($wslDockerPath.Trim()) (WSL mode)"
                } else {
                    Write-Err "Docker is not available on Windows or in WSL2."
                    Write-Host ""
                    Write-Host "  Options to install Docker WITHOUT Docker Desktop:" -ForegroundColor White
                    Write-Host ""
                    Write-Host "  [A] Rancher Desktop (recommended - lightweight GUI, free):" -ForegroundColor Yellow
                    Write-Host "      winget install suse.RancherDesktop" -ForegroundColor Gray
                    Write-Host "      or download from https://rancherdesktop.io" -ForegroundColor Gray
                    Write-Host ""
                    Write-Host "  [B] Command line only via WSL2 + Docker Engine:" -ForegroundColor Yellow
                    Write-Host "      1. Enable WSL2:  wsl --install" -ForegroundColor Gray
                    Write-Host "      2. Open Ubuntu and run:" -ForegroundColor Gray
                    Write-Host "         sudo apt update && sudo apt install -y docker.io docker-compose-v2" -ForegroundColor DarkGray
                    Write-Host "         sudo usermod -aG docker `$USER" -ForegroundColor DarkGray
                    Write-Host "         sudo service docker start" -ForegroundColor DarkGray
                    Write-Host "      3. Run this script again" -ForegroundColor Gray
                    Write-Host ""
                    exit 1
                }
            } else {
                Write-Err "Docker not found and WSL2 is not available."
                Write-Host ""
                Write-Host "  Fastest option:" -ForegroundColor White
                Write-Host "    winget install suse.RancherDesktop" -ForegroundColor Yellow
                Write-Host "  Then open a new terminal and run this script again." -ForegroundColor Gray
                Write-Host ""
                exit 1
            }
        }
    }

    # --- Verify that the daemon is running ---
    $null = Invoke-Docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        if ($script:DockerMode -eq "wsl") {
            Write-Err "The Docker daemon is not running in WSL2."
            Write-Info "Inside WSL2, run: sudo service docker start"
            Write-Info "Or to start automatically: sudo systemctl enable docker"
        } else {
            Write-Err "Docker is not running."
            Write-Info "Open Rancher Desktop (or Docker Desktop) and wait until it is ready."
        }
        exit 1
    }
    Write-Ok "Docker daemon responding"

    # --- Verify docker compose v2 ---
    $null = Invoke-Docker compose version 2>&1
    if ($LASTEXITCODE -ne 0) {
        if ($script:DockerMode -eq "wsl") {
            Write-Err "docker compose (v2) not found in WSL2."
            Write-Info "Inside WSL2: sudo apt install -y docker-compose-v2"
        } else {
            Exit-WithError "Docker Compose v2 not found. Update Rancher Desktop."
        }
        exit 1
    }
    Write-Ok "Docker Compose v2 available  (mode: $($script:DockerMode))"
}

# ---------------------------------------------------------------------------
# 2. Ensure .env exists
# ---------------------------------------------------------------------------
function Ensure-EnvFile {
    Write-Header "Checking environment file (.env)"

    if (Test-Path $ENV_FILE) {
        Write-Ok ".env already exists"
        return
    }

    if (-not (Test-Path $ENV_SAMPLE)) {
        Exit-WithError "'$ENV_SAMPLE' not found. Run this script from the root of the GAME project."
    }

    Copy-Item $ENV_SAMPLE $ENV_FILE
    Write-Ok ".env created from $ENV_SAMPLE"
    Write-Host ""
    Write-Warn "ACTION REQUIRED: .env was created with default values."
    Write-Warn "For production or shared environments, change these values before continuing:"
    Write-Info "  - SECRET_KEY"
    Write-Info "  - DB_PASSWORD"
    Write-Info "  - KEYCLOAK_ADMIN_PASSWORD"
    Write-Info "  - KEYCLOAK_CLIENT_SECRET"
    Write-Info "  - KEYCLOAK_USER_WITH_ROLE_PASSWORD"
    Write-Info "  - KEYCLOAK_USER_NO_ROLE_PASSWORD"
    Write-Host ""
    Write-Host "  For local development the default values work without changes." -ForegroundColor White
}

# ---------------------------------------------------------------------------
# 3. First-time setup: build + up
# ---------------------------------------------------------------------------
function First-Run-Setup {
    Write-Header "First run: building Docker images"
    Write-Info "This may take several minutes the first time..."
    Write-Host ""

    Invoke-Docker compose -f $COMPOSE_FILE build
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError "Image build failed. Check the errors above."
    }
    Write-Ok "Images built"

    Write-Header "Starting services for the first time"
    Invoke-Docker compose -f $COMPOSE_FILE up -d
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError "Could not start the services."
    }

    Wait-ForApi

    # Only create the marker if everything went well
    Set-Content -Path $MARKER_FILE -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Write-Ok "Environment initialized (marker: $MARKER_FILE)"
}

# ---------------------------------------------------------------------------
# 4. Normal start: up only
# ---------------------------------------------------------------------------
function Normal-Start {
    Write-Header "Starting services"

    Invoke-Docker compose -f $COMPOSE_FILE up -d
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError "Could not start the services."
    }

    Wait-ForApi
}

# ---------------------------------------------------------------------------
# 5. Forced rebuild
# ---------------------------------------------------------------------------
function Force-Rebuild {
    Write-Header "Forced rebuild of Docker images"
    Write-Info "Stopping existing containers..."
    Invoke-Docker compose -f $COMPOSE_FILE down
    Write-Host ""

    Invoke-Docker compose -f $COMPOSE_FILE build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError "Build failed. Check the errors above."
    }
    Write-Ok "Images rebuilt"

    Write-Header "Starting services"
    Invoke-Docker compose -f $COMPOSE_FILE up -d
    if ($LASTEXITCODE -ne 0) {
        Exit-WithError "Could not start the services."
    }

    Wait-ForApi
    Set-Content -Path $MARKER_FILE -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Write-Ok "Environment re-initialized"
}

# ---------------------------------------------------------------------------
# 6. Wait for the API to be ready
# ---------------------------------------------------------------------------
function Wait-ForApi {
    Write-Header "Waiting for the API to be ready"
    Write-Info "URL: $API_HEALTH_URL"
    Write-Info "Timeout: $Timeout seconds"
    Write-Host ""

    $elapsed  = 0
    $interval = 5
    $spinnerChars = @('|', '/', '-', '\')
    $spinnerIdx   = 0

    while ($elapsed -lt $Timeout) {
        try {
            $response = Invoke-WebRequest -Uri $API_HEALTH_URL -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                Write-Host ""
                Write-Ok "API ready (responded in $elapsed seconds)"
                return
            }
        } catch {
            # Not responding yet, keep waiting
        }

        $spinner = $spinnerChars[$spinnerIdx % $spinnerChars.Length]
        Write-Host "`r  $spinner  Waiting... ${elapsed}s" -NoNewline -ForegroundColor DarkGray
        $spinnerIdx++
        Start-Sleep -Seconds $interval
        $elapsed += $interval
    }

    Write-Host ""
    Write-Warn "The API did not respond within $Timeout seconds."
    Write-Warn "Services may still be starting. Check the logs:"
    Write-Info "  Invoke-Docker compose -f $COMPOSE_FILE logs -f api"
}

# ---------------------------------------------------------------------------
# 7. Show service URLs
# ---------------------------------------------------------------------------
function Show-ServiceUrls {
    Write-Host ""
    Write-Host "  ----------------------------------------" -ForegroundColor DarkGray
    Write-Host "   GAME - Available services" -ForegroundColor White
    Write-Host "  ----------------------------------------" -ForegroundColor DarkGray
    Write-Host "   API (Swagger):  " -NoNewline -ForegroundColor Gray;  Write-Host "http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
    Write-Host "   Dashboard:      " -NoNewline -ForegroundColor Gray;  Write-Host "http://localhost:3000" -ForegroundColor Cyan
    Write-Host "   Keycloak:       " -NoNewline -ForegroundColor Gray;  Write-Host "http://localhost:8080" -ForegroundColor Cyan
    Write-Host "   Grafana:        " -NoNewline -ForegroundColor Gray;  Write-Host "http://localhost:3001  (admin/admin)" -ForegroundColor Cyan
    Write-Host "   Prometheus:     " -NoNewline -ForegroundColor Gray;  Write-Host "http://localhost:9090" -ForegroundColor Cyan
    Write-Host "  ----------------------------------------" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Useful commands:" -ForegroundColor Gray
    Write-Host "    .\start.ps1 -Logs    # View real-time logs" -ForegroundColor DarkGray
    Write-Host "    .\start.ps1 -Down    # Stop services" -ForegroundColor DarkGray
    Write-Host "    .\start.ps1 -Force   # Full rebuild" -ForegroundColor DarkGray
    Write-Host "    .\start.ps1 -Clean   # Stop + delete data (CAUTION)" -ForegroundColor DarkGray
    Write-Host ""
}

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

# Change to the script directory so relative paths work
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "  ======================================" -ForegroundColor DarkCyan
Write-Host "   GAME - Goals And Motivation Engine" -ForegroundColor Cyan
Write-Host "  ======================================" -ForegroundColor DarkCyan

# Check Docker first (needed for Down and Clean as well)
Check-Docker

# --- Stop services ---
if ($Down) {
    Write-Header "Stopping services"
    Invoke-Docker compose -f $COMPOSE_FILE down
    if ($LASTEXITCODE -ne 0) { Exit-WithError "Error stopping services." }
    Write-Ok "Services stopped"
    exit 0
}

# --- Full cleanup ---
if ($Clean) {
    Write-Host ""
    Write-Warn "WARNING: this will delete all persisted data (PostgreSQL, Keycloak, etc.)"
    $confirm = Read-Host "  Type 'yes' to confirm"
    if ($confirm -ne "yes") {
        Write-Info "Operation cancelled."
        exit 0
    }
    Write-Header "Stopping services and removing volumes"
    Invoke-Docker compose -f $COMPOSE_FILE down -v
    if ($LASTEXITCODE -ne 0) { Exit-WithError "Error during cleanup." }
    if (Test-Path $MARKER_FILE) { Remove-Item $MARKER_FILE }
    Write-Ok "Environment cleaned. The next start will be like a first run."
    exit 0
}

Ensure-EnvFile

if ($Force) {
    Force-Rebuild
} elseif (-not (Test-Path $MARKER_FILE)) {
    First-Run-Setup
} else {
    $initDate = Get-Content $MARKER_FILE -Raw
    Write-Header "Environment already initialized"
    Write-Info "Initialized on: $($initDate.Trim())"
    Normal-Start
}

Show-ServiceUrls

if ($Logs) {
    Write-Header "Showing logs (Ctrl+C to exit)"
    Invoke-Docker compose -f $COMPOSE_FILE logs -f
}
