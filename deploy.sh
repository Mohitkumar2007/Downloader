#!/bin/bash

# YouTube Video Downloader Docker Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Function to deploy development version
deploy_dev() {
    print_status "Deploying YouTube Video Downloader (Development)..."
    
    # Stop existing containers
    docker-compose down 2>/dev/null || true
    
    # Build and start
    docker-compose up -d --build
    
    print_success "Development deployment completed!"
    print_status "Application is running at: http://localhost:8501"
}

# Function to deploy production version
deploy_prod() {
    print_status "Deploying YouTube Video Downloader (Production)..."
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Build and start production version
    docker-compose -f docker-compose.prod.yml up -d --build
    
    print_success "Production deployment completed!"
    print_status "Application is running at: http://localhost:8501"
    print_status "With Nginx proxy at: http://localhost:80"
}

# Function to show status
show_status() {
    print_status "Container Status:"
    docker-compose ps 2>/dev/null || docker-compose -f docker-compose.prod.yml ps 2>/dev/null || print_warning "No containers running"
    
    echo ""
    print_status "Application Logs (last 10 lines):"
    docker-compose logs --tail=10 youtube-downloader 2>/dev/null || \
    docker-compose -f docker-compose.prod.yml logs --tail=10 youtube-downloader 2>/dev/null || \
    print_warning "No logs available"
}

# Function to stop all containers
stop_all() {
    print_status "Stopping all YouTube Downloader containers..."
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_success "All containers stopped"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down --rmi all --volumes --remove-orphans 2>/dev/null || true
    docker system prune -f
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "YouTube Video Downloader Docker Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev         Deploy development version (default)"
    echo "  prod        Deploy production version with Nginx"
    echo "  status      Show container status and logs"
    echo "  stop        Stop all containers"
    echo "  restart     Restart the application"
    echo "  cleanup     Stop containers and clean up resources"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev      # Deploy for development"
    echo "  $0 prod     # Deploy for production"
    echo "  $0 status   # Check status"
}

# Main script logic
case "${1:-dev}" in
    "dev")
        check_docker
        deploy_dev
        ;;
    "prod")
        check_docker
        deploy_prod
        ;;
    "status")
        show_status
        ;;
    "stop")
        stop_all
        ;;
    "restart")
        stop_all
        sleep 2
        check_docker
        deploy_dev
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac