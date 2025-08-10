import os
import sys
import csv
import json
import random
import threading
import asyncio
import logging
import pandas as pd
import chardet
import pyotp
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from openai import OpenAI
import time
from proxy_manager import proxy_manager
from enhanced_instagram_auth import enhanced_auth
from instagram_cookie_manager import cookie_manager

# Configuration constants
INSTAGRAM_URL = "https://www.instagram.com/"
MAX_PARALLEL_ACCOUNTS = 10

# Global locks and variables
csv_lock = threading.Lock()
used_proxies = set()

class DMAutomationEngine:
    def __init__(self, log_callback=None, stop_callback=None):
        self.log_callback = log_callback or print
        self.stop_callback = stop_callback or (lambda: False)
        self.client = None
        self.sent_dms = []
        self.positive_responses = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        self.log_callback(formatted_message, level)

    async def update_visual_status(self, page, status_text, account_number, step=None):
        """Visual status updates disabled for VPS deployment"""
        pass  # No-op for headless mode
        
    def setup_openai_client(self):
        """Setup OpenAI client for DeepSeek API"""
        try:
            # Always use the default API key
            deepseek_key = 'sk-0307c2f76e434a19aaef94e76c017fca'
            self.log("Using default DeepSeek API key for AI-powered message generation")
            
            self.client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com"
            )
            self.log("DeepSeek AI client initialized successfully")
            return True
        except Exception as e:
            self.log(f"Failed to initialize AI client: {e}", "ERROR")
            return False
    
    def get_account_proxy(self, username):
        """Get the assigned proxy for an account"""
        return proxy_manager.get_account_proxy(username)
    
    def parse_proxy(self, proxy_string):
        """Parse proxy string into components"""
        return proxy_manager.parse_proxy(proxy_string)
    
    async def setup_browser(self, proxy_string=None, account_number=1):
        """Set up browser with optimized settings and proxy support"""
        try:
            playwright = await async_playwright().start()
            
            # Parse proxy if provided
            proxy_config = None
            if proxy_string:
                proxy_parts = self.parse_proxy(proxy_string)
                if proxy_parts:
                    proxy_config = {
                        'server': proxy_parts['server'],
                        'username': proxy_parts['username'],
                        'password': proxy_parts['password']
                    }
                    self.log(f"Using proxy: {proxy_parts['server']}")
            
            # Randomize viewport and user agent
            viewports = [
                {"width": 1366, "height": 768},
                {"width": 1920, "height": 1080},
                {"width": 1536, "height": 864},
                {"width": 1440, "height": 900},
                {"width": 1280, "height": 720}
            ]
            viewport = random.choice(viewports)
            
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
            ]
            user_agent = random.choice(user_agents)
            
            # Configure browser launch args for headless mode
            browser_args = [
                "--no-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
            
            # Full viewport for headless mode
            viewport = {"width": 1920, "height": 1080}
            
            # Launch browser with stealth mode
            browser = await playwright.chromium.launch(
                headless=False,  # Show browser for localhost debugging
                proxy=proxy_config,
                args=browser_args + ['--start-maximized', '--disable-blink-features=AutomationControlled'],
                slow_mo=1000  # Slow down actions for visibility
            )
            
            context = await browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                java_script_enabled=True,
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                window.chrome = {
                    runtime: {}
                };
            """)
            
            context.set_default_timeout(120000)  # 2 minutes
            context.set_default_navigation_timeout(120000)
            
            return playwright, browser, context
        
        except Exception as e:
            self.log(f"Browser setup failed: {e}", "ERROR")
            raise
    
    def load_accounts(self, accounts_file):
        """Load bot accounts from file"""
        try:
            if accounts_file.endswith('.csv'):
                accounts_df = pd.read_csv(accounts_file)
            else:
                accounts_df = pd.read_excel(accounts_file)
            
            # Standardize column names
            accounts_df.columns = accounts_df.columns.str.strip().str.title()
            
            if 'Username' not in accounts_df.columns or 'Password' not in accounts_df.columns:
                raise ValueError("Accounts file must contain 'Username' and 'Password' columns")
            
            accounts = []
            for _, row in accounts_df.iterrows():
                if pd.notna(row['Username']) and pd.notna(row['Password']):
                    username = str(row['Username']).strip()
                    password = str(row['Password']).strip()
                    
                    # Get full account details including TOTP secret from database
                    from instagram_accounts import get_account_details
                    account_details = get_account_details(username)
                    
                    if account_details:
                        # Use account details from database which includes TOTP secret
                        accounts.append({
                            'username': username,
                            'password': password,
                            'totp_secret': account_details.get('totp_secret', ''),
                            'email': account_details.get('email', ''),
                            'phone': account_details.get('phone', '')
                        })
                        self.log(f"✅ Account {username} loaded with full details from database")
                    else:
                        # Fallback to CSV data only
                        accounts.append({
                            'username': username,
                            'password': password,
                            'totp_secret': '',
                            'email': '',
                            'phone': ''
                        })
                        self.log(f"⚠️ Account {username} loaded from CSV only (no database entry found)")
            
            self.log(f"Loaded {len(accounts)} bot accounts")
            return accounts
            
        except Exception as e:
            self.log(f"Error loading accounts: {e}", "ERROR")
            raise
    
    def load_target_users(self, target_file=None):
        """Load target users from file - no defaults allowed"""
        if not target_file:
            self.log("❌ No target file provided - target users are required for DM automation", "ERROR")
            self.log("Please upload an Excel/CSV file containing target users with columns like: username, first_name, city, bio", "ERROR")
            return []
        
        try:
            # Detect encoding
            with open(target_file, 'rb') as f:
                encoding = chardet.detect(f.read())['encoding']
            
            if target_file.endswith('.csv'):
                target_df = pd.read_csv(target_file, encoding=encoding)
            else:
                target_df = pd.read_excel(target_file)
            
            # Standardize column names (case-insensitive)
            target_df.columns = target_df.columns.str.strip().str.lower()
            
            # Log available columns for debugging
            self.log(f"Available columns in target file: {list(target_df.columns)}")
            
            # Check for username column variants
            username_columns = ['username', 'user_name', 'user', 'instagram_username', 'ig_username', 'handle']
            username_col = None
            for col in username_columns:
                if col in target_df.columns:
                    username_col = col
                    break
            
            if not username_col:
                self.log("❌ ERROR: No username column found in target file!", "ERROR")
                self.log(f"Expected one of: {username_columns}", "ERROR")
                self.log(f"Found columns: {list(target_df.columns)}", "ERROR")
                return []
            
            # Filter out rows with empty usernames
            valid_users = []
            total_rows = len(target_df)
            
            for _, row in target_df.iterrows():
                username = row.get(username_col, '').strip() if pd.notna(row.get(username_col)) else ''
                
                if username and username != '':
                    # Normalize username (remove @ if present)
                    username = username.replace('@', '').strip()
                    
                    # Skip obviously invalid usernames
                    if username.lower().startswith('user_') and username[5:].isdigit():
                        self.log(f"⚠️ Skipping dummy username: {username}", "WARNING")
                        continue
                    
                    user_data = {
                        'username': username,
                        'first_name': row.get('first_name', row.get('firstname', row.get('name', ''))),
                        'city': row.get('city', row.get('location', '')),
                        'bio': row.get('bio', row.get('biography', row.get('description', ''))),
                    }
                    
                    # Clean up data
                    for key, value in user_data.items():
                        if pd.isna(value):
                            user_data[key] = ''
                        else:
                            user_data[key] = str(value).strip()
                    
                    valid_users.append(user_data)
                else:
                    self.log(f"⚠️ Skipping row with empty username", "WARNING")
            
            self.log(f"✅ Loaded {len(valid_users)} valid target users (filtered from {total_rows} rows)")
            
            if len(valid_users) == 0:
                self.log("❌ No valid target users found! Check your file format and data.", "ERROR")
                return []
            
            # Show sample of loaded users for verification
            if len(valid_users) > 0:
                sample_user = valid_users[0]
                self.log(f"📋 Sample user: @{sample_user['username']} | {sample_user['first_name']} | {sample_user['city']}")
            
            return valid_users
            
        except Exception as e:
            self.log(f"Error loading target users: {e}", "WARNING")
            return []
    
    def load_dm_prompt(self, prompt_file=None, custom_prompt=None):
        """Load DM prompt from file or use custom prompt"""
        if custom_prompt and custom_prompt.strip():
            self.log("Using custom DM prompt")
            return custom_prompt.strip()
        
        if prompt_file and os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as file:
                    prompt = file.read().strip()
                self.log("DM prompt loaded from file")
                return prompt
            except Exception as e:
                self.log(f"Error loading prompt file: {e}", "WARNING")
        
        # Default prompt
        default_prompt = """Create a personalized Instagram DM for {first_name} in {city} who works in {bio}. 
The message should be about offering virtual assistant services to help with business tasks. 
Keep it friendly, professional, and under 500 characters. 
Mention how VA services could specifically help their type of work.
Make it feel personal and not like spam."""
        
        self.log("Using default DM prompt")
        return default_prompt
    
    def generate_message(self, user_data, prompt_template):
        """Generate personalized message using AI"""
        try:
            city = user_data.get('city', '') or "your area"
            bio = user_data.get('bio', '') or "your work"
            first_name = user_data.get('first_name', user_data.get('username', 'there'))
            
            prompt = f"{prompt_template}\nUser data: city: {city}, bio: {bio}, first_name: {first_name}"
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Write personalized Instagram DMs. Keep under 500 characters."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            self.log(f"Message generation failed: {e}", "WARNING")
            return f"Hey {first_name}, interested in VA services to help with your business tasks? Worth a chat?"
    
    async def handle_login_info_save_dialog(self, page, username):
        """Handle the 'Save your login info?' dialog by clicking 'Not now'"""
        try:
            self.log(f"[{username}] 🔍 Looking for 'Not now' button on save login info dialog...")
            
            # Wait a moment for the dialog to fully load
            await asyncio.sleep(2)
            
            # Check if we're on the save login info page
            current_url = page.url
            if "accounts/onetap" not in current_url:
                self.log(f"[{username}] Not on save login info page, current URL: {current_url}")
                return False
            
            # Updated selectors based on latest Instagram DOM structure (August 2025)
            not_now_selectors = [
                # Latest Instagram "Not now" button selectors with exact class chain
                'div.x1i10hfl.xjqpnuy.xc5r6h4.xqeqjp1.x1phubyo.xdl72j9.x2lah0s.xe8uvvx.xdj266r.x14z9mp.xat24cr.x1lziwak.x2lwn1j.xeuugli.x1hl2dhg.xggy1nq.x1ja2u2z.x1t137rt.x1q0g3np.x1a2a7pz.x6s0dn4.xjyslct.x1ejq31n.x18oe1m7.x1sy0etr.xstzfhl.x9f619.x1ypdohk.x1f6kntn.xl56j7k.x17ydfre.x2b8uid.xlyipyv.x87ps6o.x14atkfc.x5c86q.x18br7mf.x1i0vuye.xl0gqc1.xr5sc7.xlal1re.x14jxsvd.xt0b8zv.xjbqb8w.xr9e8f9.x1e4oeot.x1ui04y5.x6en5u8.x972fbf.x10w94by.x1qhh985.x14e42zd.xt0psk2.xt7dq6l.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x1n2onr6.x1n5bzlp[role="button"]:has-text("Not now")',
                
                # Partial class match selectors
                'div[class*="x1i10hfl"][class*="xjqpnuy"][class*="xc5r6h4"][role="button"]:has-text("Not now")',
                'div[class*="x1i10hfl"][class*="xjqpnuy"][role="button"]:has-text("Not now")',
                'div[class*="x1i10hfl"][role="button"]:has-text("Not now")',
                
                # Previous working selectors
                'button:has-text("Not now")',
                'button:has-text("Not Now")', 
                'div[role="button"]:has-text("Not now")',
                'div[role="button"]:has-text("Not Now")',
                
                # XPath selectors with latest class targeting
                '//div[contains(@class, "x1i10hfl") and contains(@class, "xjqpnuy") and contains(@class, "xc5r6h4") and @role="button" and contains(text(), "Not now")]',
                '//div[contains(@class, "x1i10hfl") and contains(@class, "xjqpnuy") and @role="button" and contains(text(), "Not now")]',
                '//div[contains(@class, "x1i10hfl") and @role="button" and contains(text(), "Not now")]',
                
                # Generic XPath selectors
                '//button[contains(text(), "Not now")]',
                '//button[contains(text(), "Not Now")]',
                '//div[@role="button" and contains(text(), "Not now")]',
                '//div[@role="button" and contains(text(), "Not Now")]',
                
                # Generic role-based selectors
                '[role="button"]:has-text("Not now")',
                '[role="button"]:has-text("Not Now")',
                
                # Instagram button classes (legacy)
                'button._acan._acap._acas._aj1-',
                'div[role="button"]._acan._acap._acas._aj1-',
                
                # Fallback selectors
                '*:has-text("Not now"):visible',
                '*:has-text("Not Now"):visible'
            ]
            
            for i, selector in enumerate(not_now_selectors):
                try:
                    self.log(f"[{username}] Trying selector {i+1}: {selector[:100]}{'...' if len(selector) > 100 else ''}")
                    
                    if selector.startswith('//'):
                        # XPath selector
                        element = await page.wait_for_selector(f'xpath={selector}', timeout=3000)
                    else:
                        # CSS selector
                        element = await page.wait_for_selector(selector, timeout=3000)
                    
                    if element:
                        # Check if element is visible and clickable
                        is_visible = await element.is_visible()
                        if is_visible:
                            # Verify the element actually contains "Not now" text
                            element_text = await element.text_content()
                            if element_text and ("Not now" in element_text or "Not Now" in element_text):
                                await element.click()
                                self.log(f"[{username}] ✅ Clicked 'Not now' button using selector {i+1}")
                                await asyncio.sleep(random.uniform(2, 3))
                                
                                # Verify we've moved away from the save login page
                                await asyncio.sleep(1)
                                new_url = page.url
                                if "accounts/onetap" not in new_url:
                                    self.log(f"[{username}] ✅ Successfully moved away from save login page")
                                    return True
                                else:
                                    self.log(f"[{username}] Still on save login page after click, trying next selector...")
                                    continue
                            else:
                                self.log(f"[{username}] Element found but text doesn't match: '{element_text}'")
                                continue
                        else:
                            self.log(f"[{username}] Element found but not visible with selector {i+1}")
                except Exception as e:
                    self.log(f"[{username}] Selector {i+1} failed: {e}")
                    continue
            
            # Final fallback - try to click anywhere that says "Not now"
            try:
                self.log(f"[{username}] Final fallback - looking for any 'Not now' text...")
                await page.click('text="Not now"', timeout=3000)
                self.log(f"[{username}] ✅ Clicked 'Not now' using text fallback")
                await asyncio.sleep(3)
                return True
            except:
                pass
            
            # If all else fails, try pressing Escape or Tab to potentially skip
            try:
                self.log(f"[{username}] All selectors failed, trying keyboard shortcuts...")
                await page.keyboard.press('Tab')
                await asyncio.sleep(0.5)
                await page.keyboard.press('Enter')
                await asyncio.sleep(2)
                
                new_url = page.url  
                if "accounts/onetap" not in new_url:
                    self.log(f"[{username}] ✅ Keyboard shortcut worked!")
                    return True
            except:
                pass
            
            self.log(f"[{username}] ❌ Could not find or click 'Not now' button after all attempts")
            return False
            
        except Exception as e:
            self.log(f"[{username}] Error handling save login dialog: {e}")
            return False

    async def is_verification_required(self, page):
        """Check if the current page requires verification"""
        current_url = page.url
        verification_indicators = [
            "challenge",
            "checkpoint", 
            # "accounts/onetap" removed - this is just "Save your login info?" dialog, can be handled automatically
            "auth_platform/codeentry",
            "two_factor",
            "2fa",
            "verify",
            "security",
            "suspicious"
        ]
        
        # Check URL
        if any(indicator in current_url.lower() for indicator in verification_indicators):
            return True
            
        # Check page content for verification elements
        verification_selectors = [
            "input[name='verificationCode']",
            "input[name='security_code']", 
            "[data-testid='2fa-input']",
            "text=Enter the code",
            "text=verification code",
            "text=Two-factor authentication"
        ]
        
        for selector in verification_selectors:
            if await page.query_selector(selector):
                return True
                
        return False

    async def safe_goto(self, page, url, retries=3):
        """Safely navigate to URL with retries"""
        for attempt in range(retries):
            try:
                self.log(f"Navigating to {url} (attempt {attempt + 1})")
                
                if attempt == 0:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                elif attempt == 1:
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                else:
                    await page.goto(url, wait_until="load", timeout=60000)
                
                await asyncio.sleep(random.uniform(2, 4))
                
                if "instagram.com" in page.url:
                    return True
                else:
                    self.log(f"Unexpected URL: {page.url}", "WARNING")
                    
            except Exception as e:
                self.log(f"Navigation attempt {attempt + 1} failed: {e}", "WARNING")
                if attempt < retries - 1:
                    await asyncio.sleep(random.uniform(3, 5))
                    continue
        
        return False
    
    async def handle_notifications_popup(self, page, account_username):
        """Handle 'Turn On Notifications' popup if it appears"""
        try:
            self.log(f"[{account_username}] Checking for notifications popup...")
            
            # Wait a moment for popup to appear
            await asyncio.sleep(2)
            
            # Look for notification popup selectors
            notification_selectors = [
                # "Turn On Notifications" popup
                'button:has-text("Turn On Notifications")',
                'div[role="button"]:has-text("Turn On Notifications")', 
                'button:has-text("Yes")',
                'div[role="button"]:has-text("Yes")',
                'text="Turn On Notifications"',
                'text="Yes"',
                ':text-is("Yes")',
                ':text-is("Turn On Notifications")',
                # Generic notification related buttons
                'button:has-text("Allow")',
                'button:has-text("Enable")',
                'div[role="button"]:has-text("Allow")',
                'div[role="button"]:has-text("Enable")'
            ]
            
            # Try each selector to find and click the "Yes" or "Turn On Notifications" button
            for i, selector in enumerate(notification_selectors):
                try:
                    self.log(f"[{account_username}] Trying notification popup selector {i+1}/{len(notification_selectors)}: {selector}")
                    
                    # Check if element exists
                    element = await page.query_selector(selector)
                    if element:
                        # Verify element is visible
                        is_visible = await element.is_visible()
                        if is_visible:
                            # Get the actual text of the element
                            element_text = await element.text_content()
                            await element.click()
                            self.log(f"[{account_username}] ✅ Clicked '{element_text}' button for notifications popup")
                            
                            # Wait for popup to dismiss
                            await asyncio.sleep(2)
                            return True
                        else:
                            self.log(f"[{account_username}] Element found but not visible with selector {i+1}")
                    else:
                        self.log(f"[{account_username}] No element found with selector {i+1}")
                        
                except Exception as e:
                    self.log(f"[{account_username}] Notification popup selector {i+1} failed: {str(e)[:100]}")
                    continue
            
            # Try modern Playwright locators as fallback
            try:
                self.log(f"[{account_username}] Trying modern Playwright locators for notifications...")
                
                # Try get_by_text for "Yes"
                try:
                    yes_locator = page.get_by_text("Yes", exact=True)
                    await yes_locator.click(timeout=3000)
                    self.log(f"[{account_username}] ✅ Clicked 'Yes' button with get_by_text locator")
                    await asyncio.sleep(2)
                    return True
                except:
                    pass
                
                # Try get_by_text for "Turn On Notifications"
                try:
                    turn_on_locator = page.get_by_text("Turn On Notifications", exact=False)
                    await turn_on_locator.click(timeout=3000)
                    self.log(f"[{account_username}] ✅ Clicked 'Turn On Notifications' button with get_by_text locator")
                    await asyncio.sleep(2)
                    return True
                except:
                    pass
                    
            except Exception as e:
                self.log(f"[{account_username}] Modern locators failed: {str(e)[:100]}")
            
            self.log(f"[{account_username}] ℹ️ No notifications popup found or already dismissed")
            return False
            
        except Exception as e:
            self.log(f"[{account_username}] Error handling notifications popup: {str(e)}", "WARNING")
            return False
    
    async def login_instagram(self, page, username, password, totp_secret='', account_number=1):
        """Login to Instagram with improved error handling and 2FA support"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.log(f"[{username}] Login attempt {attempt + 1}/{max_retries}")
                
                # Add human-like delay between attempts
                if attempt > 0:
                    delay = random.uniform(5, 10)
                    self.log(f"[{username}] Waiting {delay:.1f}s before retry attempt...")
                    await asyncio.sleep(delay)
                
                # Navigate to Instagram
                if not await self.safe_goto(page, INSTAGRAM_URL):
                    self.log(f"[{username}] Failed to load Instagram", "ERROR")
                    if attempt < max_retries - 1:
                        continue
                    return False
                
                # Wait for page to fully load with human-like delay
                await asyncio.sleep(random.uniform(2, 4))
                
                # Check if already logged in
                home_indicators = [
                    "nav[aria-label='Primary navigation']",
                    "[aria-label='Home']",
                    "svg[aria-label='Home']",
                    "a[href='/']"
                ]
                
                for indicator in home_indicators:
                    if await page.query_selector(indicator):
                        self.log(f"[{username}] Already logged in")
                        return True
                
                # Check for suspended account or immediate redirects
                current_url = page.url
                if any(indicator in current_url.lower() for indicator in ["suspended", "challenge", "checkpoint"]):
                    # Skip auth_platform as it might be 2FA
                    if "auth_platform" not in current_url.lower():
                        self.log(f"[{username}] Account issue detected immediately: {current_url[:100]}...", "ERROR")
                        return False
                
                # If we're on a 2FA page immediately, handle it
                if await self.is_verification_required(page):
                    self.log(f"[{username}] 2FA required immediately - attempting automatic resolution")
                    if totp_secret and totp_secret.strip():
                        return await self.handle_2fa_verification(page, username, totp_secret, account_number, retry_attempt=0)
                    else:
                        self.log(f"[{username}] ❌ 2FA required but no TOTP secret configured", "ERROR")
                        return False
                
                # Find login form with better detection
                login_form_found = False
                
                # Wait for login form to appear
                try:
                    await page.wait_for_selector("input[name='username']", timeout=10000)
                    login_form_found = True
                except:
                    # Try to navigate to login page
                    login_selectors = [
                        "a[href='/accounts/login/']",
                        "a:has-text('Log In')",
                        "a:has-text('Log in')",
                        "button:has-text('Log In')",
                        "button:has-text('Log in')"
                    ]
                    
                    for selector in login_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                await element.click()
                                await asyncio.sleep(3)
                                try:
                                    await page.wait_for_selector("input[name='username']", timeout=5000)
                                    login_form_found = True
                                    break
                                except:
                                    continue
                        except:
                            continue
                
                if not login_form_found:
                    self.log(f"[{username}] Login form not found after attempts", "ERROR")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    return False
                
                # Fill login form
                try:
                    # Wait for form elements to be ready
                    await asyncio.sleep(1)
                    
                    username_input = await page.query_selector("input[name='username']")
                    if username_input:
                        await username_input.click()
                        await asyncio.sleep(0.3)
                        # Clear field using keyboard shortcuts
                        await username_input.press("Control+A")
                        await username_input.press("Delete")
                        await asyncio.sleep(0.2)
                        await username_input.type(username, delay=50)
                        await asyncio.sleep(0.5)
                    else:
                        raise Exception("Username input field not found")
                    
                    password_input = await page.query_selector("input[name='password']")
                    if password_input:
                        await password_input.click()
                        await asyncio.sleep(0.3)
                        # Clear field using keyboard shortcuts
                        await password_input.press("Control+A")
                        await password_input.press("Delete")
                        await asyncio.sleep(0.2)
                        await password_input.type(password, delay=50)
                        await asyncio.sleep(0.5)
                    else:
                        raise Exception("Password input field not found")
                    
                    # Submit form with better button detection
                    submit_button_clicked = False
                    submit_selectors = [
                        "button[type='submit']",
                        "button:has-text('Log In')",
                        "button:has-text('Log in')",
                        "div[role='button']:has-text('Log In')",
                        "div[role='button']:has-text('Log in')"
                    ]
                    
                    for selector in submit_selectors:
                        try:
                            button = await page.query_selector(selector)
                            if button:
                                await button.click()
                                submit_button_clicked = True
                                break
                        except:
                            continue
                    
                    if not submit_button_clicked:
                        # Fallback to pressing Enter
                        await password_input.press("Enter")
                    
                    # Wait for login to complete with loading indicators
                    self.log(f"[{username}] Submitting login form...")
                    await asyncio.sleep(3)
                    
                    # Wait for navigation or error messages
                    try:
                        await asyncio.sleep(5)  # Give time for login processing
                    except:
                        pass
                    
                    # Check login result with better detection
                    current_url = page.url
                    
                    # Check if we're on the "Save your login info?" page first
                    if "accounts/onetap" in current_url:
                        self.log(f"[{username}] Handling 'Save your login info?' dialog...")
                        if await self.handle_login_info_save_dialog(page, username):
                            # After handling the dialog, wait and check for success indicators
                            await asyncio.sleep(3)
                            current_url = page.url
                    
                    # First check if verification is required
                    if await self.is_verification_required(page):
                        # This is the proper way to handle 2FA - automatically attempt it instead of manual intervention
                        self.log(f"[{username}] 2FA verification required")
                        
                        if totp_secret and totp_secret.strip():
                            # Attempt automatic 2FA with TOTP
                            if await self.handle_2fa_verification(page, username, totp_secret, account_number, retry_attempt=0):
                                return True
                            else:
                                # If first attempt fails, try once more with a new TOTP code and better timing
                                self.log(f"[{username}] First 2FA attempt failed, retrying with new TOTP code...")
                                await asyncio.sleep(random.uniform(5, 8))  # Longer delay before retry
                                if await self.handle_2fa_verification(page, username, totp_secret, account_number, retry_attempt=1):
                                    return True
                                else:
                                    self.log(f"[{username}] ❌ 2FA verification failed after retry", "ERROR")
                                    return False
                        else:
                            self.log(f"[{username}] ❌ 2FA required but no TOTP secret configured for this account", "ERROR")
                            return False
                    
                    # Check for success indicators
                    success_indicators = [
                        "nav[aria-label='Primary navigation']",
                        "[aria-label='Home']",
                        "svg[aria-label='Home']",
                        "[data-testid='mobile-nav-home']"
                    ]
                    
                    for indicator in success_indicators:
                        if await page.query_selector(indicator):
                            self.log(f"[{username}] ✅ Login successful!")
                            return True
                    
                    # Check for error messages
                    error_selectors = [
                        "#slfErrorAlert",
                        "[role='alert']",
                        "p:has-text('incorrect')",
                        "div:has-text('incorrect')",
                        "div:has-text('password you entered is incorrect')",
                        "div:has-text('user not found')"
                    ]
                    
                    error_found = False
                    for selector in error_selectors:
                        if await page.query_selector(selector):
                            error_found = True
                            self.log(f"[{username}] ❌ Login credentials incorrect", "WARNING")
                            break
                    
                    if not error_found:
                        self.log(f"[{username}] ⚠️  Login status unclear, URL: {current_url[:100]}...", "WARNING")
                        # If we're still on instagram.com, might be rate limited
                        if "instagram.com" in current_url and "login" not in current_url:
                            self.log(f"[{username}] Possible rate limiting detected", "WARNING")
                        
                except Exception as e:
                    self.log(f"[{username}] Login form error: {e}", "WARNING")
                
            except Exception as e:
                self.log(f"[{username}] Login attempt {attempt + 1} failed: {e}", "ERROR")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(3, 5))
                    continue
                return False
        
        return False
    
    def generate_totp_code(self, username, totp_secret, wait_for_new_window=False):
        """Generate TOTP code for Instagram 2FA with timing optimization"""
        try:
            if not totp_secret or totp_secret.strip() == '':
                self.log(f"[{username}] No TOTP secret configured for this account", "WARNING")
                return None
            
            # Clean the secret - remove spaces and convert to uppercase
            cleaned_secret = totp_secret.strip().replace(' ', '').upper()
            
            # Validate the secret format (should be base32)
            if not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567' for c in cleaned_secret):
                self.log(f"[{username}] Invalid TOTP secret format - must be base32", "ERROR")
                return None
            
            # Check length (support both 16 and 32 character secrets)
            if len(cleaned_secret) not in [16, 32]:
                self.log(f"[{username}] Invalid TOTP secret length (must be 16 or 32 characters)", "ERROR")
                return None
            
            # Create TOTP object
            totp = pyotp.TOTP(cleaned_secret)
            
            # If waiting for new window, check timing
            if wait_for_new_window:
                import time
                current_time = int(time.time())
                time_in_window = current_time % 30
                
                # If we're too close to window change (within 5 seconds), wait for new window
                if time_in_window > 25:
                    wait_time = 30 - time_in_window + random.uniform(1, 3)
                    self.log(f"[{username}] Waiting {wait_time:.1f}s for fresh TOTP window...")
                    import time
                    time.sleep(wait_time)
                # If we're very early in window (within 5 seconds), also wait a bit
                elif time_in_window < 5:
                    wait_time = random.uniform(2, 4)
                    self.log(f"[{username}] Waiting {wait_time:.1f}s for TOTP window to stabilize...")
                    import time
                    time.sleep(wait_time)
            
            # Generate the TOTP code
            otp_code = totp.now()
            
            # Get time remaining in current window for logging
            import time
            current_time = int(time.time())
            time_remaining = 30 - (current_time % 30)
            
            self.log(f"[{username}] Generated TOTP code (valid for {time_remaining}s)")
            return otp_code
            
        except Exception as e:
            self.log(f"[{username}] TOTP generation failed: {e}", "ERROR")
            return None
    
    async def handle_2fa_verification(self, page, username, totp_secret, account_number=1, retry_attempt=0):
        """Handle Instagram 2FA verification automatically with improved timing."""
        try:
            self.log(f"[{username}] 2FA verification required...")
            
            # Add human-like delay before generating TOTP
            await asyncio.sleep(random.uniform(2, 4))
            
            # Generate TOTP code with timing optimization for retries
            wait_for_new_window = retry_attempt > 0
            otp_code = self.generate_totp_code(username, totp_secret, wait_for_new_window)
            if not otp_code:
                self.log(f"[{username}] Cannot generate TOTP code", "ERROR")
                return False
            
            # Human-like delay before interacting with the page
            await asyncio.sleep(random.uniform(3, 5))

            # Enhanced verification selectors with more options
            verification_selectors = [
                'input[name="verificationCode"]',
                'input[aria-label="Security Code"]',
                'input[aria-describedby="verificationCodeDescription"]',
                'input[type="tel"][maxlength="8"]',
                'input[autocomplete="off"][maxlength="8"]',
                'input[class*="aa4b"][type="tel"]',
                'input[placeholder*="code"]',
                'input[placeholder*="Code"]',
                'input[data-testid="2fa-input"]',
                'input[type="text"][maxlength="6"]',
                'input[type="text"][maxlength="8"]',
                'input[class*="verification"]',
                'input[id*="verificationCode"]'
            ]
            
            verification_input = None
            # Try each selector with extended timeout for retry attempts
            timeout = 20000 if retry_attempt > 0 else 15000
            
            for i, selector in enumerate(verification_selectors):
                try:
                    self.log(f"[{username}] Trying verification selector {i+1}: {selector}")
                    verification_input = await page.wait_for_selector(selector, timeout=timeout)
                    if verification_input and await verification_input.is_visible():
                        self.log(f"[{username}] Found verification input field with selector: {selector}")
                        break
                    else:
                        verification_input = None
                except Exception as e:
                    self.log(f"[{username}] Selector {i+1} failed: {str(e)[:100]}")
                    continue
            
            if not verification_input:
                # Final attempt - check if we're still on a 2FA page
                current_url = page.url
                if not await self.is_verification_required(page):
                    self.log(f"[{username}] No longer on verification page - may have already passed", "INFO")
                    return True
                
                self.log(f"[{username}] Could not find verification code input field after trying all selectors", "ERROR")
                self.log(f"[{username}] Current URL: {current_url}", "ERROR")
                return False
            
            # Human-like interaction with the input field
            await verification_input.focus()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Clear the field properly with multiple methods
            try:
                await verification_input.press("Control+A")
                await asyncio.sleep(random.uniform(0.3, 0.5))
                await verification_input.press("Delete")
                await asyncio.sleep(random.uniform(0.5, 0.8))
            except:
                # Alternative clearing method
                try:
                    await verification_input.fill("")
                    await asyncio.sleep(random.uniform(0.3, 0.5))
                except:
                    pass
            
            # Type the code with human-like delay between characters
            for char in otp_code:
                await verification_input.type(char)
                await asyncio.sleep(random.uniform(0.15, 0.35))
            
            # Human-like pause before submitting
            await asyncio.sleep(random.uniform(1.5, 2.5))
            self.log(f"[{username}] Entered TOTP code")
            
            submit_selectors = [
                'button:has-text("Confirm")',
                'button[type="submit"]',
                'div[role="button"]:has-text("Confirm")',
                'button:has-text("Submit")',
                'div[role="button"]:has-text("Submit")',
                'button._aswp._aswr._aswu._asw_._asx2',
                'button[class*="_aswp"][class*="_aswr"][class*="_aswu"][class*="_asw_"][class*="_asx2"]',
                '[role="button"]:has-text("Confirm")',
                '[role="button"]:has-text("Submit")'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = await page.query_selector(selector)
                    if submit_button and await submit_button.is_visible():
                        await submit_button.click()
                        self.log(f"[{username}] Submitted 2FA code with selector: {selector}")
                        # Longer wait to let Instagram process the verification
                        await asyncio.sleep(random.uniform(8, 12))
                        
                        if not await self.is_verification_required(page):
                            self.log(f"[{username}] ✅ 2FA verification successful!")
                            return True
                        else:
                            self.log(f"[{username}] ❌ 2FA verification failed.")
                            return False
                        break
                except Exception as e:
                    self.log(f"[{username}] Error with submit selector {selector}: {e}")
                    continue
            
            # Fallback if button not found or clicked
            if not submit_button:
                self.log(f"[{username}] Could not find submit button, trying to press Enter.")
                await verification_input.press("Enter")
                await asyncio.sleep(random.uniform(8, 12))
                if not await self.is_verification_required(page):
                    self.log(f"[{username}] ✅ 2FA verification successful! (with Enter key)")
                    return True
                else:
                    self.log(f"[{username}] ❌ 2FA verification failed. (with Enter key)")
                    return False

        except Exception as e:
            self.log(f"[{username}] Error during 2FA: {e}", "ERROR")
            return False
    
    async def login_instagram_with_cookies_and_2fa(self, context, username, password, totp_secret='', account_number=1):
        """Enhanced login with cookie management and automatic 2FA handling"""
        try:
            # Use the enhanced authentication system
            self.log(f"[{username}] 🔐 Starting enhanced authentication...")
            
            # Create a log callback for the authentication system
            def auth_log_callback(message):
                self.log(f"[{username}] {message}")
            
            # Use enhanced authentication with cookies and proxy
            success, auth_info = await enhanced_auth.authenticate_with_cookies_and_proxy(
                context=context,
                username=username,
                password=password,
                log_callback=auth_log_callback
            )
            
            if success:
                self.log(f"[{username}] ✅ Authentication successful!")
                self.log(f"[{username}] 📊 Method: {auth_info.get('authentication_method', 'unknown')}")
                self.log(f"[{username}] 🍪 Cookies loaded: {auth_info.get('cookies_loaded', False)}")
                self.log(f"[{username}] 💾 Cookies saved: {auth_info.get('cookies_saved', False)}")
                return True
            else:
                self.log(f"[{username}] ❌ Authentication failed")
                if auth_info.get('errors'):
                    for error in auth_info['errors']:
                        self.log(f"[{username}] ❌ Error: {error}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"[{username}] ❌ Login error: {e}", "ERROR")
            return False
    
    async def send_dm(self, page, username, message):
        """Send DM to user with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.log(f"Sending DM to @{username} (attempt {attempt + 1}/{max_retries})")
                
                # Navigate to profile
                if not await self.safe_goto(page, f"{INSTAGRAM_URL}{username}/"):
                    return "NAVIGATION_FAILED"
                
                # Check if profile exists
                if await page.query_selector("text=Sorry, this page isn't available."):
                    return "USER_NOT_FOUND"
                
                # Wait for profile to load
                try:
                    await page.wait_for_selector("header, main, article", timeout=20000)
                except:
                    return "PROFILE_LOAD_TIMEOUT"
                
                # Find and click message button
                message_clicked = False
                
                message_button_selectors = [
                    "button:has-text('Message')",
                    "div[role='button']:has-text('Message')", 
                    "[aria-label='Message']",
                    "a:has-text('Message')",
                    "button:has-text('Send message')",
                    "div[role='button']:has-text('Send message')",
                    # Additional selectors for message button
                    "a[href*='/direct/']",
                    "button[class*='_acan'][class*='_acao']"  # Instagram button classes
                ]
                
                for selector in message_button_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            await element.click()
                            message_clicked = True
                            await asyncio.sleep(2)
                            self.log(f"Clicked message button for @{username}")
                            break
                    except:
                        continue
                
                if not message_clicked:
                    if attempt < max_retries - 1:
                        self.log(f"Message button not found for @{username}, retrying in 3 seconds...")
                        await asyncio.sleep(3)
                        continue
                    return "MESSAGE_BUTTON_NOT_FOUND"
                
                # Wait for DM interface to load
                await asyncio.sleep(3)
                
                # Find message input with updated selectors based on the provided element
                input_selectors = [
                    # New selectors based on the provided element
                    'div[aria-label="Message"][contenteditable="true"][role="textbox"]',
                    'div[aria-describedby="Message"][contenteditable="true"]',
                    'div[class*="xzsf02u"][contenteditable="true"][role="textbox"]',
                    'div[data-lexical-editor="true"][contenteditable="true"]',
                    'div[aria-placeholder="Message..."][contenteditable="true"]',
                    # Original selectors as fallback
                    "div[role='textbox']",
                    "div[contenteditable='true']",
                    "textarea[placeholder*='Message']",
                    "textarea[placeholder*='message']",
                    # Additional Instagram-specific selectors
                    'div[role="textbox"][contenteditable="true"]',
                    'div[contenteditable="true"][spellcheck="true"]',
                    'div[class*="notranslate"][contenteditable="true"]'
                ]
                
                message_input = None
                for i, selector in enumerate(input_selectors):
                    try:
                        self.log(f"Trying message input selector {i+1}: {selector}")
                        message_input = await page.wait_for_selector(selector, timeout=5000)
                        if message_input:
                            # Verify the element is visible and interactable
                            is_visible = await message_input.is_visible()
                            if is_visible:
                                self.log(f"Found message input field with selector {i+1}")
                                break
                            else:
                                self.log(f"Message input found but not visible with selector {i+1}")
                                message_input = None
                    except Exception as e:
                        self.log(f"Selector {i+1} failed: {e}")
                        continue
                
                if not message_input:
                    if attempt < max_retries - 1:
                        self.log(f"Message input field not found for @{username}, retrying in 5 seconds...")
                        await asyncio.sleep(5)
                        continue
                    return "INPUT_FIELD_ERROR"
                
                # Type and send message
                try:
                    self.log(f"Typing message to @{username}")
                    await message_input.click()
                    await asyncio.sleep(0.5)
                    
                    # Clear any existing content
                    await message_input.press("Control+A")
                    await asyncio.sleep(0.2)
                    await message_input.press("Delete")
                    await asyncio.sleep(0.3)
                    
                    # Type the message
                    await message_input.type(message, delay=50)
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    # Send the message
                    await message_input.press("Enter")
                    await asyncio.sleep(2)
                    
                    self.log(f"Message sent to @{username}")
                    return True
                    
                except Exception as e:
                    self.log(f"Error typing/sending message to @{username}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3)
                        continue
                    return "MESSAGE_SEND_ERROR"
                
            except Exception as e:
                self.log(f"DM send error for @{username} (attempt {attempt + 1}): {e}", "ERROR")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                    continue
                return f"GENERAL_ERROR: {e}"
        
        return "MAX_RETRIES_EXCEEDED"
    
    async def check_dm_responses(self, page, account_username):
        """Check for unread messages in DM inbox (simple and fast)"""
        try:
            self.log(f"[{account_username}] Checking for unread messages...")
            
            # Navigate to direct messages
            if not await self.safe_goto(page, f"{INSTAGRAM_URL}direct/inbox/"):
                self.log(f"[{account_username}] Failed to navigate to DM inbox", "WARNING")
                return []
            
            await asyncio.sleep(3)
            
            # Handle "Turn On Notifications" popup if it appears
            await self.handle_notifications_popup(page, account_username)
            
            # Wait for inbox to load
            try:
                await page.wait_for_selector("div[role='main'], div[role='grid']", timeout=15000)
            except:
                self.log(f"[{account_username}] Inbox load timeout", "WARNING")
                return []
            
            responses = []
            
            # Look for unread message indicators (Instagram shows unread conversations differently)
            unread_selectors = [
                "div[role='listitem']:has(div[class*='unread'])",  # Conversations with unread indicators
                "div[role='listitem']:has(span[class*='badge'])",   # Conversations with notification badges  
                "div[role='listitem']:has(div[style*='font-weight: bold'])", # Bold text indicates unread
                "a[href*='/direct/t/']:has(div[class*='unread'])", # Direct links with unread markers
            ]
            
            unread_conversations = []
            for selector in unread_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        unread_conversations.extend(elements)
                except:
                    continue
            
            # If no specific unread indicators found, check first few conversations
            if not unread_conversations:
                try:
                    all_conversations = await page.query_selector_all("div[role='listitem']")
                    unread_conversations = all_conversations[:5]  # Check first 5 conversations
                except:
                    pass
            
            if not unread_conversations:
                self.log(f"[{account_username}] No conversations found in inbox", "INFO")
                return []
            
            self.log(f"[{account_username}] Found {len(unread_conversations)} potential unread conversations")
            
            # Check each unread conversation
            for i, conversation in enumerate(unread_conversations[:10]):  # Limit to 10 for speed
                try:
                    # Click on conversation
                    await conversation.click()
                    await asyncio.sleep(1)  # Reduced wait time
                    
                    # Get username from conversation header
                    username_selectors = [
                        "header h1", "header span", 
                        "div[role='button'] span", 
                        "a[role='link'] span"
                    ]
                    
                    conversation_username = "Unknown"
                    for selector in username_selectors:
                        try:
                            username_element = await page.query_selector(selector)
                            if username_element:
                                username_text = await username_element.inner_text()
                                if username_text and len(username_text.strip()) > 0:
                                    conversation_username = username_text.strip()
                                    break
                        except:
                            continue
                    
                    # Get the latest message (assume it's unread)
                    message_selectors = [
                        "div[data-testid='message-text']",
                        "div[class*='message'] span",
                        "div[role='row'] div span"
                    ]
                    
                    latest_message = ""
                    for selector in message_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            if elements:
                                # Get the last message
                                last_element = elements[-1]
                                latest_message = await last_element.inner_text()
                                if latest_message and len(latest_message.strip()) > 0:
                                    break
                        except:
                            continue
                    
                    # Store any message found (we're not filtering, just collecting)
                    if latest_message and len(latest_message.strip()) > 0:
                        response_data = {
                            'account': account_username,
                            'responder': conversation_username,
                            'message': latest_message.strip(),
                            'timestamp': datetime.now().isoformat()
                        }
                        responses.append(response_data)
                        self.log(f"[{account_username}] 📩 Response from {conversation_username}: {latest_message[:50]}...", "INFO")
                    
                    # Go back to inbox quickly
                    await page.go_back()
                    await asyncio.sleep(0.5)  # Reduced wait time
                    
                except Exception as e:
                    self.log(f"[{account_username}] Error checking conversation {i+1}: {e}", "WARNING")
                    # Try to go back to inbox if we're stuck
                    try:
                        await page.go_back()
                        await asyncio.sleep(0.5)
                    except:
                        break
                    continue
            
            self.log(f"[{account_username}] Collected {len(responses)} responses")
            return responses
            
        except Exception as e:
            self.log(f"[{account_username}] Error checking responses: {e}", "ERROR")
            return []
    
    def distribute_users(self, users, num_accounts):
        """Distribute users across accounts"""
        distributed = [[] for _ in range(num_accounts)]
        for i, user in enumerate(users):
            distributed[i % num_accounts].append(user)
        return distributed
    
    async def process_account(self, account_data, assigned_users, prompt_template, dm_limit, account_number=1):
        """Process DMs for single account with enhanced error handling"""
        username = account_data.get('username')
        password = account_data.get('password')
        
        playwright = None
        browser = None
        context = None
        
        try:
            # Get the assigned proxy for this account
            proxy_string = self.get_account_proxy(username)
            if not proxy_string:
                self.log(f"[{username}] No proxy assigned to this account", "WARNING")
            else:
                proxy_info = self.parse_proxy(proxy_string)
                if proxy_info:
                    self.log(f"[{username}] Using assigned proxy: {proxy_info['host']}:{proxy_info['port']}")
            
            self.log(f"[{username}] Starting with {len(assigned_users)} users (limit: {dm_limit})")
            
            # Setup browser with assigned proxy
            playwright, browser, context = await self.setup_browser(proxy_string, account_number)
            page = await context.new_page()
            
            # Login with enhanced cookie management and 2FA support
            totp_secret = account_data.get('totp_secret', '')
            if not await self.login_instagram_with_cookies_and_2fa(context, username, password, totp_secret, account_number):
                self.log(f"[{username}] Login failed", "ERROR")
                return {"account": username, "sent": 0, "processed": 0, "error": "Login failed"}
            
            # Get the page after successful authentication
            page = await context.new_page()
            await page.goto("https://www.instagram.com/", wait_until='domcontentloaded')
            
            sent_count = 0
            processed_count = 0
            
            # Process users up to limit
            users_to_process = assigned_users[:dm_limit]
            
            for user in users_to_process:
                # Check if browser is still connected (closed detection)
                try:
                    if not browser.is_connected():
                        self.log(f"[{username}] Browser was closed manually - stopping automation", "WARNING")
                        return {"account": username, "sent": sent_count, "processed": processed_count, "error": "Browser closed manually"}
                except:
                    # If we can't check browser status, assume it's closed
                    self.log(f"[{username}] Browser connection lost - stopping automation", "WARNING") 
                    return {"account": username, "sent": sent_count, "processed": processed_count, "error": "Browser connection lost"}
                
                if self.stop_callback():
                    self.log(f"[{username}] Stopped by user request", "WARNING")
                    break
                
                processed_count += 1
                target_username = user.get('username', '')
                
                # Skip if no username found
                if not target_username or target_username.strip() == '':
                    self.log(f"[{username}] ⚠️ Skipping user {processed_count} - no username found", "WARNING")
                    continue
                
                target_username = target_username.strip()
                
                # Generate personalized message
                message = self.generate_message(user, prompt_template)
                
                # Send DM
                result = await self.send_dm(page, target_username, message)
                
                if result is True:
                    sent_count += 1
                    self.log(f"[{username}] ✅ DM sent to @{target_username} ({sent_count}/{dm_limit})", "SUCCESS")
                    
                    # Save to sent DMs log
                    with csv_lock:
                        self.sent_dms.append({
                            'timestamp': datetime.now().isoformat(),
                            'bot_account': username,
                            'target_username': target_username,
                            'message': message,
                            'status': 'sent'
                        })
                elif result == "USER_NOT_FOUND":
                    self.log(f"[{username}] ❌ Profile @{target_username} not found or not accessible", "WARNING")
                elif result == "MESSAGE_BUTTON_NOT_FOUND":
                    self.log(f"[{username}] ❌ Cannot send DM to @{target_username} - message button not available (private account or restricted?)", "WARNING")
                elif result == "NAVIGATION_FAILED":
                    self.log(f"[{username}] ❌ Failed to navigate to @{target_username} profile", "WARNING")
                elif result == "PROFILE_LOAD_TIMEOUT":
                    self.log(f"[{username}] ❌ Profile @{target_username} load timeout", "WARNING")
                elif result == "INPUT_FIELD_ERROR":
                    self.log(f"[{username}] ❌ Could not find message input field for @{target_username}", "WARNING")
                elif result == "MESSAGE_SEND_ERROR":
                    self.log(f"[{username}] ❌ Error typing/sending message to @{target_username}", "WARNING")
                elif result == "MAX_RETRIES_EXCEEDED":
                    self.log(f"[{username}] ❌ Max retries exceeded for @{target_username}", "WARNING")
                elif result.startswith("GENERAL_ERROR"):
                    self.log(f"[{username}] ❌ General error for @{target_username}: {result}", "WARNING")
                else:
                    self.log(f"[{username}] ❌ Failed to send DM to @{target_username}: {result}", "WARNING")
                
                # Rate limiting
                await asyncio.sleep(random.uniform(10, 20))
                
                if sent_count >= dm_limit:
                    break
            
            self.log(f"[{username}] Completed: {sent_count} sent out of {processed_count} processed")
            
            # Check for responses after sending all DMs
            self.log(f"[{username}] Waiting 10 seconds before checking for responses...")
            await asyncio.sleep(10)  # Reduced wait time
            
            responses = await self.check_dm_responses(page, username)
            
            # Store responses globally
            if responses:
                self.positive_responses.extend(responses)
                self.log(f"[{username}] Collected {len(responses)} positive responses!")
            
            return {
                "account": username,
                "sent": sent_count,
                "processed": processed_count,
                "responses": len(responses),
                "proxy_used": proxy_string.split(':')[0] if proxy_string else "none"
            }
            
        except Exception as e:
            self.log(f"[{username}] Processing error: {e}", "ERROR")
            return {"account": username, "sent": 0, "processed": 0, "error": str(e)}
            
        finally:
            # Cleanup browser (no need to release proxy since it's permanently assigned)
            try:
                if browser:
                    await browser.close()
                if playwright:
                    await playwright.stop()
            except:
                pass

async def run_dm_automation(
    script_id,
    accounts_file,
    target_file=None,
    prompt_file=None,
    custom_prompt=None,
    dms_per_account=30,
    log_callback=None,
    stop_callback=None
):
    """Main function to run DM automation"""
    
    engine = DMAutomationEngine(log_callback, stop_callback)
    
    try:
        engine.log("=== Instagram DM Automation Started ===")
        engine.log(f"Script ID: {script_id}")
        engine.log("") 
        engine.log("📋 ACCOUNT REQUIREMENTS:")
        engine.log("✅ Account should NOT have 2FA (Two Factor Authentication) enabled")
        engine.log("✅ Account should be verified/trusted (not flagged for suspicious activity)")  
        engine.log("✅ Account should have been logged in recently from this IP/device")
        engine.log("")
        
        # Setup AI client
        if not engine.setup_openai_client():
            engine.log("Failed to setup AI client", "ERROR")
            return False
        
        # Load data
        engine.log("Loading bot accounts...")
        bot_accounts = engine.load_accounts(accounts_file)
        
        if not bot_accounts:
            engine.log("No valid bot accounts found", "ERROR")
            return False
        
        # Use all accounts from the file dynamically
        engine.log(f"Using {len(bot_accounts)} bot accounts (all accounts from file)")

        engine.log("Loading target users...")
        target_users = engine.load_target_users(target_file)
        
        if not target_users:
            engine.log("No target users found", "ERROR")
            return False
        
        # Load DM prompt
        prompt_template = engine.load_dm_prompt(prompt_file, custom_prompt)
        
        engine.log(f"Configuration:")
        engine.log(f"- Bot accounts: {len(bot_accounts)}")
        engine.log(f"- Target users: {len(target_users)}")
        engine.log(f"- DMs per account: {dms_per_account}")
        engine.log(f"- Total target DMs: {len(bot_accounts) * dms_per_account}")
        
        # Distribute users across accounts
        user_distribution = engine.distribute_users(target_users, len(bot_accounts))
        
        engine.log("Starting parallel DM campaigns...")
        
        # Create tasks for parallel processing
        tasks = []
        for i, (account, assigned_users) in enumerate(zip(bot_accounts, user_distribution), 1):
            if assigned_users:
                task = engine.process_account(account, assigned_users, prompt_template, dms_per_account, i)
                tasks.append(task)
        
        # Run parallel processing
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if any browser was closed manually (early termination)
        browser_closed_manually = False
        for result in results:
            if isinstance(result, dict) and result.get('error') in ['Browser closed manually', 'Browser connection lost']:
                browser_closed_manually = True
                engine.log("⚠️ Browser was closed manually - stopping automation", "WARNING")
                break
        
        if browser_closed_manually:
            engine.log("❌ Automation stopped due to browser closure", "ERROR")
            return False  # This will trigger automatic script stopping
        
        # Calculate final results
        total_sent = 0
        total_processed = 0
        total_responses = 0
        successful_accounts = 0
        
        engine.log("\n=== FINAL RESULTS ===")
        
        for i, result in enumerate(results):
            if isinstance(result, dict):
                account = result.get('account', f'Account_{i+1}')
                sent = result.get('sent', 0)
                processed = result.get('processed', 0)
                responses = result.get('responses', 0)
                error = result.get('error')
                
                if error:
                    engine.log(f"❌ {account}: Error - {error}", "ERROR")
                else:
                    response_text = f" | {responses} responses" if responses > 0 else ""
                    engine.log(f"✅ {account}: {sent}/{processed} DMs sent{response_text}")
                    successful_accounts += 1
                
                total_sent += sent
                total_processed += processed
                total_responses += responses
            else:
                engine.log(f"❌ Task failed: {result}", "ERROR")
        
        engine.log(f"\n📊 SUMMARY:")
        engine.log(f"- Total DMs sent: {total_sent}")
        engine.log(f"- Total targets processed: {total_processed}")
        engine.log(f"- Total positive responses: {total_responses}")
        engine.log(f"- Response rate: {(total_responses/total_sent)*100:.1f}%" if total_sent > 0 else "0%")
        engine.log(f"- Success rate: {(total_sent/total_processed)*100:.1f}%" if total_processed > 0 else "0%")
        engine.log(f"- Successful accounts: {successful_accounts}/{len(bot_accounts)}")
        
        # Save results
        if engine.sent_dms:
            try:
                import os
                results_file = os.path.join('logs', f'dm_results_{script_id}.csv')
                os.makedirs('logs', exist_ok=True)
                
                with open(results_file, 'w', newline='', encoding='utf-8') as f:
                    if engine.sent_dms:
                        fieldnames = engine.sent_dms[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(engine.sent_dms)
                
                engine.log(f"Results saved to: {results_file}")
            except Exception as e:
                engine.log(f"Failed to save results: {e}", "WARNING")
        
        # Save positive responses
        if engine.positive_responses:
            try:
                import os
                responses_file = os.path.join('logs', f'dm_responses_{script_id}.csv')
                
                with open(responses_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = engine.positive_responses[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(engine.positive_responses)
                
                engine.log(f"Positive responses saved to: {responses_file}")
                
                # Also save as JSON for API access
                responses_json_file = os.path.join('logs', f'dm_responses_{script_id}.json')
                with open(responses_json_file, 'w', encoding='utf-8') as f:
                    json.dump(engine.positive_responses, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                engine.log(f"Failed to save positive responses: {e}", "WARNING")
        
        engine.log("=== DM Automation Completed ===")
        return total_sent > 0
        
    except Exception as e:
        engine.log(f"DM Automation failed: {e}", "ERROR")
        import traceback
        engine.log(f"Traceback: {traceback.format_exc()}", "ERROR")
        return False
