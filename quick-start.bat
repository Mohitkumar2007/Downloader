@echo off
echo.
echo ========================================
echo  YouTube Video Downloader - Quick Start
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from:
    echo https://docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not available
    echo Please ensure Docker Desktop is properly installed
    echo.
    pause
    exit /b 1
)

echo ✅ Docker is installed and ready
echo.

REM Ask user for deployment mode
echo Choose deployment mode:
echo 1. Development (recommended for testing)
echo 2. Production (with Nginx proxy)
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Starting YouTube Video Downloader in Development mode...
    echo.
    docker-compose down >nul 2>&1
    docker-compose up -d
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ Deployment successful!
        echo.
        echo 🌐 Your app is running at: http://localhost:8501
        echo 📁 Downloads will be saved to: %cd%\downloads
        echo.
        echo 💡 Useful commands:
        echo    View logs: docker-compose logs -f
        echo    Stop app:  docker-compose down
        echo    Restart:   docker-compose restart
        echo.
    ) else (
        echo.
        echo ❌ Deployment failed. Check the error messages above.
        echo.
    )
    
) else if "%choice%"=="2" (
    echo.
    echo 🚀 Starting YouTube Video Downloader in Production mode...
    echo.
    docker-compose -f docker-compose.prod.yml down >nul 2>&1
    docker-compose -f docker-compose.prod.yml up -d
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ Production deployment successful!
        echo.
        echo 🌐 Your app is running at:
        echo    - Direct access: http://localhost:8501
        echo    - Nginx proxy:   http://localhost:80
        echo 📁 Downloads will be saved to: %cd%\downloads
        echo.
        echo 💡 Useful commands:
        echo    View logs: docker-compose -f docker-compose.prod.yml logs -f
        echo    Stop app:  docker-compose -f docker-compose.prod.yml down
        echo.
    ) else (
        echo.
        echo ❌ Production deployment failed. Check the error messages above.
        echo.
    )
    
) else (
    echo.
    echo ❌ Invalid choice. Please run the script again and choose 1 or 2.
    echo.
)

echo.
echo Press any key to exit...
pause >nul