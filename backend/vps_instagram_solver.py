#!/usr/bin/env python3
"""
VPS Instagram Access Solution - Bypass Rate Limiting
"""

import asyncio
import sys
import os
import time
import random
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright

class VPSInstagramSolver:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def get_random_user_agent(self):
        """Get a random user agent"""
        return random.choice(self.user_agents)
    
    def get_stealth_browser_args(self):
        """Get browser arguments to avoid detection"""
        return [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--allow-running-insecure-content',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-ipc-flooding-protection',
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--mute-audio',
            '--no-first-run',
            '--disable-gpu',
            '--disable-features=TranslateUI',
            '--disable-component-extensions-with-background-pages',
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-dev-tools',
            '--no-zygote',
            '--single-process',
            '--disable-background-networking'
        ]
    
    async def wait_for_rate_limit_reset(self, minutes=15):
        """Wait for Instagram rate limit to reset"""
        print(f"⏳ Waiting {minutes} minutes for rate limit reset...")
        for i in range(minutes):
            remaining = minutes - i
            print(f"   {remaining} minutes remaining...")
            await asyncio.sleep(60)  # Wait 1 minute
        print("✅ Wait complete, trying again...")
    
    async def test_instagram_access_with_stealth(self, max_retries=3):
        """Test Instagram access with stealth techniques"""
        print("🥷 Testing Instagram Access with Stealth Mode...")
        
        for attempt in range(max_retries):
            print(f"\n🔄 Attempt {attempt + 1}/{max_retries}")
            
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=self.get_stealth_browser_args()
                    )
                    
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent=self.get_random_user_agent(),
                        locale='en-US',
                        timezone_id='America/New_York',
                        extra_http_headers={
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'DNT': '1',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                        }
                    )
                    
                    page = await context.new_page()
                    
                    # Remove automation indicators
                    await page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined,
                        });
                        
                        window.chrome = {
                            runtime: {},
                        };
                        
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5],
                        });
                        
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en'],
                        });
                    """)
                    
                    # Add random delay
                    delay = random.uniform(2, 8)
                    print(f"   ⏱️ Random delay: {delay:.1f}s")
                    await asyncio.sleep(delay)
                    
                    # Try alternative Instagram URLs
                    instagram_urls = [
                        'https://www.instagram.com/',
                        'https://www.instagram.com/accounts/login/',
                        'https://instagram.com/',
                    ]
                    
                    for url in instagram_urls:
                        try:
                            print(f"   🌐 Trying URL: {url}")
                            
                            response = await page.goto(url, 
                                                     wait_until='networkidle', 
                                                     timeout=30000)
                            
                            status = response.status
                            print(f"   📊 Response status: {status}")
                            
                            if status == 200:
                                # Wait for page to load
                                await asyncio.sleep(5)
                                
                                # Check page content
                                content = await page.content()
                                content_length = len(content)
                                print(f"   📊 Page content length: {content_length}")
                                
                                if content_length > 1000:
                                    # Look for login indicators
                                    has_login = 'login' in content.lower()
                                    has_instagram = 'instagram' in content.lower()
                                    has_username = 'username' in content.lower()
                                    
                                    print(f"   📊 Content analysis:")
                                    print(f"     Has login: {has_login}")
                                    print(f"     Has Instagram: {has_instagram}")
                                    print(f"     Has username: {has_username}")
                                    
                                    if has_login and has_instagram:
                                        print("   ✅ Instagram page loaded successfully!")
                                        
                                        # Try to find input fields
                                        inputs = await page.query_selector_all('input')
                                        print(f"   📊 Input fields found: {len(inputs)}")
                                        
                                        await browser.close()
                                        return True
                                
                            elif status == 429:
                                print("   ❌ Still rate limited (429)")
                                break  # Try next attempt
                                
                            else:
                                print(f"   ⚠️ Unexpected status: {status}")
                                
                        except Exception as e:
                            print(f"   ❌ URL {url} failed: {e}")
                            continue
                    
                    await browser.close()
                    
            except Exception as e:
                print(f"   ❌ Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                # Wait before next attempt
                wait_time = random.uniform(30, 90)
                print(f"   ⏳ Waiting {wait_time:.1f}s before next attempt...")
                await asyncio.sleep(wait_time)
        
        return False
    
    async def suggest_solutions(self):
        """Suggest solutions for VPS Instagram access"""
        print("\n🔧 Suggested Solutions for VPS Instagram Access:")
        print("="*60)
        
        print("\n1. 🌍 **Change VPS Location/Provider**")
        print("   - Current VPS IP is flagged by Instagram")
        print("   - Try a VPS from different region (US, Europe)")
        print("   - Use residential IP VPS providers")
        
        print("\n2. 🔄 **Add Proxy Rotation**")
        print("   - Install rotating proxy service")
        print("   - Use residential/mobile proxies")
        print("   - Configure proxy_manager.py")
        
        print("\n3. ⏰ **Wait and Retry Strategy**")
        print("   - Instagram rate limits reset after 24 hours")
        print("   - Schedule automation during off-peak hours")
        print("   - Add random delays between requests")
        
        print("\n4. 🏠 **Run from Different Environment**")
        print("   - Test from local machine first")
        print("   - Use home internet connection")
        print("   - Deploy to different cloud provider")
        
        print("\n5. 🔐 **Account Warmup Process**")
        print("   - Login manually from VPS browser first")
        print("   - Build session history gradually")
        print("   - Use cookie-based authentication")

async def main():
    """Main VPS solution function"""
    print("🚀 VPS Instagram Access Solution")
    print("="*50)
    
    solver = VPSInstagramSolver()
    
    print("Testing Instagram access with stealth techniques...")
    success = await solver.test_instagram_access_with_stealth()
    
    if success:
        print("\n✅ SUCCESS! Instagram access working with stealth mode")
        print("🚀 You can now run the automation scripts")
    else:
        print("\n❌ Instagram access still blocked")
        await solver.suggest_solutions()
        
        print("\n⚠️ IMMEDIATE ACTION REQUIRED:")
        print("1. Set up accounts: python backend/setup_accounts.py")
        print("2. Wait 24 hours for rate limit reset")
        print("3. Try from different VPS location")
        print("4. Add proxy configuration")

if __name__ == "__main__":
    asyncio.run(main())
