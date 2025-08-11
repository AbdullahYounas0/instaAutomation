#!/bin/bash

# Instagram Automation Deployment Script for Hostinger VPS
# Domain: wdyautomation.shop
# Repository: AbdullahYounas0/instaAutomation

set -e  # Exit on any error

echo "🚀 Starting Instagram Automation Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="wdyautomation.shop"
APP_DIR="/var/www/instaAutomation"
BACKEND_PORT=5000
FRONTEND_PORT=3000

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons."
   print_status "Please run as a regular user with sudo privileges."
   exit 1
fi

print_status "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y

print_status "Step 2: Installing required system packages..."
sudo apt install -y curl wget git build-essential software-properties-common

# Install Node.js 18.x
print_status "Step 3: Installing Node.js 18.x..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.9+ and pip
print_status "Step 4: Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install Nginx
print_status "Step 5: Installing Nginx..."
sudo apt install -y nginx

# Install PM2 globally for process management
print_status "Step 6: Installing PM2 for process management..."
sudo npm install -g pm2

# Create application directory
print_status "Step 7: Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# Clone the repository
print_status "Step 8: Cloning repository..."
cd $APP_DIR
if [ -d ".git" ]; then
    print_status "Repository already exists. Fetching latest changes..."
    git fetch origin
    print_status "Resetting to latest main branch..."
    git reset --hard origin/main
    print_status "Cleaning up any untracked files..."
    git clean -fd
else
    git clone https://github.com/AbdullahYounas0/instaAutomation.git .
fi

# Setup environment file
print_status "Step 9: Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Instagram Automation Environment Configuration
FLASK_ENV=production
CORS_ORIGINS=https://wdyautomation.shop,https://www.wdyautomation.shop,http://wdyautomation.shop,http://www.wdyautomation.shop,http://localhost:3000

# Database and Storage
DATABASE_URL=sqlite:///automation.db

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Instagram API Settings
INSTAGRAM_API_DELAY_MIN=2
INSTAGRAM_API_DELAY_MAX=5

# Proxy Settings
PROXY_ROTATION_ENABLED=true
PROXY_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Performance
MAX_CONCURRENT_SCRIPTS=5
MAX_SCRIPT_DURATION=7200

# File Upload
MAX_FILE_SIZE=100MB
UPLOAD_FOLDER=uploads
EOF
    print_success "Environment file created with production settings"
else
    print_warning "Environment file already exists"
    # Update CORS origins if needed
    if ! grep -q "wdyautomation.shop" .env; then
        echo "CORS_ORIGINS=https://wdyautomation.shop,https://www.wdyautomation.shop,http://wdyautomation.shop,http://www.wdyautomation.shop,http://localhost:3000" >> .env
        print_success "Added domain to CORS origins"
    fi
fi

# Backend Setup
print_status "Step 10: Setting up Python backend..."
cd $APP_DIR/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
print_status "Installing Playwright browsers..."
python -m playwright install chromium
if [ $? -eq 0 ]; then
    print_success "Playwright browsers installed successfully"
else
    print_warning "Playwright browser installation failed, will attempt during runtime"
fi

# Create necessary directories
mkdir -p logs uploads

print_success "Backend setup completed"

# Frontend Setup
print_status "Step 11: Setting up React frontend..."
cd $APP_DIR/frontend

# Install Node.js dependencies
npm install

# Build production version
npm run build

print_success "Frontend build completed"

# Create PM2 ecosystem file
print_status "Step 12: Creating PM2 configuration..."
cd $APP_DIR
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'insta-automation-backend',
      script: '$APP_DIR/backend/venv/bin/python',
      args: '-m uvicorn app:app --host 0.0.0.0 --port $BACKEND_PORT --workers 1',
      cwd: '$APP_DIR/backend',
      env: {
        ENV: 'production',
        PORT: $BACKEND_PORT,
        CORS_ORIGINS: 'https://wdyautomation.shop,https://www.wdyautomation.shop,http://wdyautomation.shop,http://www.wdyautomation.shop'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '$APP_DIR/logs/backend-error.log',
      out_file: '$APP_DIR/logs/backend-out.log',
      log_file: '$APP_DIR/logs/backend-combined.log'
    },
    {
      name: 'insta-automation-frontend',
      script: 'npx',
      args: 'serve -s build -l $FRONTEND_PORT',
      cwd: '$APP_DIR/frontend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      error_file: '$APP_DIR/logs/frontend-error.log',
      out_file: '$APP_DIR/logs/frontend-out.log',
      log_file: '$APP_DIR/logs/frontend-combined.log'
    }
  ]
};
EOF

# Install serve package globally for serving frontend
sudo npm install -g serve

# Create logs directory
mkdir -p $APP_DIR/logs

print_success "PM2 configuration created"

# Configure Nginx
print_status "Step 13: Configuring Nginx..."
sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Frontend - Serve React build
    location / {
        proxy_pass http://localhost:$FRONTEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:$BACKEND_PORT;
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

# Enable the site
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

print_success "Nginx configuration completed"

# Configure firewall
print_status "Step 14: Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

print_success "Firewall configured"

# Start services
print_status "Step 15: Starting services..."

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Start applications with PM2
cd $APP_DIR
pm2 start ecosystem.config.js
pm2 save
pm2 startup

print_success "Services started successfully"

# Install SSL certificate (Let's Encrypt)
print_status "Step 16: Installing SSL certificate..."
sudo apt install -y certbot python3-certbot-nginx

# Note: SSL certificate setup requires domain to be pointed to server
print_warning "SSL certificate setup requires domain DNS to be configured"
print_status "After DNS configuration, run: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"

# Final status check
print_status "Step 17: Final status check..."

echo ""
print_success "🎉 Deployment completed successfully!"
echo ""
echo -e "${BLUE}=== Deployment Summary ===${NC}"
echo -e "Domain: ${GREEN}$DOMAIN${NC}"
echo -e "Application Directory: ${GREEN}$APP_DIR${NC}"
echo -e "Backend API: ${GREEN}http://$DOMAIN/api${NC}"
echo -e "Frontend: ${GREEN}http://$DOMAIN${NC}"
echo ""
echo -e "${BLUE}=== Service Management ===${NC}"
echo -e "View logs: ${YELLOW}pm2 logs${NC}"
echo -e "Restart services: ${YELLOW}pm2 restart all${NC}"
echo -e "Stop services: ${YELLOW}pm2 stop all${NC}"
echo -e "Service status: ${YELLOW}pm2 status${NC}"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo -e "1. Configure your domain DNS to point to this server's IP"
echo -e "2. Run SSL setup: ${YELLOW}sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN${NC}"
echo -e "3. Update .env file with production settings"
echo -e "4. Test the application at ${GREEN}http://$DOMAIN${NC}"
echo ""
echo -e "${GREEN}🔥 Your Instagram Automation app is now live!${NC}"
