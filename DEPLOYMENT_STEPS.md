# 🚀 YouTube Video Downloader - Docker Deployment Steps

## Prerequisites

### 1. Install Docker
**Windows:**
- Download Docker Desktop from https://docker.com/products/docker-desktop
- Run the installer and follow the setup wizard
- Restart your computer when prompted
- Verify installation: `docker --version`

**Linux (Ubuntu/Debian):**
```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

**macOS:**
- Download Docker Desktop from https://docker.com/products/docker-desktop
- Drag Docker to Applications folder
- Launch Docker from Applications
- Verify installation: `docker --version`

### 2. Clone the Repository
```bash
git clone https://github.com/Mohitkumar2007/Downloader.git
cd Downloader
```

---

## 🎯 Deployment Options

## Option 1: Quick Start (Easiest)

### Step 1: Start the Application
```bash
# Development mode (recommended for testing)
docker-compose up -d

# Or production mode (with Nginx proxy)
docker-compose -f docker-compose.prod.yml up -d
```

### Step 2: Access Your App
- Open browser and go to: **http://localhost:8501**
- (Production mode also available at: http://localhost:80)

### Step 3: Check Status
```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f youtube-downloader
```

---

## Option 2: Using Deployment Scripts

### Windows PowerShell:
```powershell
# Make sure you're in the project directory
cd C:\path\to\Downloader

# Deploy in development mode
.\deploy.ps1 dev

# Or deploy in production mode
.\deploy.ps1 prod

# Check status
.\deploy.ps1 status

# Stop containers
.\deploy.ps1 stop
```

### Linux/macOS:
```bash
# Make script executable
chmod +x deploy.sh

# Deploy in development mode
./deploy.sh dev

# Or deploy in production mode
./deploy.sh prod

# Check status
./deploy.sh status

# Stop containers
./deploy.sh stop
```

---

## Option 3: Manual Docker Commands

### Step 1: Build the Image
```bash
# Build from Dockerfile
docker build -t youtube-downloader .

# Or build production version
docker build -f Dockerfile.prod -t youtube-downloader:prod .
```

### Step 2: Run Container
```bash
# Basic run
docker run -d \
  --name youtube-downloader-app \
  -p 8501:8501 \
  -v $(pwd)/downloads:/app/downloads \
  youtube-downloader

# Windows PowerShell equivalent
docker run -d `
  --name youtube-downloader-app `
  -p 8501:8501 `
  -v ${PWD}/downloads:/app/downloads `
  youtube-downloader
```

### Step 3: Access Application
- Open browser: **http://localhost:8501**

---

## 🔧 Configuration & Management

### Environment Variables
You can customize the deployment by modifying `docker-compose.yml`:

```yaml
environment:
  - STREAMLIT_SERVER_PORT=8501
  - STREAMLIT_SERVER_ADDRESS=0.0.0.0
  - STREAMLIT_SERVER_HEADLESS=true
  - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Volume Mounts
Downloads are persisted in the `downloads` folder:
```yaml
volumes:
  - ./downloads:/app/downloads  # Your downloads will be saved here
  - ./logs:/app/logs           # Application logs (optional)
```

### Port Configuration
To change the port, modify the `ports` section:
```yaml
ports:
  - "3000:8501"  # Access via http://localhost:3000
```

---

## 📊 Monitoring & Troubleshooting

### Check Container Status
```bash
# View all containers
docker ps

# View specific container logs
docker logs youtube-downloader-app

# Follow logs in real-time
docker logs -f youtube-downloader-app
```

### Health Check
```bash
# Manual health check
curl http://localhost:8501/_stcore/health

# Container health status
docker inspect youtube-downloader-app --format='{{.State.Health.Status}}'
```

### Resource Usage
```bash
# Monitor resource usage
docker stats youtube-downloader-app
```

---

## 🛠 Common Commands

### Start/Stop/Restart
```bash
# Stop containers
docker-compose down

# Start containers
docker-compose up -d

# Restart containers
docker-compose restart

# Rebuild and start
docker-compose up -d --build
```

### View Application
```bash
# View logs
docker-compose logs -f

# Execute commands inside container
docker-compose exec youtube-downloader bash

# View downloaded files
ls -la downloads/
```

### Cleanup
```bash
# Stop and remove containers, networks, images
docker-compose down --rmi all --volumes

# Remove all Docker resources (careful!)
docker system prune -a
```

---

## 🚀 Production Deployment

### For Production Environment:

1. **Use Production Docker Compose:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

2. **Enable SSL (Optional):**
   - Add your SSL certificates to `./ssl/` folder
   - Uncomment HTTPS section in `nginx.conf`
   - Update domain name in nginx configuration

3. **Set Resource Limits:**
   The production compose file includes resource limits:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: '0.5'
   ```

4. **Monitor with Health Checks:**
   ```bash
   # Check health status
   curl http://localhost/_stcore/health
   ```

---

## ❌ Troubleshooting

### Common Issues:

1. **Port Already in Use:**
   ```bash
   # Check what's using port 8501
   netstat -tulpn | grep 8501
   
   # Change port in docker-compose.yml
   ports:
     - "8502:8501"
   ```

2. **Permission Denied (Linux):**
   ```bash
   # Fix download folder permissions
   sudo chown -R $USER:$USER downloads/
   chmod 755 downloads/
   ```

3. **Container Won't Start:**
   ```bash
   # Check logs for errors
   docker-compose logs youtube-downloader
   
   # Rebuild without cache
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **FFmpeg Not Found:**
   ```bash
   # Rebuild image to ensure FFmpeg is installed
   docker-compose build --no-cache
   ```

5. **Out of Disk Space:**
   ```bash
   # Clean up unused Docker resources
   docker system prune -f
   docker volume prune -f
   ```

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start in development mode |
| `docker-compose -f docker-compose.prod.yml up -d` | Start in production mode |
| `docker-compose ps` | View container status |
| `docker-compose logs -f` | View logs |
| `docker-compose down` | Stop containers |
| `docker-compose restart` | Restart containers |
| `./deploy.sh status` | Check deployment status |
| `./deploy.ps1 cleanup` | Clean up all resources |

---

## 🌟 Success Indicators

✅ **Deployment Successful When:**
- Container status shows "Up" in `docker-compose ps`
- Health check returns "healthy"
- Application accessible at http://localhost:8501
- No error messages in logs
- Downloads folder is created and writable

🎉 **Your YouTube Video Downloader is now running in Docker!**

Access it at: **http://localhost:8501**