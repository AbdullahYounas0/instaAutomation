# Instagram Automation - VPS Deployment Guide

## Overview
This guide will help you deploy your Instagram Automation application to a Hostinger VPS with your domain `wdyautomation.shop`.

## Prerequisites
- Hostinger VPS with Ubuntu 20.04+ 
- Domain name: `wdyautomation.shop`
- SSH access to your VPS
- Basic terminal knowledge

## Quick Deployment

### Step 1: Connect to Your VPS
```bash
ssh root@your-vps-ip
```

### Step 2: Create a Non-Root User (Recommended)
```bash
adduser deploy
usermod -aG sudo deploy
su - deploy
```

### Step 3: Upload and Run Deployment Script
```bash
# Clone the repository
git clone https://github.com/AbdullahYounas0/instaAutomation.git
cd instaAutomation

# Make scripts executable
chmod +x deploy.sh manage.sh

# Run the deployment script
./deploy.sh
```

The deployment script will automatically:
- ✅ Update system packages
- ✅ Install Node.js, Python, Nginx, PM2
- ✅ Set up the application
- ✅ Configure reverse proxy
- ✅ Start all services
- ✅ Configure firewall

## Post-Deployment Steps

### 1. Configure DNS
Point your domain to your VPS IP address:
- **A Record**: `wdyautomation.shop` → `your-vps-ip`
- **A Record**: `www.wdyautomation.shop` → `your-vps-ip`

### 2. Setup SSL Certificate
After DNS propagation (usually 5-10 minutes):
```bash
sudo certbot --nginx -d wdyautomation.shop -d www.wdyautomation.shop
```

### 3. Configure Environment Variables
Edit the `.env` file in `/var/www/instaAutomation/`:
```bash
nano /var/www/instaAutomation/.env
```

Update any specific configurations like API keys, database URLs, etc.

## Application Management

Use the `manage.sh` script for easy management:

```bash
# Navigate to app directory
cd /var/www/instaAutomation

# Start services
./manage.sh start

# Stop services
./manage.sh stop

# Restart services
./manage.sh restart

# Check status
./manage.sh status

# View logs
./manage.sh logs

# Update application
./manage.sh update

# Monitor real-time
./manage.sh monitor

# Create backup
./manage.sh backup
```

## Service Architecture

### Frontend (React)
- **Port**: 3000 (internal)
- **Served by**: PM2 + serve
- **URL**: `https://wdyautomation.shop`

### Backend (FastAPI)
- **Port**: 5000 (internal)
- **Served by**: PM2 + Uvicorn
- **URL**: `https://wdyautomation.shop/api`

### Reverse Proxy (Nginx)
- **Port**: 80/443 (public)
- **Handles**: SSL termination, static files, proxy to apps

## File Locations

```
/var/www/instaAutomation/          # Main application directory
├── backend/                       # FastAPI backend
│   ├── venv/                     # Python virtual environment
│   ├── app.py                    # Main application file
│   └── requirements.txt          # Python dependencies
├── frontend/                     # React frontend
│   ├── build/                    # Production build
│   └── package.json             # Node.js dependencies
├── logs/                         # Application logs
├── .env                          # Environment configuration
├── ecosystem.config.js           # PM2 configuration
└── manage.sh                     # Management script
```

## Log Files

```bash
# PM2 Logs
pm2 logs

# Nginx Logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application Logs
tail -f /var/www/instaAutomation/logs/backend-combined.log
tail -f /var/www/instaAutomation/logs/frontend-combined.log
```

## Troubleshooting

### Check Service Status
```bash
# PM2 processes
pm2 status

# Nginx status
sudo systemctl status nginx

# System resources
htop
df -h
```

### Common Issues

1. **Port Already in Use**
   ```bash
   sudo lsof -i :5000
   sudo lsof -i :3000
   ```

2. **Permission Issues**
   ```bash
   sudo chown -R deploy:deploy /var/www/instaAutomation
   ```

3. **SSL Certificate Issues**
   ```bash
   sudo certbot renew --dry-run
   ```

4. **Memory Issues**
   ```bash
   free -h
   sudo systemctl restart nginx
   pm2 restart all
   ```

## Security Considerations

- ✅ Firewall configured (UFW)
- ✅ Non-root user for application
- ✅ SSL certificate for HTTPS
- ✅ Secure headers in Nginx
- ✅ Environment variables for secrets

## Backup Strategy

### Automated Backups
```bash
# Add to crontab for daily backups
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /var/www/instaAutomation/manage.sh backup
```

### Manual Backup
```bash
./manage.sh backup
```

## Performance Optimization

### Enable Gzip Compression
Already configured in Nginx configuration.

### Monitor Resources
```bash
# Real-time monitoring
htop

# Disk usage
df -h

# Memory usage
free -h

# PM2 monitoring
pm2 monit
```

## Support

If you encounter any issues:

1. Check the logs: `./manage.sh logs`
2. Verify services: `./manage.sh status`
3. Check system resources: `htop` and `df -h`
4. Review Nginx configuration: `sudo nginx -t`

## URLs After Deployment

- **Frontend**: https://wdyautomation.shop
- **Backend API**: https://wdyautomation.shop/api
- **Admin Dashboard**: https://wdyautomation.shop/admin

---

🚀 **Your Instagram Automation application is now live!**
