# 🐳 Docker Deployment Guide for YouTube Video Downloader

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mohitkumar2007/Downloader.git
   cd Downloader
   ```

2. **Start the application:**
   ```bash
   docker-compose up -d
   ```

3. **Access the app:**
   Open your browser and go to `http://localhost:8501`

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t youtube-downloader .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name youtube-downloader-app \
     -p 8501:8501 \
     -v $(pwd)/downloads:/app/downloads \
     youtube-downloader
   ```

## 🔧 Configuration

### Environment Variables

You can customize the deployment using environment variables:

```yaml
environment:
  - STREAMLIT_SERVER_PORT=8501
  - STREAMLIT_SERVER_ADDRESS=0.0.0.0
  - STREAMLIT_SERVER_HEADLESS=true
  - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Volume Mounts

- `./downloads:/app/downloads` - Persist downloaded files
- `./logs:/app/logs` - Store application logs (optional)

### Port Configuration

By default, the app runs on port 8501. To change:

```yaml
ports:
  - "3000:8501"  # Access via http://localhost:3000
```

## 🚀 Production Deployment

### Docker Swarm

```bash
# Initialize swarm (if not already done)
docker swarm init

# Deploy the stack
docker stack deploy -c docker-compose.yml youtube-downloader
```

### Kubernetes

Create a deployment file `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: youtube-downloader
spec:
  replicas: 2
  selector:
    matchLabels:
      app: youtube-downloader
  template:
    metadata:
      labels:
        app: youtube-downloader
    spec:
      containers:
      - name: youtube-downloader
        image: your-registry/youtube-downloader:latest
        ports:
        - containerPort: 8501
        volumeMounts:
        - name: downloads-volume
          mountPath: /app/downloads
      volumes:
      - name: downloads-volume
        persistentVolumeClaim:
          claimName: downloads-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: youtube-downloader-service
spec:
  selector:
    app: youtube-downloader
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f k8s-deployment.yaml
```

## 🔍 Monitoring & Debugging

### View logs:
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f youtube-downloader-app
```

### Health Check:
The container includes a health check endpoint:
```bash
curl http://localhost:8501/_stcore/health
```

### Resource Monitoring:
```bash
# Monitor container resources
docker stats youtube-downloader-app
```

## 🛠 Troubleshooting

### Common Issues:

1. **Port already in use:**
   ```bash
   # Change the port in docker-compose.yml
   ports:
     - "8502:8501"
   ```

2. **Permission issues with downloads:**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER downloads/
   ```

3. **FFmpeg not found:**
   The Dockerfile includes FFmpeg installation. If issues persist, rebuild:
   ```bash
   docker-compose build --no-cache
   ```

### Performance Tuning:

Add resource limits in docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

## 🔒 Security Considerations

1. **Run as non-root user:**
   Add to Dockerfile:
   ```dockerfile
   RUN useradd -m -u 1001 appuser
   USER appuser
   ```

2. **Use specific tags:**
   ```dockerfile
   FROM python:3.9.18-slim
   ```

3. **Scan for vulnerabilities:**
   ```bash
   docker scan youtube-downloader:latest
   ```

## 📊 Features in Docker

✅ **Included:**
- Full YouTube download functionality
- FFmpeg for video processing
- Streamlit web interface
- Anti-detection measures
- Persistent downloads folder
- Health checks
- Auto-restart on failure

✅ **Optimized for:**
- Fast startup time
- Minimal image size
- Production deployment
- Easy scaling
- Container orchestration

## 🎯 Next Steps

1. **Custom Domain:** Set up reverse proxy (nginx/traefik)
2. **HTTPS:** Add SSL certificates
3. **Scaling:** Use load balancer for multiple instances
4. **Monitoring:** Add Prometheus/Grafana
5. **Backup:** Schedule download folder backups