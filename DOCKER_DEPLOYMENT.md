# Docker Deployment Guide

This guide explains how to deploy the Instagram Automation Platform using Docker containers.

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 2.0 or later
- At least 4GB RAM and 20GB disk space
- Domain pointed to your server (for SSL)

## Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/AbdullahYounas0/instaAutomation.git
cd instaAutomation
```

2. **Create environment file:**
```bash
cp .env.example .env
```

3. **Update environment variables:**
Edit `.env` file with your production values:
```bash
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-production-jwt-secret
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

4. **Build and start containers:**
```bash
docker-compose up -d --build
```

5. **Check container status:**
```bash
docker-compose ps
docker-compose logs
```

## Container Architecture

### Backend Container (`insta-automation-backend`)
- **Base Image:** Python 3.11 slim
- **Purpose:** FastAPI application with Instagram automation
- **Port:** 5000
- **Features:**
  - Playwright browsers pre-installed
  - Non-root user for security
  - Health checks
  - Volume mounts for persistent data

### Frontend Container (`insta-automation-frontend`)
- **Base Image:** Node.js 18 Alpine (build) + Nginx Alpine (runtime)
- **Purpose:** React TypeScript frontend
- **Port:** 80
- **Features:**
  - Multi-stage build for optimization
  - Nginx reverse proxy to backend
  - Static file serving
  - Security headers

## Volume Mounts

The following directories are mounted for data persistence:

```
./backend/logs:/app/logs                           # Application logs
./backend/uploads:/app/uploads                     # File uploads
./backend/instagram_cookies:/app/instagram_cookies # Instagram sessions
./backend/browser_profiles:/app/browser_profiles   # Browser profiles
./backend/users.json:/app/users.json              # User data
./backend/instagram_accounts.json:/app/instagram_accounts.json # Instagram accounts
./backend/proxy_assignments.json:/app/proxy_assignments.json   # Proxy config
./backend/activity_logs.json:/app/activity_logs.json          # Activity logs
```

## Docker Commands

### Development
```bash
# Build and start in development mode
docker-compose up --build

# View logs
docker-compose logs -f

# Execute commands in running container
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Production
```bash
# Start in detached mode
docker-compose up -d --build

# Update containers
docker-compose pull
docker-compose up -d --build

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Maintenance
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ This will delete data)
docker-compose down -v

# View container stats
docker stats

# Clean up unused images
docker system prune -a
```

## Environment Variables

### Required Variables
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT token secret
- `CORS_ORIGINS` - Allowed CORS origins

### Optional Variables
- `INSTAGRAM_API_DELAY_MIN` - Minimum delay between API calls (default: 2)
- `INSTAGRAM_API_DELAY_MAX` - Maximum delay between API calls (default: 5)
- `PROXY_ROTATION_ENABLED` - Enable proxy rotation (default: true)
- `LOG_LEVEL` - Logging level (default: INFO)
- `MAX_CONCURRENT_SCRIPTS` - Maximum concurrent automation scripts (default: 5)

## SSL Configuration (Production)

For production with SSL, uncomment the nginx-proxy service in `docker-compose.yml` and:

1. **Create SSL certificates:**
```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

2. **Create SSL proxy configuration:**
```bash
# Create ssl-proxy.conf
cat > ssl-proxy.conf << EOF
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/certs/privkey.pem;
    
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://\$server_name\$request_uri;
}
EOF
```

3. **Update docker-compose.yml:**
```yaml
nginx-proxy:
  image: nginx:alpine
  container_name: nginx-proxy
  ports:
    - "443:443"
    - "80:80"
  volumes:
    - ./ssl-proxy.conf:/etc/nginx/conf.d/default.conf
    - /etc/letsencrypt/live/yourdomain.com/fullchain.pem:/etc/ssl/certs/fullchain.pem:ro
    - /etc/letsencrypt/live/yourdomain.com/privkey.pem:/etc/ssl/certs/privkey.pem:ro
  depends_on:
    - frontend
  restart: unless-stopped
```

## Monitoring and Logging

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

### Health Checks
Both containers include health checks:
- Backend: HTTP check on `/api/health`
- Frontend: HTTP check on port 80

### Container Stats
```bash
# Resource usage
docker stats

# Detailed container info
docker-compose exec backend ps aux
docker-compose exec backend df -h
```

## Troubleshooting

### Common Issues

1. **Port conflicts:**
```bash
# Check if ports are in use
netstat -tulpn | grep :80
netstat -tulpn | grep :5000

# Change ports in docker-compose.yml if needed
```

2. **Permission issues:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER ./backend/logs
sudo chown -R $USER:$USER ./backend/uploads
```

3. **Container won't start:**
```bash
# Check logs for errors
docker-compose logs backend
docker-compose logs frontend

# Check container status
docker-compose ps
```

4. **Playwright issues:**
```bash
# Rebuild backend container
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Debug Mode
```bash
# Run in debug mode
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up
```

## Security Considerations

1. **Use strong secrets:**
   - Generate random SECRET_KEY and JWT_SECRET_KEY
   - Never commit secrets to version control

2. **Network security:**
   - Use Docker's internal networking
   - Expose only necessary ports

3. **File permissions:**
   - Containers run as non-root users
   - Mounted volumes have proper permissions

4. **Regular updates:**
   - Keep Docker images updated
   - Monitor for security vulnerabilities

## Backup and Recovery

### Backup Data
```bash
# Create backup of persistent data
tar -czf backup-$(date +%Y%m%d).tar.gz \
  backend/logs \
  backend/uploads \
  backend/instagram_cookies \
  backend/browser_profiles \
  backend/*.json
```

### Restore Data
```bash
# Stop containers
docker-compose down

# Restore backup
tar -xzf backup-YYYYMMDD.tar.gz

# Start containers
docker-compose up -d
```

## Performance Optimization

1. **Resource limits:**
   Add to docker-compose.yml:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

2. **Log rotation:**
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Support

For issues and questions:
- Check container logs: `docker-compose logs`
- Review this guide's troubleshooting section
- Check Docker and Docker Compose documentation
- Ensure your system meets the prerequisites
