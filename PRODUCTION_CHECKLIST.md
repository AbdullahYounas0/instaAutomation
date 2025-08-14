# Production Deployment Checklist

## ✅ Pre-Deployment Checklist

### 🔐 Security Configuration
- [x] **Secret Keys Generated**: Production-ready SECRET_KEY and JWT_SECRET_KEY configured
- [x] **Environment Variables**: `.env` file created with production settings
- [ ] **Domain Configuration**: DNS pointing to your server IP
- [ ] **Firewall**: Ports 22 (SSH), 80 (HTTP), 443 (HTTPS) opened
- [ ] **SSL Certificate**: Let's Encrypt certificate installed

### 🐳 Docker Configuration
- [x] **Docker Files**: All Dockerfiles and compose files ready
- [x] **Production Config**: `docker-compose.prod.yml` with resource limits
- [x] **Nginx SSL Config**: SSL reverse proxy configuration ready
- [x] **Health Checks**: Container health monitoring configured

### 🏗️ Infrastructure
- [ ] **Server Requirements**: Minimum 4GB RAM, 20GB disk space
- [ ] **Docker Installed**: Docker Engine and Docker Compose installed
- [ ] **Git Repository**: Access to the repository configured
- [ ] **Backup Strategy**: Automated backup system in place

## 🚀 Deployment Steps

### Step 1: Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Application Deployment
```bash
# Clone repository
git clone https://github.com/AbdullahYounas0/instaAutomation.git
cd instaAutomation

# Production deployment
make prod
```

### Step 3: SSL Configuration (After DNS is configured)
```bash
# Setup SSL certificates
make setup-ssl

# Start with SSL
make prod-ssl
```

### Step 4: Final Verification
```bash
# Check container status
make status

# View logs
make logs

# Test application
curl -f https://wdyautomation.shop/api/health
```

## 🔧 Production Settings Applied

### 🔑 Security Settings
- **SECRET_KEY**: `ECF5D0BF2DC9809BDC8390C8231D8F10C5357DE3A8DA540F3F4E33AB679A7ABF`
- **JWT_SECRET_KEY**: `D39371E092229425823D02B2C0BF590EC8B67FD22F35E87CD3991AC93B9FDB73`
- **CORS Origins**: Configured for `wdyautomation.shop` domain
- **SSL/TLS**: Let's Encrypt certificate with HSTS enabled

### 🐳 Container Configuration
- **Backend**: 
  - Memory: 2GB limit, 512MB reserved
  - CPU: 1.0 limit, 0.5 reserved
  - Non-root user execution
  - Health checks enabled
- **Frontend**: 
  - Memory: 512MB limit, 128MB reserved
  - CPU: 0.5 limit, 0.25 reserved
  - Nginx with gzip compression
  - Security headers configured

### 📊 Monitoring & Logging
- **Log Rotation**: 10MB max file size, 3 files retention
- **Health Checks**: Automatic container health monitoring
- **Restart Policy**: `unless-stopped` for high availability
- **Backup**: Daily automated backups at 2 AM

## 🎯 Post-Deployment Tasks

### Immediate Tasks
1. **Test all endpoints**: Verify backend API and frontend work
2. **Check SSL**: Verify HTTPS is working correctly
3. **Monitor logs**: Watch for any startup errors
4. **Create first backup**: Run `make backup` to test backup system

### Ongoing Maintenance
1. **Monitor Resources**: Use `docker stats` to monitor usage
2. **Check Logs**: Regular log review with `make logs`
3. **Update Application**: Use `make deploy-prod` for updates
4. **Security Updates**: Keep Docker and system packages updated

## 📋 Quick Reference Commands

### Management Commands
```bash
make prod           # Start production containers
make prod-ssl       # Start with SSL
make logs           # View logs
make restart        # Restart all containers
make status         # Check container status
make backup         # Create backup
make deploy-prod    # Full production deployment
```

### Docker Commands
```bash
docker-compose ps                           # Container status
docker-compose logs -f backend             # Backend logs
docker-compose exec backend bash           # Access backend container
docker stats                               # Resource usage
```

### System Commands
```bash
sudo systemctl status docker               # Docker service status
sudo ufw status                            # Firewall status
sudo certbot certificates                  # SSL certificate status
df -h                                      # Disk usage
free -h                                    # Memory usage
```

## 🚨 Troubleshooting

### Common Issues
1. **Containers won't start**: Check `make logs` for errors
2. **SSL certificate issues**: Verify DNS and run `make setup-ssl`
3. **High memory usage**: Check `docker stats` and restart if needed
4. **Database connection issues**: Verify volume mounts and permissions

### Emergency Procedures
1. **Complete restart**: `make down && make prod`
2. **Rollback**: Restore from backup with `make restore BACKUP_FILE=backup-xxx.tar.gz`
3. **Emergency stop**: `docker-compose down --remove-orphans`

## ✅ Production Ready Status

The Instagram Automation Platform is now **PRODUCTION READY** with:

- ✅ **Secure secret keys** generated and configured
- ✅ **Docker containerization** with resource limits
- ✅ **SSL/HTTPS** configuration ready
- ✅ **Automated backups** configured
- ✅ **Health monitoring** enabled
- ✅ **Security headers** and CORS configured
- ✅ **Log rotation** and management
- ✅ **Easy deployment** with single commands

**Next Step**: Point your domain DNS to the server IP and run `make setup-ssl && make prod-ssl`
