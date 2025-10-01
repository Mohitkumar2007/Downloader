#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${CYAN}========================================"
    echo -e " YouTube Video Downloader - Quick Start"
    echo -e "========================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}🚀 $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}💡 $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo
        echo "Please install Docker first:"
        echo "- Ubuntu/Debian: sudo apt install docker.io docker-compose"
        echo "- macOS: Download Docker Desktop from https://docker.com/products/docker-desktop"
        echo "- CentOS/RHEL: sudo yum install docker docker-compose"
        echo
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo
        echo "Please install Docker Compose:"
        echo "sudo apt install docker-compose  # Ubuntu/Debian"
        echo "Or download from: https://docs.docker.com/compose/install/"
        echo
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Main deployment function
deploy_app() {
    print_header
    
    # Check Docker installation
    check_docker
    echo
    
    # Ask user for deployment mode
    echo "Choose deployment mode:"
    echo "1. Development (recommended for testing)"
    echo "2. Production (with Nginx proxy)"
    echo
    read -p "Enter your choice (1 or 2): " choice
    echo
    
    case $choice in
        1)
            print_info "Starting YouTube Video Downloader in Development mode..."
            echo
            
            # Stop any existing containers
            docker-compose down 2>/dev/null || true
            
            # Start development deployment
            if docker-compose up -d; then
                echo
                print_success "Deployment successful!"
                echo
                echo -e "${CYAN}🌐 Your app is running at: http://localhost:8501${NC}"
                echo -e "${CYAN}📁 Downloads will be saved to: $(pwd)/downloads${NC}"
                echo
                print_warning "Useful commands:"
                echo "   View logs: docker-compose logs -f"
                echo "   Stop app:  docker-compose down"
                echo "   Restart:   docker-compose restart"
                echo
            else
                echo
                print_error "Deployment failed. Check the error messages above."
                exit 1
            fi
            ;;
            
        2)
            print_info "Starting YouTube Video Downloader in Production mode..."
            echo
            
            # Stop any existing containers
            docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
            
            # Start production deployment
            if docker-compose -f docker-compose.prod.yml up -d; then
                echo
                print_success "Production deployment successful!"
                echo
                echo -e "${CYAN}🌐 Your app is running at:${NC}"
                echo "   - Direct access: http://localhost:8501"
                echo "   - Nginx proxy:   http://localhost:80"
                echo -e "${CYAN}📁 Downloads will be saved to: $(pwd)/downloads${NC}"
                echo
                print_warning "Useful commands:"
                echo "   View logs: docker-compose -f docker-compose.prod.yml logs -f"
                echo "   Stop app:  docker-compose -f docker-compose.prod.yml down"
                echo
            else
                echo
                print_error "Production deployment failed. Check the error messages above."
                exit 1
            fi
            ;;
            
        *)
            echo
            print_error "Invalid choice. Please run the script again and choose 1 or 2."
            exit 1
            ;;
    esac
}

# Run the deployment
deploy_app