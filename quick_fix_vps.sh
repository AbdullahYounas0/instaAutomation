#!/bin/bash

# Quick VPS Fix for Playwright Dependencies
# Run this script to immediately fix the browser dependencies issue

echo "🔧 Quick Fix: Installing Playwright System Dependencies..."

# Navigate to the backend directory and activate virtual environment
cd /var/www/instaAutomation/backend
source venv/bin/activate

# Install system dependencies using Python module
echo "Installing system dependencies..."
python -m playwright install-deps

# If that fails, install manually
if [ $? -ne 0 ]; then
    echo "Installing dependencies manually..."
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
        libxcursor1 \
        libxi6 \
        libxtst6 \
        fonts-liberation \
        xvfb
fi

echo "Restarting PM2 services..."
pm2 restart all

echo "✅ Quick fix completed! Your automation scripts should now work."
echo "Check the status with: pm2 logs"
