#!/bin/bash

# VPS System Dependencies Fix Script
# Installs all required system dependencies for Playwright browsers

set -e  # Exit on any error

echo "🔧 Installing Playwright System Dependencies on VPS..."

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

print_status "Step 1: Updating package lists..."
sudo apt update

print_status "Step 2: Installing Playwright system dependencies..."
sudo playwright install-deps

if [ $? -eq 0 ]; then
    print_success "Playwright system dependencies installed successfully"
else
    print_warning "Playwright install-deps failed, trying manual installation..."
    
    print_status "Step 3: Installing dependencies manually..."
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
        libxcursor1 \
        libxi6 \
        libxtst6 \
        libasound2-dev \
        libatspi2.0-dev \
        libdrm2 \
        libxkbcommon0 \
        libgtk-4-1
    
    print_success "Manual dependency installation completed"
fi

print_status "Step 4: Installing additional media dependencies..."
sudo apt-get install -y \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    libwebkit2gtk-4.0-37

print_status "Step 5: Installing fonts and additional libraries..."
sudo apt-get install -y \
    fonts-liberation \
    fonts-roboto \
    fonts-ubuntu \
    xvfb \
    x11-utils \
    x11-xserver-utils

print_status "Step 6: Configuring virtual display for headless mode..."
# Install and configure xvfb for virtual display
sudo apt-get install -y xvfb

# Create xvfb service for persistent virtual display
sudo tee /etc/systemd/system/xvfb.service > /dev/null << EOF
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable xvfb
sudo systemctl start xvfb

print_status "Step 7: Setting up environment variables..."
# Add display environment variable
echo "export DISPLAY=:99" | sudo tee -a /etc/environment

print_status "Step 8: Verifying installation..."
# Test browser launch
cd /var/www/instaAutomation/backend
source venv/bin/activate

echo "Testing browser launch..."
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://example.com')
        title = await page.title()
        print(f'✅ Browser test successful! Page title: {title}')
        await browser.close()
        await playwright.stop()
        return True
    except Exception as e:
        print(f'❌ Browser test failed: {e}')
        return False

asyncio.run(test_browser())
"

print_success "🎉 VPS system dependencies installation completed!"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo -e "1. Restart your PM2 services: ${YELLOW}pm2 restart all${NC}"
echo -e "2. Test your automation scripts"
echo -e "3. Check logs: ${YELLOW}pm2 logs${NC}"
echo ""
echo -e "${GREEN}System is now ready for Playwright automation!${NC}"
