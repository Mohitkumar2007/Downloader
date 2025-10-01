# YouTube Video Downloader Docker Deployment Script for Windows
param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "prod", "status", "stop", "restart", "cleanup", "help")]
    [string]$Command = "dev"
)

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

function Test-Docker {
    try {
        $null = docker --version
        $null = docker-compose --version
        Write-Success "Docker and Docker Compose are installed"
        return $true
    }
    catch {
        Write-Error "Docker or Docker Compose is not installed or not in PATH"
        Write-Status "Please install Docker Desktop for Windows"
        return $false
    }
}

function Deploy-Dev {
    Write-Status "Deploying YouTube Video Downloader (Development)..."
    
    # Stop existing containers
    try {
        docker-compose down 2>$null
    }
    catch {
        # Ignore errors if no containers are running
    }
    
    # Build and start
    docker-compose up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Development deployment completed!"
        Write-Status "Application is running at: http://localhost:8501"
    }
    else {
        Write-Error "Deployment failed with exit code $LASTEXITCODE"
    }
}

function Deploy-Prod {
    Write-Status "Deploying YouTube Video Downloader (Production)..."
    
    # Stop existing containers
    try {
        docker-compose -f docker-compose.prod.yml down 2>$null
    }
    catch {
        # Ignore errors if no containers are running
    }
    
    # Build and start production version
    docker-compose -f docker-compose.prod.yml up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Production deployment completed!"
        Write-Status "Application is running at: http://localhost:8501"
        Write-Status "With Nginx proxy at: http://localhost:80"
    }
    else {
        Write-Error "Production deployment failed with exit code $LASTEXITCODE"
    }
}

function Show-Status {
    Write-Status "Container Status:"
    
    try {
        docker-compose ps
    }
    catch {
        try {
            docker-compose -f docker-compose.prod.yml ps
        }
        catch {
            Write-Warning "No containers running"
        }
    }
    
    Write-Host ""
    Write-Status "Application Logs (last 10 lines):"
    
    try {
        docker-compose logs --tail=10 youtube-downloader
    }
    catch {
        try {
            docker-compose -f docker-compose.prod.yml logs --tail=10 youtube-downloader
        }
        catch {
            Write-Warning "No logs available"
        }
    }
}

function Stop-All {
    Write-Status "Stopping all YouTube Downloader containers..."
    
    try {
        docker-compose down 2>$null
    }
    catch {
        # Ignore errors
    }
    
    try {
        docker-compose -f docker-compose.prod.yml down 2>$null
    }
    catch {
        # Ignore errors
    }
    
    Write-Success "All containers stopped"
}

function Clean-Up {
    Write-Status "Cleaning up Docker resources..."
    
    try {
        docker-compose down --rmi all --volumes --remove-orphans 2>$null
    }
    catch {
        # Ignore errors
    }
    
    try {
        docker-compose -f docker-compose.prod.yml down --rmi all --volumes --remove-orphans 2>$null
    }
    catch {
        # Ignore errors
    }
    
    docker system prune -f
    Write-Success "Cleanup completed"
}

function Show-Help {
    Write-Host "YouTube Video Downloader Docker Deployment Script" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 [COMMAND]" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor $Colors.White
    Write-Host "  dev         Deploy development version (default)" -ForegroundColor $Colors.White
    Write-Host "  prod        Deploy production version with Nginx" -ForegroundColor $Colors.White
    Write-Host "  status      Show container status and logs" -ForegroundColor $Colors.White
    Write-Host "  stop        Stop all containers" -ForegroundColor $Colors.White
    Write-Host "  restart     Restart the application" -ForegroundColor $Colors.White
    Write-Host "  cleanup     Stop containers and clean up resources" -ForegroundColor $Colors.White
    Write-Host "  help        Show this help message" -ForegroundColor $Colors.White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 dev      # Deploy for development" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 prod     # Deploy for production" -ForegroundColor $Colors.White
    Write-Host "  .\deploy.ps1 status   # Check status" -ForegroundColor $Colors.White
}

# Main script logic
switch ($Command) {
    "dev" {
        if (Test-Docker) {
            Deploy-Dev
        }
    }
    "prod" {
        if (Test-Docker) {
            Deploy-Prod
        }
    }
    "status" {
        Show-Status
    }
    "stop" {
        Stop-All
    }
    "restart" {
        Stop-All
        Start-Sleep -Seconds 2
        if (Test-Docker) {
            Deploy-Dev
        }
    }
    "cleanup" {
        Clean-Up
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
    }
}