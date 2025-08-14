#!/bin/bash

# Instagram Automation - Docker Production Deployment Script
# Domain: wdyautomation.shop
# This script sets up the complete production environment using Docker

set -e  # Exit on any error

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

# Configuration
DOMAIN="wdyautomation.shop"
APP_DIR="/var/www/instaAutomation"

print_status "🚀 Starting Instagram Automation Docker Deployment..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons."
   print_status "Please run as a regular user with sudo privileges."
   exit 1
fi

# Step 1: Update system and install Docker
print_status "Step 1: Installing Docker and Docker Compose..."
sudo apt update && sudo apt upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker installed successfully"
else
    print_success "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose already installed"
fi

# Step 2: Setup application directory
print_status "Step 2: Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# Step 3: Clone/update repository
print_status "Step 3: Setting up application code..."
cd $APP_DIR
if [ -d ".git" ]; then
    print_status "Repository already exists. Updating..."
    git fetch origin
    git reset --hard origin/main
    git clean -fd
else
    git clone https://github.com/AbdullahYounas0/instaAutomation.git .
fi

# Step 4: Create necessary directories
print_status "Step 4: Creating application directories..."
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p backend/instagram_cookies
mkdir -p backend/browser_profiles
mkdir -p backups

# Create empty JSON files if they don't exist
touch backend/users.json
touch backend/instagram_accounts.json
touch backend/proxy_assignments.json
touch backend/activity_logs.json

# Initialize JSON files with empty arrays if they're empty
for file in backend/users.json backend/instagram_accounts.json backend/proxy_assignments.json backend/activity_logs.json; do
    if [ ! -s "$file" ]; then
        echo "[]" > "$file"
    fi
done

print_success "Application directories created"

# Step 5: Configure environment
print_status "Step 5: Setting up production environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success "Environment file created from template"
else
    print_warning "Environment file already exists"
fi

# Step 6: Install Nginx for reverse proxy (optional)
print_status "Step 6: Installing Nginx for reverse proxy..."
sudo apt install -y nginx

# Create Nginx configuration for Docker
sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null << EOF
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS configuration
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL configuration (to be configured with Let's Encrypt)
    # ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # For now, proxy to Docker containers
    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Increase timeout for long-running scripts
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Handle large file uploads
    client_max_body_size 100M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# Enable the site (but don't start nginx yet until SSL is configured)
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Step 7: Build and start Docker containers
print_status "Step 7: Building and starting Docker containers..."
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

# Wait for containers to be ready
print_status "Waiting for containers to start..."
sleep 30

# Check container health
if docker-compose ps | grep -q "Up"; then
    print_success "Docker containers started successfully"
else
    print_error "Failed to start Docker containers"
    docker-compose logs
    exit 1
fi

# Step 8: Configure firewall
print_status "Step 8: Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Step 9: Install SSL certificate
print_status "Step 9: Setting up SSL certificate..."
sudo apt install -y certbot python3-certbot-nginx

print_warning "SSL certificate setup requires domain DNS to be configured"
print_status "After DNS configuration, run:"
print_status "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"

# Step 10: Create backup script
print_status "Step 10: Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash
# Backup script for Instagram Automation Docker deployment

BACKUP_DIR="/var/www/instaAutomation/backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup-$DATE.tar.gz"

echo "Creating backup: $BACKUP_FILE"

# Create backup
tar -czf "$BACKUP_FILE" \
    backend/logs \
    backend/uploads \
    backend/instagram_cookies \
    backend/browser_profiles \
    backend/users.json \
    backend/instagram_accounts.json \
    backend/proxy_assignments.json \
    backend/activity_logs.json \
    .env

echo "Backup created successfully: $BACKUP_FILE"

# Keep only last 10 backups
ls -t $BACKUP_DIR/backup-*.tar.gz | tail -n +11 | xargs -r rm

echo "Old backups cleaned up"
EOF

chmod +x backup.sh

# Step 11: Setup cron jobs
print_status "Step 11: Setting up automatic backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $APP_DIR && ./backup.sh") | crontab -

# Step 12: Create management aliases
print_status "Step 12: Creating management commands..."
cat >> ~/.bashrc << EOF

# Instagram Automation Docker Management Aliases
alias ia-logs='cd $APP_DIR && docker-compose logs -f'
alias ia-restart='cd $APP_DIR && docker-compose restart'
alias ia-stop='cd $APP_DIR && docker-compose down'
alias ia-start='cd $APP_DIR && docker-compose up -d'
alias ia-update='cd $APP_DIR && git pull && docker-compose up -d --build'
alias ia-backup='cd $APP_DIR && ./backup.sh'
alias ia-status='cd $APP_DIR && docker-compose ps'
EOF

# Final status check
print_status "Step 13: Final deployment verification..."

echo ""
print_success "🎉 Docker deployment completed successfully!"
echo ""
echo -e "${BLUE}=== Deployment Summary ===${NC}"
echo -e "Domain: ${GREEN}$DOMAIN${NC}"
echo -e "Application Directory: ${GREEN}$APP_DIR${NC}"
echo -e "Frontend: ${GREEN}http://localhost${NC} (via Docker)"
echo -e "Backend API: ${GREEN}http://localhost/api${NC} (via Docker)"
echo ""
echo -e "${BLUE}=== Docker Management ===${NC}"
echo -e "View logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "Restart services: ${YELLOW}docker-compose restart${NC}"
echo -e "Stop services: ${YELLOW}docker-compose down${NC}"
echo -e "Update deployment: ${YELLOW}git pull && docker-compose up -d --build${NC}"
echo -e "Create backup: ${YELLOW}./backup.sh${NC}"
echo ""
echo -e "${BLUE}=== Quick Commands (after relogin) ===${NC}"
echo -e "View logs: ${YELLOW}ia-logs${NC}"
echo -e "Restart: ${YELLOW}ia-restart${NC}"
echo -e "Update: ${YELLOW}ia-update${NC}"
echo -e "Backup: ${YELLOW}ia-backup${NC}"
echo -e "Status: ${YELLOW}ia-status${NC}"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo -e "1. Configure your domain DNS to point to this server's IP"
echo -e "2. Run SSL setup: ${YELLOW}sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN${NC}"
echo -e "3. Test the application at ${GREEN}http://$DOMAIN${NC}"
echo -e "4. Monitor with: ${YELLOW}ia-logs${NC}"
echo ""
print_success "🔥 Your Instagram Automation app is now live with Docker!"
echo ""
print_warning "Please logout and login again to use the management aliases"
