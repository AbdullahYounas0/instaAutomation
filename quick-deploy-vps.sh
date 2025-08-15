#!/bin/bash

# Instagram Automation - Quick VPS Deployment Script
# Run this script on your VPS to deploy the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${GREEN}"
echo "=================================================================="
echo "    Instagram Automation Platform - VPS Deployment"
echo "=================================================================="
echo -e "${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_warning "Running as root. Consider using a regular user with sudo privileges."
fi

# Step 1: Update system
print_status "Step 1: Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install Docker
print_status "Step 2: Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker installed"
else
    print_success "Docker already installed"
fi

# Step 3: Install Docker Compose
print_status "Step 3: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose already installed"
fi

# Step 4: Create application directory
print_status "Step 4: Setting up application directory..."
mkdir -p /var/www/instaAutomation
cd /var/www/instaAutomation

# Step 5: Clone repository
print_status "Step 5: Cloning repository..."
if [ -d ".git" ]; then
    print_status "Repository exists, updating..."
    git fetch origin
    git reset --hard origin/main
    git clean -fd
else
    git clone https://github.com/AbdullahYounas0/instaAutomation.git .
fi

# Step 6: Create necessary directories and files
print_status "Step 6: Creating application directories..."
mkdir -p backend/logs backend/uploads backend/instagram_cookies backend/browser_profiles

# Initialize JSON files if they don't exist
for file in backend/users.json backend/instagram_accounts.json backend/proxy_assignments.json backend/activity_logs.json; do
    if [ ! -f "$file" ]; then
        echo "[]" > "$file"
    fi
done

# Step 7: Set permissions
chown -R $USER:$USER /var/www/instaAutomation
chmod 755 backend/logs backend/uploads backend/instagram_cookies backend/browser_profiles

# Step 8: Configure firewall
print_status "Step 7: Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Step 9: Build and start application
print_status "Step 8: Building and starting application..."
docker-compose up -d --build

# Step 10: Wait for containers to start
print_status "Step 9: Waiting for containers to start..."
sleep 30

# Step 11: Test application
print_status "Step 10: Testing application..."
if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
    print_success "Backend is healthy"
else
    print_error "Backend health check failed"
fi

if curl -f http://localhost/ >/dev/null 2>&1; then
    print_success "Frontend is accessible"
else
    print_error "Frontend accessibility check failed"
fi

# Step 12: Create backup script
print_status "Step 11: Creating backup system..."
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/www/instaAutomation/backups"
DATE=$(date +%Y%m%d-%H%M%S)
mkdir -p $BACKUP_DIR

tar -czf "$BACKUP_DIR/backup-$DATE.tar.gz" \
    backend/logs \
    backend/uploads \
    backend/instagram_cookies \
    backend/browser_profiles \
    backend/users.json \
    backend/instagram_accounts.json \
    backend/proxy_assignments.json \
    backend/activity_logs.json \
    .env 2>/dev/null || true

ls -t $BACKUP_DIR/backup-*.tar.gz | tail -n +11 | xargs -r rm
echo "Backup created: backup-$DATE.tar.gz"
EOF

chmod +x backup.sh

# Step 13: Setup cron for backups
print_status "Step 12: Setting up automatic backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd /var/www/instaAutomation && ./backup.sh") | crontab -

# Step 14: Create management aliases
print_status "Step 13: Creating management commands..."
cat >> ~/.bashrc << 'EOF'

# Instagram Automation Management Commands
alias ia-logs='cd /var/www/instaAutomation && docker-compose logs -f'
alias ia-restart='cd /var/www/instaAutomation && docker-compose restart'
alias ia-stop='cd /var/www/instaAutomation && docker-compose down'
alias ia-start='cd /var/www/instaAutomation && docker-compose up -d'
alias ia-update='cd /var/www/instaAutomation && git pull && docker-compose up -d --build'
alias ia-backup='cd /var/www/instaAutomation && ./backup.sh'
alias ia-status='cd /var/www/instaAutomation && docker-compose ps'
alias ia-health='curl -f http://localhost:5000/api/health && curl -f http://localhost/ > /dev/null && echo "All services healthy"'
EOF

# Get server IP
SERVER_IP=$(curl -s http://checkip.amazonaws.com/ || curl -s http://ipinfo.io/ip || echo "Unable to detect")

echo ""
print_success "🎉 Deployment completed successfully!"
echo ""
echo -e "${BLUE}=== Access Information ===${NC}"
echo -e "Server IP: ${GREEN}$SERVER_IP${NC}"
echo -e "Frontend: ${GREEN}http://$SERVER_IP${NC}"
echo -e "Backend API: ${GREEN}http://$SERVER_IP/api${NC}"
echo -e "Health Check: ${GREEN}http://$SERVER_IP/api/health${NC}"
echo ""
echo -e "${BLUE}=== Management Commands ===${NC}"
echo -e "View logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "Restart: ${YELLOW}docker-compose restart${NC}"
echo -e "Status: ${YELLOW}docker-compose ps${NC}"
echo -e "Update: ${YELLOW}git pull && docker-compose up -d --build${NC}"
echo ""
echo -e "${BLUE}=== Quick Commands (after relogin) ===${NC}"
echo -e "View logs: ${YELLOW}ia-logs${NC}"
echo -e "Restart: ${YELLOW}ia-restart${NC}"
echo -e "Status: ${YELLOW}ia-status${NC}"
echo -e "Health: ${YELLOW}ia-health${NC}"
echo -e "Update: ${YELLOW}ia-update${NC}"
echo -e "Backup: ${YELLOW}ia-backup${NC}"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo "1. Test the application: curl http://$SERVER_IP/api/health"
echo "2. Open in browser: http://$SERVER_IP"
echo "3. Configure domain and SSL (optional)"
echo "4. Add Instagram accounts via admin panel"
echo ""
print_success "🚀 Your Instagram Automation Platform is now live!"
echo ""
print_warning "Please logout and login again to use the management aliases"
