#!/usr/bin/env python3
"""
Browser Installation Script
Installs Playwright browsers for production deployment
"""

import subprocess
import sys
import os

def install_playwright_browsers():
    """Install Playwright browsers"""
    try:
        print("🔧 Installing Playwright browsers...")
        
        # Try different installation methods
        installation_commands = [
            ['playwright', 'install', 'chromium'],
            ['python', '-m', 'playwright', 'install', 'chromium'],
            ['python3', '-m', 'playwright', 'install', 'chromium']
        ]
        
        for cmd in installation_commands:
            try:
                print(f"Trying: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print("✅ Playwright browsers installed successfully!")
                    print(result.stdout)
                    return True
                else:
                    print(f"❌ Command failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ Command timed out: {' '.join(cmd)}")
            except FileNotFoundError:
                print(f"❌ Command not found: {' '.join(cmd)}")
            except Exception as e:
                print(f"❌ Error running command: {e}")
        
        print("❌ All installation attempts failed")
        return False
        
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def check_browser_installation():
    """Check if browsers are installed"""
    try:
        # Check common installation paths
        possible_paths = [
            os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
            os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-win/chrome.exe"),
            "/home/deploy/.cache/ms-playwright/chromium-*/chrome-linux/chrome"
        ]
        
        print("🔍 Checking browser installation...")
        
        # Also try to run a simple playwright command
        try:
            result = subprocess.run(['playwright', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Playwright version: {result.stdout.strip()}")
            else:
                print(f"⚠️ Playwright command failed: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Cannot check Playwright version: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking installation: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Playwright Browser Installation Script")
    print("=" * 50)
    
    # Check current status
    check_browser_installation()
    
    print("\n" + "=" * 50)
    
    # Install browsers
    success = install_playwright_browsers()
    
    print("\n" + "=" * 50)
    
    if success:
        print("🎉 Browser installation completed successfully!")
        print("You can now run the Instagram automation scripts.")
    else:
        print("❌ Browser installation failed.")
        print("Please manually run: playwright install chromium")
        sys.exit(1)
