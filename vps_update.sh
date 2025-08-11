#!/bin/bash

# VPS Deployment Update Script
# Run this script on your VPS to update the Instagram Automation platform

set -e  # Exit on any error

echo "🚀 Starting VPS deployment update..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
APP_DIR="/var/www/instaAutomation"
BACKUP_DIR="/var/www/instaAutomation_backup_$(date +%Y%m%d_%H%M%S)"

print_status "Step 1: Creating backup..."
if [ -d "$APP_DIR" ]; then
    sudo cp -r "$APP_DIR" "$BACKUP_DIR"
    print_success "Backup created at $BACKUP_DIR"
else
    print_warning "Application directory not found, skipping backup"
fi

print_status "Step 2: Stopping services..."
pm2 stop all || print_warning "PM2 services not running"

print_status "Step 3: Updating code from GitHub..."
cd "$APP_DIR"
git fetch origin
git reset --hard origin/main
git clean -fd
print_success "Code updated from GitHub"

print_status "Step 4: Updating Python dependencies..."
cd "$APP_DIR/backend"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies updated"

print_status "Step 5: Installing Playwright browsers and system dependencies..."
python -m playwright install chromium
if [ $? -eq 0 ]; then
    print_success "Playwright browsers installed successfully"
else
    print_warning "Playwright browser installation failed, will attempt during runtime"
fi

# Install system dependencies
print_status "Installing Playwright system dependencies..."
sudo playwright install-deps
if [ $? -eq 0 ]; then
    print_success "Playwright system dependencies installed successfully"
else
    print_warning "Playwright system dependencies installation failed, installing manually..."
    sudo apt-get update
    sudo apt-get install -y \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libatspi2.0-0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libxss1 \
        libgtk-3-0 \
        libnss3 \
        fonts-liberation \
        xvfb
    print_success "Manual system dependencies installation completed"
fi

print_status "Step 6: Testing browser installation..."
python ../install_browsers.py
print_success "Browser installation test completed"

print_status "Step 7: Updating frontend..."
cd "$APP_DIR/frontend"
npm install
npm run build
print_success "Frontend updated and built"

print_status "Step 8: Restarting services..."
cd "$APP_DIR"
pm2 restart all
pm2 save
print_success "Services restarted"

print_status "Step 9: Checking service status..."
pm2 status

print_status "Step 10: Testing the fixes..."
cd "$APP_DIR/backend"
source venv/bin/activate

# Test OpenAI client
echo "Testing OpenAI client..."
python -c "
from instagram_dm_automation import DMAutomationEngine
engine = DMAutomationEngine()
result = engine.setup_openai_client()
print('✅ OpenAI Client Setup: SUCCESS' if result else '❌ OpenAI Client Setup: FAILED')
"

# Test browser installation
echo "Testing browser availability..."
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        await browser.close()
        await playwright.stop()
        print('✅ Browser Test: SUCCESS')
        return True
    except Exception as e:
        print(f'❌ Browser Test: FAILED - {e}')
        return False

asyncio.run(test_browser())
"

print_success "🎉 VPS deployment update completed!"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo -e "1. Check application logs: ${YELLOW}pm2 logs${NC}"
echo -e "2. Test the application at your domain"
echo -e "3. Monitor for any issues in the first few runs"
echo ""
echo -e "${GREEN}The following issues have been fixed:${NC}"
echo -e "✅ Automatic Playwright browser installation"
echo -e "✅ Enhanced OpenAI client compatibility"
echo -e "✅ Better error handling for production environment"
echo -e "✅ Fallback mechanisms for failed services"
