# import asyncio
# import pandas as pd
# from playwright.async_api import async_playwright, TimeoutError
# import os
# import glob
# import time
# import random
# from pathlib import Path
# import logging
# import pyotp
# import re
# import datetime
# import traceback
# from instagram_accounts import get_account_details
# from proxy_manager import proxy_manager
# from enhanced_instagram_auth import enhanced_auth
# from instagram_cookie_manager import cookie_manager

# class InstagramDailyPostAutomation:
#     def __init__(self, script_id, log_callback=None, stop_flag_callback=None):
#         self.script_id = script_id
#         self.log_callback = log_callback or self.default_log
#         self.stop_flag_callback = stop_flag_callback or (lambda: False)
#         self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
#         self.supported_video_formats = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']
#         self.media_file = None
#         self.is_video = False
        
#     def default_log(self, message, level="INFO"):
#         """Default logging function with timestamp"""
#         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         formatted_message = f"[{timestamp}] [{level}] {message}"
#         print(formatted_message, flush=True)
        
#     def log(self, message, level="INFO"):
#         """Log message using the callback with timestamp"""
#         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         formatted_message = f"[{timestamp}] [{level}] {message}"
#         self.log_callback(formatted_message, level)

#     async def generate_totp_code(self, username, totp_secret):
#         """Generate TOTP code for 2FA authentication"""
#         try:
#             if not totp_secret:
#                 self.log(f"[{username}] ℹ️ No TOTP secret provided", "INFO")
#                 return None
                
#             # Clean the secret (remove spaces and convert to uppercase)
#             clean_secret = totp_secret.strip().replace(' ', '').upper()
            
#             # Validate secret length (16 or 32 characters for base32)
#             if len(clean_secret) not in [16, 32]:
#                 self.log(f"[{username}] ❌ Invalid TOTP secret length: {len(clean_secret)} (must be 16 or 32 characters)", "ERROR")
#                 return None
                
#             # Validate base32 format
#             if not re.match(r'^[A-Z2-7=]+$', clean_secret):
#                 self.log(f"[{username}] ❌ Invalid TOTP secret format (must be base32)", "ERROR")
#                 return None
            
#             # Generate TOTP code
#             totp = pyotp.TOTP(clean_secret)
#             code = totp.now()
            
#             self.log(f"[{username}] ✅ Generated TOTP code: {code} (secret length: {len(clean_secret)})", "INFO")
#             return code
            
#         except Exception as e:
#             self.log(f"[{username}] ❌ Error generating TOTP code: {e}", "ERROR")
#             return None

#     async def handle_2fa_verification(self, page, username, totp_secret):
#         """Handle Instagram 2FA verification using TOTP."""
#         try:
#             self.log(f"[{username}] 🔐 2FA verification required...")
            
#             # Generate TOTP code
#             totp_code = await self.generate_totp_code(username, totp_secret)
#             if not totp_code:
#                 self.log(f"[{username}] ❌ Could not generate TOTP code.")
#                 return False
            
#             await self.human_delay(1000, 2000)

#             # Look for 2FA input field
#             totp_selectors = [
#                 'input[name="verificationCode"]',
#                 'input[name="security_code"]',
#                 'input[aria-label*="security code"]',
#                 'input[placeholder*="security code"]',
#                 'input[placeholder*="verification code"]',
#                 '[data-testid="2fa-input"]',
#                 'input[type="text"][maxlength="6"]',
#                 'input[autocomplete="one-time-code"]',
#                 'input[aria-label="Security Code"]',
#                 'input[aria-describedby="verificationCodeDescription"]',
#                 'input[type="tel"][maxlength="8"]',
#                 'input[autocomplete="off"][maxlength="8"]',
#                 'input[class*="aa4b"][type="tel"]'
#             ]
            
#             totp_input = None
#             for selector in totp_selectors:
#                 try:
#                     totp_input = await page.wait_for_selector(selector, timeout=5000)
#                     if totp_input:
#                         self.log(f"[{username}] 📱 Found 2FA input field with selector: {selector}")
#                         break
#                 except:
#                     continue
            
#             if not totp_input:
#                 self.log(f"[{username}] ❌ Could not find 2FA input field.")
#                 return False
            
#             # Enter TOTP code
#             await totp_input.click()
#             await page.keyboard.press('Control+a')
#             await totp_input.fill(totp_code)
#             self.log(f"[{username}] ✅ Entered TOTP code: {totp_code}")
#             await self.human_delay(1500, 2500)
            
#             # Look for submit button
#             submit_selectors = [
#                 'button[type="submit"]',
#                 'button:has-text("Confirm")',
#                 'div[role="button"]:has-text("Confirm")',
#                 'button:has-text("Continue")',
#                 '[role="button"]:has-text("Continue")',
#                 'button:has-text("Submit")',
#                 'div[role="button"]:has-text("Submit")',
#                 'button:has-text("Verify")',
#                 'button._aswp._aswr._aswu._asw_._asx2',
#                 'button[class*="_aswp"][class*="_aswr"][class*="_aswu"][class*="_asw_"][class*="_asx2"]'
#             ]
            
#             submit_button = None
#             for selector in submit_selectors:
#                 try:
#                     submit_button = await page.wait_for_selector(selector, timeout=3000)
#                     if submit_button:
#                         break
#                 except:
#                     continue
            
#             if submit_button:
#                 await submit_button.click()
#                 self.log(f"[{username}] 🚀 Clicked submit button for 2FA verification")
#             else:
#                 await page.keyboard.press('Enter')
#                 self.log(f"[{username}] ⌨️ Pressed Enter for 2FA verification")
            
#             await self.human_delay(5000, 7000) # Increased delay for verification
            
#             # Check if verification was successful
#             if not await self.is_verification_required(page):
#                 self.log(f"[{username}] ✅ 2FA verification successful!")
#                 return True
#             else:
#                 self.log(f"[{username}] ❌ 2FA verification failed.")
#                 return False
                
#         except Exception as e:
#             self.log(f"[{username}] ❌ Error during 2FA verification: {e}", "ERROR")
#             return False

#     def should_stop(self):
#         """Check if the script should stop"""
#         return self.stop_flag_callback()

#     async def login_instagram_with_cookies_and_2fa(self, page, context, username, password, account_number):
#         """Enhanced login with cookie management and automatic 2FA handling
        
#         Returns:
#             tuple: (success: bool, auth_info: dict) - success status and authentication info
#                    auth_info contains 'authentication_method' ('cookies' or 'credentials')
#         """
#         try:
#             # Use the enhanced authentication system
#             self.log(f"[Account {account_number}] 🔐 Starting enhanced authentication for {username}...")
            
#             # Create a log callback for the authentication system
#             def auth_log_callback(message):
#                 self.log(f"[Account {account_number}] {message}")
            
#             # Use enhanced authentication with cookies and proxy
#             success, auth_info = await enhanced_auth.authenticate_with_cookies_and_proxy(
#                 context=context,
#                 username=username,
#                 password=password,
#                 log_callback=auth_log_callback
#             )
            
#             if success:
#                 self.log(f"[Account {account_number}] ✅ Authentication successful!")
#                 self.log(f"[Account {account_number}] 📊 Method: {auth_info.get('authentication_method', 'unknown')}")
#                 self.log(f"[Account {account_number}] 🍪 Cookies loaded: {auth_info.get('cookies_loaded', False)}")
#                 self.log(f"[Account {account_number}] 💾 Cookies saved: {auth_info.get('cookies_saved', False)}")
#                 return True, auth_info  # Return both success and auth_info
#             else:
#                 self.log(f"[Account {account_number}] ❌ Authentication failed")
#                 if auth_info.get('errors'):
#                     for error in auth_info['errors']:
#                         self.log(f"[Account {account_number}] ❌ Error: {error}", "ERROR")
#                 return False, auth_info  # Return both success and auth_info
                
#         except Exception as e:
#             self.log(f"[Account {account_number}] ❌ Login error: {e}", "ERROR")
#             return False, {'authentication_method': 'unknown', 'errors': [str(e)]}

#     def load_accounts_from_file(self, file_path):
#         """Load Instagram credentials from Excel or CSV file."""
#         try:
#             # Determine file type and read accordingly
#             if file_path.endswith('.csv'):
#                 df = pd.read_csv(file_path)
#             else:
#                 df = pd.read_excel(file_path)
            
#             if df.empty:
#                 self.log("Error: Accounts file is empty.", "ERROR")
#                 return []
            
#             # Check for required columns (case-insensitive)
#             df.columns = df.columns.str.strip().str.title()
#             required_columns = ["Username", "Password"]
#             missing_columns = [col for col in required_columns if col not in df.columns]
#             if missing_columns:
#                 self.log(f"Error: Missing columns in accounts file: {missing_columns}.", "ERROR")
#                 self.log(f"Available columns: {list(df.columns)}", "ERROR")
#                 return []
            
#             # Load accounts
#             accounts = []
#             for i in range(len(df)):
#                 username = df.loc[i, "Username"]
#                 password = df.loc[i, "Password"]
#                 if pd.notna(username) and pd.notna(password):
#                     accounts.append((str(username).strip(), str(password).strip()))
            
#             self.log(f"Loaded {len(accounts)} account(s) from file.")
#             return accounts
            
#         except FileNotFoundError:
#             self.log(f"Error: File {file_path} not found.", "ERROR")
#             return []
#         except Exception as e:
#             self.log(f"Error loading accounts: {e}", "ERROR")
#             return []

#     def set_media_file(self, media_path):
#         """Set the media file and determine if it's a video"""
#         self.media_file = media_path
#         file_ext = Path(media_path).suffix.lower()
#         self.is_video = file_ext in self.supported_video_formats
#         self.log(f"Media file set: {os.path.basename(media_path)} ({'Video' if self.is_video else 'Image'})")

#     async def human_type(self, page, selector, text, delay_range=(50, 150)):
#         """Type text with random delays"""
#         if self.should_stop():
#             return
#         element = await page.wait_for_selector(selector, state='visible')
#         await element.click()
#         await page.wait_for_timeout(random.randint(300, 800))
        
#         for char in text:
#             if self.should_stop():
#                 return
#             await element.type(char)
#             await page.wait_for_timeout(random.randint(delay_range[0], delay_range[1]))

#     async def update_visual_status(self, page, status_text, step=None):
#         """Visual status updates disabled for VPS deployment"""
#         pass  # No-op for headless mode

#     async def human_delay(self, min_ms=1000, max_ms=3000):
#         """Add human-like random delays."""
#         if self.should_stop():
#             return
#         await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)

#     async def handle_login_info_save_dialog(self, page, account_number):
#         """Handle the 'Save your login info?' dialog by clicking 'Save info' only"""
#         try:
#             self.log(f"[Account {account_number}] 🔍 Checking for 'Save login info' dialog...")
            
#             # Wait a moment for the dialog to fully load
#             await self.human_delay(2000, 3000)
            
#             # Check if we're on the save login info page
#             current_url = page.url
#             if "accounts/onetap" not in current_url:
#                 self.log(f"[Account {account_number}] ℹ️ Not on save login info page, current URL: {current_url}")
#                 return True  # Not an error, just not on that page
            
#             self.log(f"[Account {account_number}] 🔧 On save login info page - looking for 'Save info' button...")
#             self.log(f"[Account {account_number}] 📊 Page title: {await page.title()}")
            
#             # Strategy 1: Try selectors for "Save info" button only
#             simple_selectors = [
#                 # Save info button (only option now)
#                 'button.aswp._aswr._aswu._asw_._asx2:has-text("Save info")',
#                 'button:has-text("Save info")',
#                 ':text-is("Save info")',
#                 'text="Save info"',
#                 'button[type="button"]:has-text("Save info")',
#                 'div[role="button"]:has-text("Save info")',
#                 '[role="button"]:has-text("Save info")',
#                 'div:has-text("Save info")',
#                 '*:has-text("Save info")'
#             ]
            
#             # Add timeout to prevent infinite loops - max 30 seconds total
#             start_time = time.time()
#             max_duration = 30  # seconds
            
#             for i, selector in enumerate(simple_selectors):
#                 if time.time() - start_time > max_duration:
#                     self.log(f"[Account {account_number}] ⏰ Timeout reached after {max_duration} seconds", "WARNING")
#                     break
                    
#                 try:
#                     self.log(f"[Account {account_number}] 🎯 Trying selector {i+1}/{len(simple_selectors)}: {selector}")
                    
#                     # Try to find and click the element
#                     element = await page.wait_for_selector(selector, timeout=5000)
#                     if element:
#                         # Verify element is visible
#                         is_visible = await element.is_visible()
#                         if is_visible:
#                             # Get the actual text of the clicked element
#                             element_text = await element.text_content()
#                             await element.click()
#                             self.log(f"[Account {account_number}] ✅ Clicked '{element_text}' button with selector {i+1}")
                            
#                             # Wait and verify we moved away from the page
#                             await self.human_delay(3000, 4000)
                            
#                             new_url = page.url
#                             if "accounts/onetap" not in new_url:
#                                 self.log(f"[Account {account_number}] ✅ Successfully saved login info!")
#                                 self.log(f"[Account {account_number}] 📊 New URL: {new_url}")
#                                 return True
#                             else:
#                                 self.log(f"[Account {account_number}] ⚠️ Still on save login page after click, trying next selector...")
#                                 continue
#                         else:
#                             self.log(f"[Account {account_number}] ⚠️ Element found but not visible with selector {i+1}")
#                             continue
#                     else:
#                         self.log(f"[Account {account_number}] ⚠️ No element found with selector {i+1}")
#                         continue
                        
#                 except Exception as e:
#                     self.log(f"[Account {account_number}] ⚠️ Selector {i+1} failed: {str(e)[:100]}")
#                     continue
            
#             # Strategy 2: Use modern Playwright locators with timeout
#             if time.time() - start_time <= max_duration:
#                 self.log(f"[Account {account_number}] 🔄 Trying modern Playwright locators...")
                
#                 try:
#                     # Try get_by_text approach with exact match - Save info only
#                     save_info_locator = page.get_by_text("Save info", exact=True)
#                     await save_info_locator.click(timeout=5000)
#                     self.log(f"[Account {account_number}] ✅ Clicked 'Save info' button with get_by_text locator")
                    
#                     await self.human_delay(3000, 4000)
#                     new_url = page.url
#                     if "accounts/onetap" not in new_url:
#                         self.log(f"[Account {account_number}] ✅ Successfully saved login info!")
#                         return True
                        
#                 except Exception as e:
#                     self.log(f"[Account {account_number}] ⚠️ get_by_text locator failed: {str(e)[:100]}")
                
#                 try:
#                     # Try get_by_role approach - Save info only
#                     save_info_role = page.get_by_role("button", name=re.compile("save info", re.IGNORECASE))
#                     await save_info_role.click(timeout=5000)
#                     self.log(f"[Account {account_number}] ✅ Clicked 'Save info' button with get_by_role locator")
                    
#                     await self.human_delay(3000, 4000)
#                     new_url = page.url
#                     if "accounts/onetap" not in new_url:
#                         self.log(f"[Account {account_number}] ✅ Successfully saved login info!")
#                         return True
                        
#                 except Exception as e:
#                     self.log(f"[Account {account_number}] ⚠️ get_by_role locator failed: {str(e)[:100]}")
            
#             # If all strategies fail, log and continue
#             self.log(f"[Account {account_number}] ⚠️ Could not find 'Save info' button. Continuing anyway...", "WARNING")
#             return True  # Continue script execution even if button not found
            
#             # Strategy 4: Direct navigation (last resort) with timeout check
#             if time.time() - start_time <= max_duration:
#                 self.log(f"[Account {account_number}] 🏠 Final resort: Direct navigation to Instagram home...")
#                 try:
#                     await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=15000)
#                     await self.human_delay(3000, 5000)
                    
#                     final_url = page.url
#                     if final_url == "https://www.instagram.com/" or final_url.startswith("https://www.instagram.com/?"):
#                         self.log(f"[Account {account_number}] ✅ Direct navigation worked!")
#                         return True
                        
#                 except Exception as e:
#                     self.log(f"[Account {account_number}] ⚠️ Direct navigation failed: {e}")
            
#             # If we reach here, all methods failed
#             total_time = time.time() - start_time
#             self.log(f"[Account {account_number}] ❌ All methods failed to dismiss save login dialog after {total_time:.1f} seconds", "ERROR")
#             self.log(f"[Account {account_number}] 📊 Final URL: {page.url}")
            
#             # Force continue anyway to prevent infinite loops
#             self.log(f"[Account {account_number}] 🔄 Forcing continuation to prevent infinite loop...")
#             return True  # Return True to continue the script instead of failing
            
#         except Exception as e:
#             self.log(f"[Account {account_number}] ❌ Error handling save login dialog: {e}", "ERROR")
#             # Return True to continue instead of failing
#             return True

#     async def is_verification_required(self, page):
#         """Check if the current page requires verification"""
#         current_url = page.url
#         verification_indicators = [
#             "challenge",
#             "checkpoint", 
#             # "accounts/onetap" removed - this is just "Save your login info?" dialog, can be handled automatically
#             "auth_platform/codeentry",
#             "two_factor",
#             "2fa",
#             "verify",
#             "security",
#             "suspicious"
#         ]
        
#         # Check URL
#         if any(indicator in current_url.lower() for indicator in verification_indicators):
#             return True
            
#         # Check page content for verification elements
#         verification_selectors = [
#             "input[name='verificationCode']",
#             "input[name='security_code']", 
#             "[data-testid='2fa-input']",
#             "text=Enter the code",
#             "text=verification code",
#             "text=Two-factor authentication"
#         ]
        
#         for selector in verification_selectors:
#             if await page.query_selector(selector):
#                 return True
                
#         return False

#     async def instagram_post_script(self, username, password, account_number, caption=""):
#         """Main Instagram posting function for a single account."""
#         self.log(f"[Account {account_number}] 🚀 Starting automation for {username}")
#         self.log(f"[Account {account_number}] 📊 Script ID: {self.script_id}")
#         self.log(f"[Account {account_number}] 📊 Media file: {os.path.basename(self.media_file) if self.media_file else 'None'}")
        
#         if self.should_stop():
#             self.log(f"[Account {account_number}] ⚠️ Stop flag detected at start - terminating", "WARNING")
#             return None
        
#         # Validate inputs
#         if not username or not password:
#             self.log(f"[Account {account_number}] ❌ Missing username or password", "ERROR")
#             return False
            
#         if not self.media_file or not os.path.exists(self.media_file):
#             self.log(f"[Account {account_number}] ❌ Media file not found: {self.media_file}", "ERROR")
#             return False
        
#         try:
#             async with async_playwright() as p:
#                 if self.should_stop():
#                     self.log(f"[Account {account_number}] ⚠️ Stop flag detected before browser launch, terminating", "WARNING")
#                     return
                
#                 # Get assigned proxy for this account
#                 proxy_string = proxy_manager.get_account_proxy(username)
#                 proxy_config = None
                
#                 if proxy_string:
#                     proxy_info = proxy_manager.parse_proxy(proxy_string)
#                     if proxy_info:
#                         proxy_config = {
#                             'server': proxy_info['server'],
#                             'username': proxy_info['username'],
#                             'password': proxy_info['password']
#                         }
#                         self.log(f"[Account {account_number}] Using assigned proxy: {proxy_info['host']}:{proxy_info['port']}")
#                 else:
#                     self.log(f"[Account {account_number}] No proxy assigned to this account")
                    
#                 self.log(f"[Account {account_number}] 🚀 Launching browser...")
                
#                 # Configure browser launch args to avoid detection and redirects
#                 browser_args = [
#                     '--disable-blink-features=AutomationControlled',
#                     '--disable-dev-shm-usage',
#                     '--no-sandbox',
#                     '--disable-setuid-sandbox',
#                     '--disable-web-security',
#                     '--disable-features=VizDisplayCompositor',
#                     '--disable-gpu',
#                     '--disable-background-timer-throttling',
#                     '--disable-backgrounding-occluded-windows',
#                     '--disable-renderer-backgrounding',
#                     '--disable-field-trial-config',
#                     '--disable-hang-monitor',
#                     '--disable-ipc-flooding-protection',
#                     '--no-first-run',
#                     '--no-default-browser-check',
#                     '--disable-default-apps',
#                     '--disable-sync',
#                     '--disable-translate',
#                     '--hide-scrollbars',
#                     '--mute-audio',
#                     '--no-zygote',
#                     '--disable-logging',
#                     '--disable-permissions-api',
#                     '--ignore-certificate-errors',
#                     '--allow-running-insecure-content'
#                 ]
                
#                 # Full size for headless mode
#                 viewport_width = 1920
#                 viewport_height = 1080
                
#                 browser = None
#                 try:
#                     # Try Chromium first (more reliable)
#                     self.log(f"[Account {account_number}] 🔧 Attempting to launch Chromium browser...")
#                     browser = await p.chromium.launch(
#                         headless=False,  # Show browser for debugging
#                         args=browser_args,
#                         proxy=proxy_config,
#                         slow_mo=100  # Small delay for visibility
#                     )
#                     self.log(f"[Account {account_number}] ✅ Chromium browser launched successfully")
#                 except Exception as chrome_error:
#                     self.log(f"[Account {account_number}] ⚠️ Chromium launch failed: {chrome_error}")
                    
#                     # Fallback to basic launch without extra features
#                     try:
#                         self.log(f"[Account {account_number}] 🔄 Attempting basic browser launch...")
#                         browser = await p.chromium.launch(
#                             headless=False,
#                             proxy=proxy_config
#                         )
#                         self.log(f"[Account {account_number}] ✅ Basic browser launched successfully")
#                     except Exception as basic_error:
#                         self.log(f"[Account {account_number}] ❌ All browser launch attempts failed: {basic_error}", "ERROR")
#                         return False
                
#                 if not browser:
#                     self.log(f"[Account {account_number}] ❌ Failed to launch browser", "ERROR")
#                     return False
                
#                 try:
#                     context = await browser.new_context(
#                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#                         viewport={'width': viewport_width, 'height': viewport_height},
#                         extra_http_headers={
#                             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#                             'Accept-Language': 'en-US,en;q=0.9',
#                             'Accept-Encoding': 'gzip, deflate, br',
#                             'Sec-Fetch-Dest': 'document',
#                             'Sec-Fetch-Mode': 'navigate',
#                             'Sec-Fetch-Site': 'none',
#                             'Sec-Fetch-User': '?1',
#                             'Upgrade-Insecure-Requests': '1'
#                         }
#                     )
#                     self.log(f"[Account {account_number}] ✅ Browser context created successfully")
#                 except Exception as e:
#                     self.log(f"[Account {account_number}] ❌ Failed to create browser context: {e}", "ERROR")
#                     await browser.close()
#                     return False
                
#                 try:
#                     # Use the default page that's automatically created with the context
#                     pages = context.pages
#                     if pages:
#                         page = pages[0]  # Use the first (default) page
#                         self.log(f"[Account {account_number}] ✅ Using default browser page")
#                     else:
#                         # Fallback: create a new page if no default page exists
#                         page = await context.new_page()
#                         self.log(f"[Account {account_number}] ✅ Created new browser page")
#                 except Exception as e:
#                     self.log(f"[Account {account_number}] ❌ Failed to get browser page: {e}", "ERROR")
#                     await browser.close()
#                     return False
                
#                 # Set page title for headless mode
#                 await page.evaluate(f'''
#                     document.title = "Account {account_number}: {username}";
#                 ''')

#                 try:
#                     if self.should_stop():
#                         self.log(f"[Account {account_number}] ⚠️ Stop flag detected, terminating script", "WARNING")
#                         return
                        
#                     # Enhanced login with cookie management and 2FA support
#                     self.log(f"[Account {account_number}] 🚀 Starting enhanced login process...")
#                     login_success, auth_info = await self.login_instagram_with_cookies_and_2fa(page, context, username, password, account_number)
                    
#                     if not login_success:
#                         self.log(f"[Account {account_number}] ❌ Login failed - terminating script for this account", "ERROR")
#                         await self.update_visual_status(page, "❌ Login failed - terminating", 4)
#                         return False

#                     if self.should_stop():
#                         self.log(f"[Account {account_number}] ⚠️ Stop flag detected after login, terminating script", "WARNING")
#                         return

#                     self.log(f"[Account {account_number}] ✅ Login successful! Current URL: {page.url}")
                    
#                     # Navigate to Instagram home page after successful authentication
#                     self.log(f"[Account {account_number}] 🏠 Navigating to Instagram home page...")
#                     await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
#                     await self.human_delay(3000, 5000)
                    
#                     self.log(f"[Account {account_number}] 🔄 Proceeding to handle popups...")

#                     # Handle popups (including "Save info" button) only if login was via credentials
#                     auth_method = auth_info.get('authentication_method', 'unknown')
#                     if auth_method == 'credentials':
#                         self.log(f"[Account {account_number}] 🔑 Login was via credentials, checking for 'Save info' dialog...")
#                         await self.handle_popups(page, account_number)
#                     elif auth_method == 'cookies':
#                         self.log(f"[Account {account_number}] 🍪 Login was via cookies, skipping 'Save info' dialog check")
#                     else:
#                         self.log(f"[Account {account_number}] ❓ Unknown authentication method, skipping popup handling")

#                     if self.should_stop():
#                         self.log(f"[Account {account_number}] ⚠️ Stop flag detected after popup handling, terminating script", "WARNING")
#                         return

#                     self.log(f"[Account {account_number}] ✅ Popup handling completed! Current URL: {page.url}")

#                     # Ensure we're on Instagram home page before looking for Create button
#                     current_url = page.url
#                     if "instagram.com" not in current_url or "/accounts/" in current_url:
#                         self.log(f"[Account {account_number}] 🔄 Not on home page, navigating to Instagram home...")
#                         await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
#                         await self.human_delay(3000, 5000)

#                     # Navigate to create post
#                     self.log(f"[Account {account_number}] 📝 Looking for 'Create' button...")
#                     self.log(f"[Account {account_number}] 📊 Page title: {await page.title()}")
#                     self.log(f"[Account {account_number}] 📊 Current URL: {page.url}")
#                     await self.update_visual_status(page, "Looking for Create button...", 5)
                    
#                     # Wait for page to be fully loaded and interactive
#                     try:
#                         await page.wait_for_load_state('networkidle', timeout=15000)
#                         self.log(f"[Account {account_number}] ✅ Page fully loaded (network idle)")
#                     except Exception as load_error:
#                         self.log(f"[Account {account_number}] ⚠️ Page load state timeout: {load_error}, continuing anyway")
                    
#                     await self.human_delay(3000, 5000)  # Increased wait time for page to load fully
                    
#                     # Quick diagnostic check
#                     try:
#                         page_content = await page.content()
#                         if "Create" in page_content:
#                             self.log(f"[Account {account_number}] ✅ 'Create' text found in page content")
#                         else:
#                             self.log(f"[Account {account_number}] ⚠️ 'Create' text NOT found in page content")
                            
#                         # Count total elements on page
#                         all_elements = await page.query_selector_all('*')
#                         self.log(f"[Account {account_number}] 📊 Total elements on page: {len(all_elements)}")
                        
#                     except Exception as diag_error:
#                         self.log(f"[Account {account_number}] ⚠️ Diagnostic check failed: {diag_error}")
                    
#                     create_selectors = [
#                         # Most reliable - simple text-based selectors that should work
#                         'text="Create"',
#                         ':text-is("Create")',
#                         'a:text("Create")',
#                         'div:text("Create")',
#                         'span:text("Create")',
                        
#                         # Specific for Instagram sidebar navigation
#                         'nav a:has-text("Create")',
#                         'nav div:has-text("Create")',
#                         'aside a:has-text("Create")',
#                         '[role="navigation"] a:has-text("Create")',
                        
#                         # Container-based selectors
#                         'span:has-text("Create")',
#                         'div:has-text("Create")',
#                         'a:has-text("Create")',
                        
#                         # Role-based selectors
#                         'div[role="button"]:has-text("Create")',
#                         'a[role="menuitem"]:has-text("Create")',
#                         'button:has-text("Create")',
                        
#                         # SVG and aria-label selectors
#                         'svg[aria-label="New post"]',
#                         'div:has(svg[aria-label="New post"])',
#                         'a[aria-label="New post"]',
#                         '*[aria-label="New post"]',
                        
#                         # XPath selectors (very reliable)
#                         '//a[contains(text(), "Create")]',
#                         '//div[contains(text(), "Create")]',
#                         '//span[contains(text(), "Create")]',
#                         '//*[text()="Create"]',
#                         '//*[contains(@aria-label, "New post")]',
                        
#                         # Generic selectors
#                         'a[href*="create"]',
                        
#                         # Legacy complex selector (last resort)
#                         'div.x9f619.x3nfvp2.xr9ek0c.xjpr12u.xo237n4.x6pnmvc.x7nr27j.x12dmmrz.xz9dl7a.xpdmqnj.xsag5q8.x1g0dm76.x80pfx3.x159b3zp.x1dn74xm.xif99yt.x172qv1o.x4afuhf.x1lhsz42.x10v4vz6.xdoji71.x1dejxi8.x9k3k5o.x8st7rj.x11hdxyr.x1eunh74.x1wj20lx.x1obq294.x5a5i1n.xde0f50.x15x8krk'
#                     ]
                    
#                     clicked_create = False
#                     for i, selector in enumerate(create_selectors):
#                         if self.should_stop():
#                             self.log(f"[Account {account_number}] ⚠️ Stop flag detected during create button search, terminating script", "WARNING")
#                             return
#                         try:
#                             self.log(f"[Account {account_number}] 🎯 Trying create button selector {i+1}/{len(create_selectors)}: {selector[:50]}...")
#                             await page.wait_for_selector(selector, state='visible', timeout=5000)
#                             await page.click(selector)
#                             self.log(f"[Account {account_number}] ✅ Successfully clicked create button with selector {i+1}")
#                             clicked_create = True
#                             break
#                         except TimeoutError:
#                             self.log(f"[Account {account_number}] ⚠️ Create button selector {i+1} timed out (not found)")
#                             continue
#                         except Exception as e:
#                             self.log(f"[Account {account_number}] ❌ Create button selector {i+1} failed with error: {e}", "ERROR")
#                             continue
                    
#                     if not clicked_create:
#                         self.log(f"[Account {account_number}] ❌ Could not find create button after trying all {len(create_selectors)} selectors", "ERROR")
#                         self.log(f"[Account {account_number}] 📊 Current page URL: {page.url}")
#                         self.log(f"[Account {account_number}] 📊 Page title: {await page.title()}")
                        
#                         # Try to take a screenshot for debugging (if not headless)
#                         try:
#                             screenshot_path = f"debug_screenshot_{account_number}.png"
#                             await page.screenshot(path=screenshot_path)
#                             self.log(f"[Account {account_number}] 📸 Debug screenshot saved: {screenshot_path}")
#                         except:
#                             pass
                            
#                         # Check if we can find any elements that might be the create button
#                         try:
#                             all_buttons = await page.query_selector_all('button, div[role="button"], a[role="button"]')
#                             self.log(f"[Account {account_number}] 📊 Found {len(all_buttons)} button-like elements on page")
                            
#                             # Check for any element with "Create" text
#                             create_elements = await page.query_selector_all('*:has-text("Create")')
#                             self.log(f"[Account {account_number}] 📊 Found {len(create_elements)} elements containing 'Create' text")
                            
#                             # Check for SVG with "New post" aria-label
#                             svg_elements = await page.query_selector_all('svg[aria-label*="post"], svg[aria-label*="Post"]')
#                             self.log(f"[Account {account_number}] 📊 Found {len(svg_elements)} SVG elements with post-related aria-labels")
                            
#                         except Exception as debug_error:
#                             self.log(f"[Account {account_number}] ⚠️ Debug search failed: {debug_error}")
                        
#                         await self.update_visual_status(page, "❌ Create button not found!", 5)
#                         return False

#                     self.log(f"[Account {account_number}] ✅ Create button clicked successfully!")
#                     await self.update_visual_status(page, "✅ Opening create menu...", 6)
#                     await self.human_delay(2000, 3000)

#                     if self.should_stop():
#                         self.log(f"[Account {account_number}] ⚠️ Stop flag detected before file upload, terminating script", "WARNING")
#                         return

#                     # Handle file upload
#                     self.log(f"[Account {account_number}] 📁 Starting file upload process...")
#                     success = await self.handle_file_upload(page, account_number)
#                     if not success:
#                         self.log(f"[Account {account_number}] ❌ File upload failed - terminating script", "ERROR")
#                         return False

#                     if self.should_stop():
#                         self.log(f"[Account {account_number}] ⚠️ Stop flag detected after file upload, terminating script", "WARNING")
#                         return

#                     self.log(f"[Account {account_number}] ✅ File upload completed successfully!")

#                     # Process the post
#                     self.log(f"[Account {account_number}] 🔄 Starting post processing...")
#                     success = await self.process_post(page, account_number, caption)
#                     if not success:
#                         self.log(f"[Account {account_number}] ❌ Post processing failed - terminating script", "ERROR")
#                         return False

#                     self.log(f"[Account {account_number}] 🎉 Post completed successfully!", "SUCCESS")
#                     await self.update_visual_status(page, "✅ COMPLETED!", 5)
#                     return True

#                 except Exception as e:
#                     self.log(f"[Account {account_number}] ❌ Critical error during automation: {str(e)}", "ERROR")
#                     self.log(f"[Account {account_number}] 📊 Error occurred at URL: {page.url if 'page' in locals() else 'N/A'}")
#                     self.log(f"[Account {account_number}] 📊 Error type: {type(e).__name__}")
#                     import traceback
#                     self.log(f"[Account {account_number}] 📊 Full traceback: {traceback.format_exc()}", "ERROR")
#                     await self.update_visual_status(page, f"❌ Error: {str(e)[:30]}...", 2)
#                     return False
#                 finally:
#                     self.log(f"[Account {account_number}] 🔄 Closing browser...")
#                     try:
#                         await browser.close()
#                         self.log(f"[Account {account_number}] ✅ Browser closed successfully")
#                     except Exception as e:
#                         self.log(f"[Account {account_number}] ⚠️ Error closing browser: {e}", "WARNING")
                    
#         except Exception as e:
#             self.log(f"[Account {account_number}] Critical error: {e}", "ERROR")
#             return False

#     async def handle_popups(self, page, account_number):
#         """Handle pop-ups with enhanced logging - Updated for new Instagram UI"""
#         if self.should_stop():
#             self.log(f"[Account {account_number}] ⚠️ Stop flag detected during popup handling", "WARNING")
#             return
            
#         self.log(f"[Account {account_number}] 🔄 Starting popup handling...")
        
#         # First priority: Handle "Save info" button (new Instagram UI)
#         save_info_selectors = [
#             'button._aswp._aswr._aswu._asw_._asx2:has-text("Save info")',
#             'button:has-text("Save info")',
#             'button:has-text("Save Info")',
#             'div[role="button"]:has-text("Save info")',
#             'div[role="button"]:has-text("Save Info")',
#             '//button[contains(text(), "Save info")]',
#             '//button[contains(text(), "Save Info")]'
#         ]
        
#         self.log(f"[Account {account_number}] 🔍 Looking for 'Save info' button...")
#         save_info_clicked = False
        
#         for i, selector in enumerate(save_info_selectors, 1):
#             if self.should_stop():
#                 return
#             try:
#                 self.log(f"[Account {account_number}] 🎯 Trying save info selector {i}/{len(save_info_selectors)}: {selector[:50]}...")
#                 save_button = await page.wait_for_selector(selector, state='visible', timeout=5000)
#                 if save_button:
#                     await save_button.click()
#                     self.log(f"[Account {account_number}] ✅ Clicked 'Save info' button with selector {i}")
#                     await self.human_delay(2000, 3000)
#                     save_info_clicked = True
#                     break
#             except Exception as e:
#                 self.log(f"[Account {account_number}] ⚠️ Save info selector {i} failed: {str(e)[:100]}")
#                 continue
        
#         if not save_info_clicked:
#             self.log(f"[Account {account_number}] ℹ️ No 'Save info' button found, continuing anyway...")
        
#         self.log(f"[Account {account_number}] ✅ Popup handling completed!")
#         self.log(f"[Account {account_number}] 📊 Current URL after popup handling: {page.url}")

#     async def handle_file_upload(self, page, account_number):
#         """Handle the media file upload process with enhanced logging."""
#         if self.should_stop():
#             self.log(f"[Account {account_number}] ⚠️ Stop flag detected during file upload", "WARNING")
#             return False
            
#         self.log(f"[Account {account_number}] 📁 Starting file upload process...")
#         self.log(f"[Account {account_number}] 📊 File to upload: {os.path.basename(self.media_file)}")
#         self.log(f"[Account {account_number}] 📊 File path: {self.media_file}")
#         self.log(f"[Account {account_number}] 📊 File type: {'Video' if self.is_video else 'Image'}")
#         self.log(f"[Account {account_number}] 📊 Current URL: {page.url}")
#         await self.update_visual_status(page, "Uploading file...", 7)
#         await self.human_delay(2000, 4000)
        
#         upload_selectors = [
#             'button._aswp._aswr._aswu._asw_._asx2[type="button"]:has-text("Select from computer")',
#             'button:has-text("Select from computer")',
#             'div[role="button"]:has-text("Select from computer")',
#             'input[type="file"]',
#             'button:has-text("Select from Computer")',
#             '//button[contains(., "Select from computer")]',
#             '//input[@type="file"]'
#         ]
        
#         upload_success = False
        
#         for i, selector in enumerate(upload_selectors):
#             if self.should_stop():
#                 self.log(f"[Account {account_number}] ⚠️ Stop flag detected during upload selector {i+1}", "WARNING")
#                 return False
#             try:
#                 self.log(f"[Account {account_number}] 🎯 Trying upload selector {i+1}/{len(upload_selectors)}: {selector[:50]}...")
                
#                 if 'input[type="file"]' in selector or '//input[@type="file"]' in selector:
#                     self.log(f"[Account {account_number}] 📝 Direct file input approach...")
#                     file_input = await page.wait_for_selector(selector, state='attached', timeout=10000)
#                     await file_input.set_input_files(self.media_file)
#                     self.log(f"[Account {account_number}] ✅ File uploaded directly: {os.path.basename(self.media_file)}")
#                     upload_success = True
#                     break
#                 else:
#                     self.log(f"[Account {account_number}] 📝 File chooser approach...")
#                     await page.wait_for_selector(selector, state='visible', timeout=10000)
#                     self.log(f"[Account {account_number}] ✅ Upload button found, waiting for file chooser...")
                    
#                     async with page.expect_file_chooser(timeout=15000) as fc_info:
#                         await page.click(selector)
#                         self.log(f"[Account {account_number}] 🖱️ Clicked upload button")
#                         file_chooser = await fc_info.value
#                         await file_chooser.set_files(self.media_file)
#                         self.log(f"[Account {account_number}] ✅ File selected in chooser: {os.path.basename(self.media_file)}")
#                         await self.update_visual_status(page, "✅ File uploaded!", 8)
#                         upload_success = True
#                         break
                        
#             except TimeoutError:
#                 self.log(f"[Account {account_number}] ⚠️ Upload selector {i+1} timed out")
#                 continue
#             except Exception as e:
#                 self.log(f"[Account {account_number}] ❌ Upload selector {i+1} failed with error: {e}", "ERROR")
#                 continue
        
#         if not upload_success:
#             self.log(f"[Account {account_number}] ❌ All upload methods failed after trying {len(upload_selectors)} selectors", "ERROR")
#             self.log(f"[Account {account_number}] 📊 Current URL: {page.url}")
#             self.log(f"[Account {account_number}] 📊 Page title: {await page.title()}")
#             await self.update_visual_status(page, "❌ Upload failed!", 8)
#             return False
            
#         self.log(f"[Account {account_number}] ✅ File upload completed successfully!")
#         self.log(f"[Account {account_number}] 📊 Current URL after upload: {page.url}")
#         return True

#     async def process_post(self, page, account_number, caption=""):
#         """Navigate through post creation steps."""
#         if self.should_stop():
#             return False
            
#         self.log(f"[Account {account_number}] 🔄 Starting post processing...")
#         await self.update_visual_status(page, "Processing post...", 9)
        
#         next_selectors = [
#             # Updated Next button selectors based on your HTML structure
#             'div.x1i10hfl.xjqpnuy.xa49m3k.xqeqjp1.x2hbi6w.x13fuv20.xu3j5b3.x1q0q8m5.x26u7qi.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xdl72j9.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x2lwn1j.xeuugli.x16tdsg8.xggy1nq.x1ja2u2z.x1t137rt.x6s0dn4.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x3nfvp2.xdl72j9.x2lah0s.xe8uvvx.x1iyjqo2.xs83m0k.x1q0g3np[role="button"]',
#             'div[role="button"]:has-text("Next")',
#             'button:has-text("Next")',
#             'div.x1n2onr6:has-text("Next")',
#             '//div[@role="button" and contains(text(), "Next")]',
#             '//button[contains(., "Next")]',
#             'text="Next"',
#             ':text("Next")'
#         ]
        
#         # First 'Next' button
#         self.log(f"[Account {account_number}] 🔍 Looking for first 'Next' button...")
#         await self.human_delay(3000, 5000)
#         clicked_first_next = False
#         for i, selector in enumerate(next_selectors):
#             if self.should_stop():
#                 return False
#             try:
#                 self.log(f"[Account {account_number}] Trying first Next button selector {i+1}: {selector}")
#                 await page.wait_for_selector(selector, state='visible', timeout=15000)
#                 await page.click(selector)
#                 self.log(f"[Account {account_number}] ✅ Clicked first 'Next' button with selector {i+1}")
#                 clicked_first_next = True
#                 break
#             except TimeoutError:
#                 self.log(f"[Account {account_number}] First Next button selector {i+1} not found")
#                 continue
        
#         if not clicked_first_next:
#             self.log(f"[Account {account_number}] ❌ Could not find or click first 'Next' button", "ERROR")
#             await self.update_visual_status(page, "❌ First Next button not found!", 9)
#             return False

#         # Second 'Next' button
#         self.log(f"[Account {account_number}] 🔍 Looking for second 'Next' button...")
#         await self.update_visual_status(page, "Moving to caption step...", 10)
#         await self.human_delay(2000, 4000)
        
#         clicked_second_next = False
#         for i, selector in enumerate(next_selectors):
#             if self.should_stop():
#                 return False
#             try:
#                 self.log(f"[Account {account_number}] Trying second Next button selector {i+1}: {selector}")
#                 await page.wait_for_selector(selector, state='visible', timeout=15000)
#                 await page.click(selector)
#                 self.log(f"[Account {account_number}] ✅ Clicked second 'Next' button with selector {i+1}")
#                 clicked_second_next = True
#                 break
#             except TimeoutError:
#                 self.log(f"[Account {account_number}] Second Next button selector {i+1} not found")
#                 continue

#         if not clicked_second_next:
#             self.log(f"[Account {account_number}] ⚠️ Could not find second 'Next' button, continuing anyway...")

#         await self.human_delay(2000, 3000)

#         # Add caption
#         await self.add_caption(page, account_number, caption)

#         # Click 'Share' button
#         self.log(f"[Account {account_number}] 🚀 Looking for 'Share' button...")
#         await self.update_visual_status(page, "Preparing to share...", 11)
#         await self.human_delay(1000, 2000)
        
#         share_selectors = [
#             # Updated Share button selectors based on your HTML structure
#             'div.x1i10hfl.xjqpnuy.xa49m3k.xqeqjp1.x2hbi6w.x13fuv20.xu3j5b3.x1q0q8m5.x26u7qi.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xdl72j9.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x2lwn1j.xeuugli.x16tdsg8.xggy1nq.x1ja2u2z.x1t137rt.x6s0dn4.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x3nfvp2.xdl72j9.x2lah0s.xe8uvvx.x1iyjqo2.xs83m0k.x1q0g3np[role="button"]',
#             'div[role="button"]:has-text("Share")',
#             'button:has-text("Share")',
#             'div.x1n2onr6:has-text("Share")',
#             '[role="button"]:has-text("Share")',
#             '//div[@role="button" and contains(text(), "Share")]',
#             '//button[contains(text(), "Share")]',
#             'text="Share"',
#             ':text("Share")',
#             # Legacy selectors for fallback
#             'div.x1i10hfl[role="button"]:has-text("Share")',
#             'div[class*="x1i10hfl"][role="button"]:has-text("Share")',
#             'div[class*="xjqpnuy"][role="button"]:has-text("Share")'
#         ]
        
#         clicked_share = False
#         for i, selector in enumerate(share_selectors):
#             if self.should_stop():
#                 return False
#             try:
#                 self.log(f"[Account {account_number}] Trying Share button selector {i+1}: {selector}")
#                 element = await page.wait_for_selector(selector, state='visible', timeout=5000)
#                 if element:
#                     element_text = await element.text_content()
#                     if "Share" in element_text:
#                         await element.click()
#                         self.log(f"[Account {account_number}] ✅ Clicked 'Share' button - Upload in progress...")
#                         await self.update_visual_status(page, "🚀 Sharing post...", 12)
#                         clicked_share = True
#                         break
#             except TimeoutError:
#                 self.log(f"[Account {account_number}] Share button selector {i+1} not found")
#                 continue
#             except Exception as e:
#                 self.log(f"[Account {account_number}] Share button selector {i+1} failed: {e}")
#                 continue

#         if not clicked_share:
#             self.log(f"[Account {account_number}] ❌ Could not find or click 'Share' button", "ERROR")
#             await self.update_visual_status(page, "❌ Share button not found!", 12)
#             return False

#         # Wait for post completion
#         self.log(f"[Account {account_number}] ⏳ Waiting for post completion...")
#         await self.update_visual_status(page, "⏳ Waiting for completion...", 13)
#         await self.human_delay(5000, 8000)
#         try:
#             await page.wait_for_selector('text="Your post has been shared."', timeout=30000)
#             self.log(f"[Account {account_number}] ✅ Post shared successfully - confirmation message found!")
#             await self.update_visual_status(page, "✅ Post shared successfully!", 14)
#         except TimeoutError:
#             try:
#                 await page.wait_for_url("https://www.instagram.com/", timeout=15000)
#                 self.log(f"[Account {account_number}] ✅ Post confirmed - redirected to home page")
#                 await self.update_visual_status(page, "✅ Post confirmed!", 14)
#             except TimeoutError:
#                 self.log(f"[Account {account_number}] ⚠️ Post status unclear, but 'Share' was clicked - likely successful")
#                 await self.update_visual_status(page, "⚠️ Post likely successful", 14)
        
#         return True

#     async def add_caption(self, page, account_number, caption=""):
#         """Add caption to the post."""
#         if self.should_stop():
#             return
            
#         # Use provided caption or generate default one
#         if not caption:
#             media_type = "video" if self.is_video else "image"
#             caption = f"Automated {media_type} post! 🤖✨ #automation #instagram #bot"
#             self.log(f"[Account {account_number}] 📝 No caption provided, using default caption")
#         else:
#             self.log(f"[Account {account_number}] 📝 Adding custom caption: {caption[:100]}{'...' if len(caption) > 100 else ''}")
            
#         await self.update_visual_status(page, "Adding caption...", 10)
        
#         try:
#             caption_selectors = [
#                 # Updated caption field selector based on your HTML structure  
#                 'div.xw2csxc.x1odjw0f.x1n2onr6.x1hnll1o.xpqswwc.xl565be.x5dp1im.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x2lwn1j.xeuugli.x16tdsg8.x1iyjqo2.xs83m0k.xjbqb8w.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xdl72j9.xe8uvvx.x1d52u69.x1emribx.x1n2onr6.x16tdsg8.x1hnll1o.x1ja2u2z.x1t137rt.x1q0g3np.x1lku1pv.x1a2a7pz.x6s0dn4.x14yjl9h.xudhj91.x18nykt9.xww2gxu.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xdl72j9.xe8uvvx.x1iyjqo2.xs83m0k.x150jy0e.x159b3zp.x1n2onr6.x16tdsg8.x1hnll1o.xpqswwc.xl565be.x5dp1im.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x2lwn1j.xeuugli.x16tdsg8.xggy1nq.x1ja2u2z.x1t137rt.x6s0dn4.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x3nfvp2[aria-label="Write a caption..."][contenteditable="true"]',
#                 # Fallback selectors
#                 'div[aria-label="Write a caption..."][contenteditable="true"]',
#                 'textarea[aria-label="Write a caption..."]',
#                 'div[contenteditable="true"][aria-label*="caption"]',
#                 'textarea[placeholder*="caption"]',
#                 'div[role="textbox"][aria-label="Write a caption..."]',
#                 'div[data-testid="caption"]',
#                 'textarea[placeholder="Write a caption..."]',
#                 'div[aria-label*="caption"]',
#                 'textarea[aria-label*="caption"]',
#                 'div[contenteditable="true"]',
#                 '//textarea[@aria-label="Write a caption..."]',
#                 '//div[@contenteditable="true" and contains(@aria-label, "caption")]'
#             ]
            
#             caption_added = False
#             for i, selector in enumerate(caption_selectors):
#                 if self.should_stop():
#                     return
#                 try:
#                     self.log(f"[Account {account_number}] Trying caption field selector {i+1}: {selector}")
#                     caption_field = await page.wait_for_selector(selector, state='visible', timeout=10000)
#                     if caption_field:
#                         await self.human_type(page, selector, caption, delay_range=(30, 100))
#                         self.log(f"[Account {account_number}] ✅ Caption added successfully with selector {i+1}")
#                         caption_added = True
#                         break
#                 except TimeoutError:
#                     self.log(f"[Account {account_number}] Caption field selector {i+1} not found")
#                     continue
#                 except Exception as e:
#                     self.log(f"[Account {account_number}] Caption field selector {i+1} error: {e}")
#                     continue
            
#             if not caption_added:
#                 self.log(f"[Account {account_number}] ⚠️ Could not find caption field, posting without caption")
            
#         except Exception as e:
#             self.log(f"[Account {account_number}] ❌ Caption addition failed: {e}", "ERROR")

#     async def run_automation(self, accounts_file, media_file, concurrent_accounts=5, caption="", auto_generate_caption=True):
#         """Run Instagram posting for multiple accounts concurrently."""
#         self.log("Starting Multi-Account Instagram Automation.")
#         self.log("=" * 50)
        
#         # Set media file
#         self.set_media_file(media_file)
        
#         # Load credentials
#         accounts = self.load_accounts_from_file(accounts_file)
#         if not accounts:
#             self.log("No valid accounts found. Please check your accounts file.", "ERROR")
#             return False
        
#         # Limit concurrent accounts
#         accounts_to_process = accounts[:concurrent_accounts]
#         self.log(f"Processing {len(accounts_to_process)} account(s) concurrently.")
#         self.log("=" * 50)
        
#         # Create semaphore to limit concurrent browsers
#         semaphore = asyncio.Semaphore(min(concurrent_accounts, 5))  # Max 5 concurrent browsers
        
#         async def process_account_with_semaphore(username, password, account_num):
#             async with semaphore:
#                 if self.should_stop():
#                     self.log(f"[Account {account_num}] ⚠️ Stop flag detected before processing - skipping account", "WARNING")
#                     return False
                    
#                 self.log(f"[Account {account_num}] 🚀 Starting processing for {username}...")
#                 try:
#                     result = await self.instagram_post_script(username, password, account_num, caption)
#                     if result is None:
#                         self.log(f"[Account {account_num}] ⚠️ Script returned None - likely stopped early", "WARNING")
#                         return False
#                     elif result:
#                         self.log(f"[Account {account_num}] ✅ Processing completed successfully!", "SUCCESS")
#                         return True
#                     else:
#                         self.log(f"[Account {account_num}] ❌ Processing failed", "ERROR")
#                         return False
#                 except Exception as e:
#                     self.log(f"[Account {account_num}] ❌ Exception during processing: {e}", "ERROR")
#                     return False
        
#         # Create tasks for each account
#         tasks = []
#         for i, (username, password) in enumerate(accounts_to_process, 1):
#             if self.should_stop():
#                 break
#             self.log(f"Creating task for Account {i}: {username}.")
#             task = asyncio.create_task(process_account_with_semaphore(username, password, i))
#             tasks.append(task)
        
#         if not tasks:
#             self.log("No tasks created", "ERROR")
#             return False
        
#         self.log(f"Created {len(tasks)} tasks. Starting execution...")
        
#         # Run all tasks concurrently
#         try:
#             results = await asyncio.gather(*tasks, return_exceptions=True)
            
#             # Summary
#             self.log("\nResults Summary:")
#             successful_count = 0
#             for i, result in enumerate(results, 1):
#                 if isinstance(result, Exception):
#                     self.log(f"Account {i}: Failed with error: {result}", "ERROR")
#                 elif result:
#                     self.log(f"Account {i}: Completed successfully.", "SUCCESS")
#                     successful_count += 1
#                 else:
#                     self.log(f"Account {i}: Failed", "ERROR")
            
#             self.log("=" * 50)
#             if successful_count == len(results):
#                 self.log(f"🎉 All accounts completed successfully! {successful_count}/{len(results)} accounts processed.", "SUCCESS")
#             elif successful_count > 0:
#                 self.log(f"⚠️ Partial success: {successful_count}/{len(results)} accounts completed successfully.", "WARNING") 
#             else:
#                 self.log(f"❌ No accounts completed successfully. {len(results)} accounts failed.", "ERROR")
            
#             self.log(f"Automation finished! {successful_count}/{len(results)} accounts processed successfully.")
#             return successful_count > 0
                    
#         except Exception as e:
#             self.log(f"Error in concurrent execution: {e}", "ERROR")
#             return False

# # Async function to run the automation (to be called from Flask)
# async def run_daily_post_automation(script_id, accounts_file, media_file, concurrent_accounts=5, 
#                                    caption="", auto_generate_caption=True,
#                                    log_callback=None, stop_callback=None):
#     """Main function to run the automation"""
#     automation = InstagramDailyPostAutomation(script_id, log_callback, stop_callback)
    
#     try:
#         success = await automation.run_automation(
#             accounts_file=accounts_file,
#             media_file=media_file,
#             concurrent_accounts=concurrent_accounts,
#             caption=caption,
#             auto_generate_caption=auto_generate_caption
#         )
#         return success
#     except Exception as e:
#         if log_callback:
#             log_callback(f"Automation failed: {e}", "ERROR")
#         return False



import asyncio
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError
import os
import glob
import time
import random
from pathlib import Path
import logging
import pyotp
import re
import datetime
import traceback
from instagram_accounts import get_account_details
from proxy_manager import proxy_manager
from enhanced_instagram_auth import enhanced_auth
from instagram_cookie_manager import cookie_manager

class InstagramDailyPostAutomation:
    def __init__(self, script_id, log_callback=None, stop_flag_callback=None):
        self.script_id = script_id
        self.log_callback = log_callback or self.default_log
        self.stop_flag_callback = stop_flag_callback or (lambda: False)
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        self.supported_video_formats = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']
        self.media_file = None
        self.is_video = False
        
    def default_log(self, message, level="INFO"):
        """Default logging function with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        print(formatted_message, flush=True)
        
    def log(self, message, level="INFO", account_id=None):
        """Logs a message with an optional account ID."""
        prefix = f"[{self.script_id}]"
        if account_id:
            prefix = f"[{account_id}]"
        self.log_callback(f"{prefix} {message}", level)

    async def _perform_robust_click(self, page, selector, timeout=30000, account_id=None):
        """
        Performs a robust click action, waiting for the element to be clickable
        and handling potential interceptions.

        Args:
            page (Page): The Playwright page object.
            selector (str): The CSS selector of the element to click.
            timeout (int): The maximum time to wait for the click to succeed.
            account_id (str): The ID of the current account for logging purposes.
        """
        try:
            self.log(f"Attempting a robust click on element with selector: '{selector}'", "INFO", account_id)
            # Wait for the selector to be in a 'stable' state, meaning it's visible and enabled.
            # This is more robust than a simple click as it waits for any overlays to disappear.
            await page.wait_for_selector(selector, state='visible', timeout=timeout)
            
            # The .click() method with a `force=True` option can sometimes bypass interceptions,
            # but it's better to wait for the element to be genuinely clickable.
            # We'll stick with a standard click after a robust wait.
            await page.click(selector, timeout=timeout)
            self.log(f"Successfully clicked element with selector: '{selector}'", "SUCCESS", account_id)
        except TimeoutError as e:
            self.log(f"❌ Robust click failed on element '{selector}': Timeout {timeout}ms exceeded. The element was likely intercepted.", "ERROR", account_id)
            raise e
        except Exception as e:
            self.log(f"❌ An unexpected error occurred during the robust click on '{selector}': {e}", "ERROR", account_id)
            raise e

    async def generate_totp_code(self, username, totp_secret):
        """Generate TOTP code for 2FA authentication"""
        try:
            if not totp_secret:
                self.log(f"[{username}] ℹ️ No TOTP secret provided", "INFO")
                return None
                
            # Clean the secret (remove spaces and convert to uppercase)
            clean_secret = totp_secret.strip().replace(' ', '').upper()
            
            # Validate secret length (16 or 32 characters for base32)
            if len(clean_secret) not in [16, 32]:
                self.log(f"[{username}] ❌ Invalid TOTP secret length: {len(clean_secret)} (must be 16 or 32 characters)", "ERROR")
                return None
                
            # Validate base32 format
            if not re.match(r'^[A-Z2-7=]+$', clean_secret):
                self.log(f"[{username}] ❌ Invalid TOTP secret format (must be base32)", "ERROR")
                return None
            
            # Generate TOTP code
            totp = pyotp.TOTP(clean_secret)
            code = totp.now()
            
            self.log(f"[{username}] ✅ Generated TOTP code: {code} (secret length: {len(clean_secret)})", "INFO")
            return code
            
        except Exception as e:
            self.log(f"[{username}] ❌ Error generating TOTP code: {e}", "ERROR")
            return None

    async def handle_2fa_verification(self, page, username, totp_secret):
        """Handle Instagram 2FA verification using TOTP."""
        try:
            self.log(f"[{username}] 🔐 2FA verification required...")
            
            # Generate TOTP code
            totp_code = await self.generate_totp_code(username, totp_secret)
            if not totp_code:
                self.log(f"[{username}] ❌ Could not generate TOTP code.")
                return False
            
            await self.human_delay(1000, 2000)

            # Look for 2FA input field
            totp_selectors = [
                'input[name="verificationCode"]',
                'input[name="security_code"]',
                'input[aria-label*="security code"]',
                'input[placeholder*="security code"]',
                'input[placeholder*="verification code"]',
                '[data-testid="2fa-input"]',
                'input[type="text"][maxlength="6"]',
                'input[autocomplete="one-time-code"]',
                'input[aria-label="Security Code"]',
                'input[aria-describedby="verificationCodeDescription"]',
                'input[type="tel"][maxlength="8"]',
                'input[autocomplete="off"][maxlength="8"]',
                'input[class*="aa4b"][type="tel"]'
            ]
            
            totp_input = None
            for selector in totp_selectors:
                try:
                    totp_input = await page.wait_for_selector(selector, timeout=5000)
                    if totp_input:
                        self.log(f"[{username}] 📱 Found 2FA input field with selector: {selector}")
                        break
                except:
                    continue
            
            if not totp_input:
                self.log(f"[{username}] ❌ Could not find 2FA input field.")
                return False
            
            # Enter TOTP code
            await totp_input.click()
            await page.keyboard.press('Control+a')
            await totp_input.fill(totp_code)
            self.log(f"[{username}] ✅ Entered TOTP code: {totp_code}")
            await self.human_delay(1500, 2500)
            
            # Look for submit button
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Confirm")',
                'div[role="button"]:has-text("Confirm")',
                'button:has-text("Continue")',
                '[role="button"]:has-text("Continue")',
                'button:has-text("Submit")',
                'div[role="button"]:has-text("Submit")',
                'button:has-text("Verify")',
                'button._aswp._aswr._aswu._asw_._asx2',
                'button[class*="_aswp"][class*="_aswr"][class*="_aswu"][class*="_asw_"][class*="_asx2"]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = await page.wait_for_selector(selector, timeout=3000)
                    if submit_button:
                        break
                except:
                    continue
            
            if submit_button:
                await submit_button.click()
                self.log(f"[{username}] 🚀 Clicked submit button for 2FA verification")
            else:
                await page.keyboard.press('Enter')
                self.log(f"[{username}] ⌨️ Pressed Enter for 2FA verification")
            
            await self.human_delay(5000, 7000) # Increased delay for verification
            
            # Check if verification was successful
            if not await self.is_verification_required(page):
                self.log(f"[{username}] ✅ 2FA verification successful!")
                return True
            else:
                self.log(f"[{username}] ❌ 2FA verification failed.")
                return False
                
        except Exception as e:
            self.log(f"[{username}] ❌ Error during 2FA verification: {e}", "ERROR")
            return False

    def should_stop(self):
        """Check if the script should stop"""
        return self.stop_flag_callback()

    async def login_instagram_with_cookies_and_2fa(self, page, context, username, password, account_number):
        """Enhanced login with cookie management and automatic 2FA handling
        
        Returns:
            tuple: (success: bool, auth_info: dict) - success status and authentication info
                   auth_info contains 'authentication_method' ('cookies' or 'credentials')
        """
        try:
            # Use the enhanced authentication system
            self.log(f"[Account {account_number}] 🔐 Starting enhanced authentication for {username}...")
            
            # Create a log callback for the authentication system
            def auth_log_callback(message):
                self.log(f"[Account {account_number}] {message}")
            
            # Use enhanced authentication with cookies and proxy
            success, auth_info = await enhanced_auth.authenticate_with_cookies_and_proxy(
                context=context,
                username=username,
                password=password,
                log_callback=auth_log_callback
            )
            
            if success:
                self.log(f"[Account {account_number}] ✅ Authentication successful!")
                self.log(f"[Account {account_number}] 📊 Method: {auth_info.get('authentication_method', 'unknown')}")
                self.log(f"[Account {account_number}] 🍪 Cookies loaded: {auth_info.get('cookies_loaded', False)}")
                self.log(f"[Account {account_number}] 💾 Cookies saved: {auth_info.get('cookies_saved', False)}")
                return True, auth_info  # Return both success and auth_info
            else:
                self.log(f"[Account {account_number}] ❌ Authentication failed")
                if auth_info.get('errors'):
                    for error in auth_info['errors']:
                        self.log(f"[Account {account_number}] ❌ Error: {error}", "ERROR")
                return False, auth_info  # Return both success and auth_info
                
        except Exception as e:
            self.log(f"[Account {account_number}] ❌ Login error: {e}", "ERROR")
            return False, {'authentication_method': 'unknown', 'errors': [str(e)]}

    def load_accounts_from_file(self, file_path):
        """Load Instagram credentials from Excel or CSV file."""
        try:
            # Determine file type and read accordingly
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            if df.empty:
                self.log("Error: Accounts file is empty.", "ERROR")
                return []
            
            # Check for required columns (case-insensitive)
            df.columns = df.columns.str.strip().str.title()
            required_columns = ["Username", "Password"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.log(f"Error: Missing columns in accounts file: {missing_columns}.", "ERROR")
                self.log(f"Available columns: {list(df.columns)}", "ERROR")
                return []
            
            # Load accounts
            accounts = []
            for i in range(len(df)):
                username = df.loc[i, "Username"]
                password = df.loc[i, "Password"]
                if pd.notna(username) and pd.notna(password):
                    accounts.append((str(username).strip(), str(password).strip()))
            
            self.log(f"Loaded {len(accounts)} account(s) from file.")
            return accounts
            
        except FileNotFoundError:
            self.log(f"Error: File {file_path} not found.", "ERROR")
            return []
        except Exception as e:
            self.log(f"Error loading accounts: {e}", "ERROR")
            return []

    def set_media_file(self, media_path):
        """Set the media file and determine if it's a video"""
        self.media_file = media_path
        file_ext = Path(media_path).suffix.lower()
        self.is_video = file_ext in self.supported_video_formats
        self.log(f"Media file set: {os.path.basename(media_path)} ({'Video' if self.is_video else 'Image'})")

    async def human_type(self, page, selector, text, delay_range=(50, 150)):
        """Type text with random delays"""
        if self.should_stop():
            return
        element = await page.wait_for_selector(selector, state='visible')
        await element.click()
        await page.wait_for_timeout(random.randint(300, 800))
        
        for char in text:
            if self.should_stop():
                return
            await element.type(char)
            await page.wait_for_timeout(random.randint(delay_range[0], delay_range[1]))

    async def update_visual_status(self, page, status_text, step=None):
        """Visual status updates disabled for VPS deployment"""
        pass  # No-op for headless mode

    async def human_delay(self, min_ms=1000, max_ms=3000):
        """Add human-like random delays."""
        if self.should_stop():
            return
        await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)

    async def handle_login_info_save_dialog(self, page, account_number):
        """Handle the 'Save your login info?' dialog by clicking 'Save info' only"""
        try:
            self.log(f"[Account {account_number}] 🔍 Checking for 'Save login info' dialog...")
            
            # Wait a moment for the dialog to fully load
            await self.human_delay(2000, 3000)
            
            # Check if we're on the save login info page
            current_url = page.url
            if "accounts/onetap" not in current_url:
                self.log(f"[Account {account_number}] ℹ️ Not on save login info page, current URL: {current_url}")
                return True  # Not an error, just not on that page
            
            self.log(f"[Account {account_number}] 🔧 On save login info page - looking for 'Save info' button...")
            self.log(f"[Account {account_number}] 📊 Page title: {await page.title()}")
            
            # Strategy 1: Try selectors for "Save info" button only
            simple_selectors = [
                # Save info button (only option now)
                'button.aswp._aswr._aswu._asw_._asx2:has-text("Save info")',
                'button:has-text("Save info")',
                ':text-is("Save info")',
                'text="Save info"',
                'button[type="button"]:has-text("Save info")',
                'div[role="button"]:has-text("Save info")',
                '[role="button"]:has-text("Save info")',
                'div:has-text("Save info")',
                '*:has-text("Save info")'
            ]
            
            # Add timeout to prevent infinite loops - max 30 seconds total
            start_time = time.time()
            max_duration = 30  # seconds
            
            for i, selector in enumerate(simple_selectors):
                if time.time() - start_time > max_duration:
                    self.log(f"[Account {account_number}] ⏰ Timeout reached after {max_duration} seconds", "WARNING")
                    break
                    
                try:
                    self.log(f"[Account {account_number}] 🎯 Trying selector {i+1}/{len(simple_selectors)}: {selector}")
                    
                    # Try to find and click the element
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # Verify element is visible
                        is_visible = await element.is_visible()
                        if is_visible:
                            # Get the actual text of the clicked element
                            element_text = await element.text_content()
                            await element.click()
                            self.log(f"[Account {account_number}] ✅ Clicked '{element_text}' button with selector {i+1}")
                            
                            # Wait and verify we moved away from the page
                            await self.human_delay(3000, 4000)
                            
                            new_url = page.url
                            if "accounts/onetap" not in new_url:
                                self.log(f"[Account {account_number}] ✅ Successfully saved login info!")
                                self.log(f"[Account {account_number}] 📊 New URL: {new_url}")
                                return True
                            else:
                                self.log(f"[Account {account_number}] ⚠️ Still on save login page after click, trying next selector...")
                                continue
                        else:
                            self.log(f"[Account {account_number}] ⚠️ Element found but not visible with selector {i+1}")
                            continue
                    else:
                        self.log(f"[Account {account_number}] ⚠️ No element found with selector {i+1}")
                        continue
                        
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ Selector {i+1} failed: {str(e)[:100]}")
                    continue
            
            # Strategy 2: Use modern Playwright locators with timeout
            if time.time() - start_time <= max_duration:
                self.log(f"[Account {account_number}] 🔄 Trying modern Playwright locators...")
                
                try:
                    # Try get_by_text approach with exact match - Save info only
                    save_info_locator = page.get_by_text("Save info", exact=True)
                    await save_info_locator.click(timeout=5000)
                    self.log(f"[Account {account_number}] ✅ Clicked 'Save info' button with get_by_text locator")
                    
                    await self.human_delay(3000, 4000)
                    new_url = page.url
                    if "accounts/onetap" not in new_url:
                        self.log(f"[Account {account_number}] ✅ Successfully saved login info!")
                        return True
                        
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ get_by_text locator failed: {str(e)[:100]}")
                
                try:
                    # Try get_by_role approach - Save info only
                    save_info_role = page.get_by_role("button", name=re.compile("save info", re.IGNORECASE))
                    await save_info_role.click(timeout=5000)
                    self.log(f"[Account {account_number}] ✅ Clicked 'Save info' button with get_by_role locator")
                    
                    await self.human_delay(3000, 4000)
                    new_url = page.url
                    if "accounts/onetap" not in new_url:
                        self.log(f"[Account {account_number}] ✅ Successfully saved login info!")
                        return True
                        
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ get_by_role locator failed: {str(e)[:100]}")
            
            # If all strategies fail, log and continue
            self.log(f"[Account {account_number}] ⚠️ Could not find 'Save info' button. Continuing anyway...", "WARNING")
            return True  # Continue script execution even if button not found
            
            # Strategy 4: Direct navigation (last resort) with timeout check
            if time.time() - start_time <= max_duration:
                self.log(f"[Account {account_number}] 🏠 Final resort: Direct navigation to Instagram home...")
                try:
                    await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=15000)
                    await self.human_delay(3000, 5000)
                    
                    final_url = page.url
                    if final_url == "https://www.instagram.com/" or final_url.startswith("https://www.instagram.com/?"):
                        self.log(f"[Account {account_number}] ✅ Direct navigation worked!")
                        return True
                        
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ Direct navigation failed: {e}")
            
            # If we reach here, all methods failed
            total_time = time.time() - start_time
            self.log(f"[Account {account_number}] ❌ All methods failed to dismiss save login dialog after {total_time:.1f} seconds", "ERROR")
            self.log(f"[Account {account_number}] 📊 Final URL: {page.url}")
            
            # Force continue anyway to prevent infinite loops
            self.log(f"[Account {account_number}] 🔄 Forcing continuation to prevent infinite loop...")
            return True  # Return True to continue the script instead of failing
            
        except Exception as e:
            self.log(f"[Account {account_number}] ❌ Error handling save login dialog: {e}", "ERROR")
            # Return True to continue instead of failing
            return True

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

    async def instagram_post_script(self, username, password, account_number, caption):
        """Main Instagram posting function for a single account."""
        self.log(f"[Account {account_number}] 🚀 Starting automation for {username}")
        self.log(f"[Account {account_number}] 📊 Script ID: {self.script_id}")
        self.log(f"[Account {account_number}] 📊 Media file: {os.path.basename(self.media_file) if self.media_file else 'None'}")
        
        if self.should_stop():
            self.log(f"[Account {account_number}] ⚠️ Stop flag detected at start - terminating", "WARNING")
            return None

        # Validate inputs
        if not username or not password:
            self.log(f"[Account {account_number}] ❌ Missing username or password", "ERROR")
            return False
        if not self.media_file or not os.path.exists(self.media_file):
            self.log(f"[Account {account_number}] ❌ Media file not found: {self.media_file}", "ERROR")
            return False

        try:
            async with async_playwright() as p:
                if self.should_stop():
                    self.log(f"[Account {account_number}] ⚠️ Stop flag detected before browser launch, terminating", "WARNING")
                    return
                
                # Get assigned proxy for this account
                proxy_string = proxy_manager.get_account_proxy(username)
                proxy_config = None
                if proxy_string:
                    proxy_info = proxy_manager.parse_proxy(proxy_string)
                    if proxy_info:
                        proxy_config = {
                            'server': proxy_info['server'],
                            'username': proxy_info['username'],
                            'password': proxy_info['password']
                        }
                        self.log(f"[Account {account_number}] Using assigned proxy: {proxy_info['host']}:{proxy_info['port']}")
                    else:
                        self.log(f"[Account {account_number}] No proxy assigned to this account")
                
                self.log(f"[Account {account_number}] 🚀 Launching browser...")

                # Configure browser launch args to avoid detection and redirects
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-hang-monitor',
                    '--disable-ipc-flooding-protection',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--no-zygote',
                    '--disable-logging',
                    '--disable-permissions-api',
                    '--ignore-certificate-errors',
                    '--allow-running-insecure-content'
                ]
                
                # Full size for headless mode
                viewport_width = 1920
                viewport_height = 1080
                
                browser = None
                try:
                    # Try Chromium first (more reliable)
                    self.log(f"[Account {account_number}] 🔧 Attempting to launch Chromium browser...")
                    browser = await p.chromium.launch(
                        headless=True, # Use headless mode for VPS
                        args=browser_args,
                        proxy=proxy_config,
                        slow_mo=100 # Small delay for visibility
                    )
                    self.log(f"[Account {account_number}] ✅ Chromium browser launched successfully")
                except Exception as chrome_error:
                    self.log(f"[Account {account_number}] ⚠️ Chromium launch failed: {chrome_error}")
                    
                    # Check if it's a browser installation issue
                    if "Executable doesn't exist" in str(chrome_error) or "playwright install" in str(chrome_error).lower():
                        self.log(f"[Account {account_number}] 🔧 Browser not installed. Attempting to install browsers...")
                        try:
                            import subprocess
                            result = subprocess.run(['playwright', 'install', 'chromium'], 
                                                  capture_output=True, text=True, timeout=300)
                            if result.returncode == 0:
                                self.log(f"[Account {account_number}] ✅ Browser installation completed. Retrying launch...")
                                # Retry browser launch after installation
                                browser = await p.chromium.launch(
                                    headless=True, # Use headless mode for VPS
                                    args=browser_args,
                                    proxy=proxy_config,
                                    slow_mo=100
                                )
                                self.log(f"[Account {account_number}] ✅ Chromium browser launched successfully after installation")
                            else:
                                self.log(f"[Account {account_number}] ❌ Browser installation failed: {result.stderr}", "ERROR")
                                # Try system-level installation
                                subprocess.run(['python', '-m', 'playwright', 'install', 'chromium'], timeout=300)
                                browser = await p.chromium.launch(
                                    headless=True, # Use headless mode for VPS
                                    args=browser_args,
                                    proxy=proxy_config,
                                    slow_mo=100
                                )
                                self.log(f"[Account {account_number}] ✅ Chromium browser launched after system installation")
                        except Exception as install_error:
                            self.log(f"[Account {account_number}] ❌ Browser installation failed: {install_error}", "ERROR")
                            # Fallback to basic launch without extra features
                            try:
                                self.log(f"[Account {account_number}] 🔄 Attempting basic browser launch...")
                                browser = await p.chromium.launch(
                                    headless=True,  # Use headless mode for VPS
                                    proxy=proxy_config
                                )
                                self.log(f"[Account {account_number}] ✅ Basic browser launched successfully")
                            except Exception as basic_error:
                                self.log(f"[Account {account_number}] ❌ All browser launch attempts failed: {basic_error}", "ERROR")
                                return False
                    else:
                        # Fallback to basic launch without extra features
                        try:
                            self.log(f"[Account {account_number}] 🔄 Attempting basic browser launch...")
                            browser = await p.chromium.launch(
                                headless=True, # Use headless mode for VPS
                                proxy=proxy_config
                            )
                            self.log(f"[Account {account_number}] ✅ Basic browser launched successfully")
                        except Exception as basic_error:
                            self.log(f"[Account {account_number}] ❌ All browser launch attempts failed: {basic_error}", "ERROR")
                            return False
                
                if not browser:
                    self.log(f"[Account {account_number}] ❌ Failed to launch browser", "ERROR")
                    return False
                
                try:
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        viewport={'width': viewport_width, 'height': viewport_height},
                        extra_http_headers={
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-User': '?1',
                            'Upgrade-Insecure-Requests': '1'
                        }
                    )
                    self.log(f"[Account {account_number}] ✅ Browser context created successfully")
                except Exception as e:
                    self.log(f"[Account {account_number}] ❌ Failed to create browser context: {e}", "ERROR")
                    await browser.close()
                    return False
                
                try:
                    # Use the default page that's automatically created with the context
                    pages = context.pages
                    if pages:
                        page = pages[0]
                    else:
                        page = await context.new_page()
                    
                    self.log(f"[Account {account_number}] ✅ Page created")
                    
                    # Log in
                    login_success, auth_info = await self.login_instagram_with_cookies_and_2fa(page, context, username, password, account_number)
                    
                    if not login_success:
                        self.log(f"[Account {account_number}] ❌ Login failed for {username}", "ERROR")
                        # Try to handle 2FA if it's the reason for failure
                        if auth_info.get('requires_2fa'):
                            totp_secret = get_account_details(username).get('totp_secret')
                            if totp_secret:
                                self.log(f"[Account {account_number}] 🔄 Retrying login with 2FA handling...")
                                if await self.handle_2fa_verification(page, username, totp_secret):
                                    login_success = True
                                else:
                                    self.log(f"[Account {account_number}] ❌ 2FA verification failed again. Aborting.", "ERROR")
                                    return False
                            else:
                                self.log(f"[Account {account_number}] ❌ 2FA required but no TOTP secret provided. Aborting.", "ERROR")
                                return False
                        else:
                            return False

                    # Check for save login info dialog and dismiss it
                    await self.handle_login_info_save_dialog(page, account_number)
                    
                    # Post the media
                    post_success = await self.post_to_instagram(page, username, caption)
                    
                    return post_success
                    
                except Exception as e:
                    self.log(f"[Account {account_number}] ❌ An error occurred during the posting process: {e}", "ERROR")
                    traceback.print_exc()
                    return False
                finally:
                    await self.human_delay(1500, 2500)
                    self.log(f"[Account {account_number}] 🚪 Closing browser...")
                    if browser:
                        await browser.close()
                    self.log(f"[Account {account_number}] ✅ Browser closed")
                    
        except Exception as e:
            self.log(f"[Account {account_number}] ❌ Unhandled error: {e}", "ERROR")
            traceback.print_exc()
            return False

    async def post_to_instagram(self, page, username, caption=""):
        """Navigate to the posting page and upload the media."""
        self.log(f"[{username}] 🎨 Starting post process...")
        try:
            # Check for stop flag
            if self.should_stop():
                self.log(f"[{username}] ⚠️ Stop flag detected before posting - terminating", "WARNING")
                return False
                
            await self.human_delay(2000, 3000)
            
            # Click the 'Create' button (plus icon)
            self.log(f"[{username}] ➕ Looking for 'Create' button...")
            
            # UPDATED SELECTORS FOR 'Create' button
            create_button_selectors = [
                '[aria-label="New post"]',
                '[aria-label="Create"]',
                'div[role="button"]:has-text("Create")',
                'svg[aria-label="New post"]',
                'svg[aria-label="Create"]',
                'div[role="button"] > svg[aria-label="New post"]',
                '[data-testid="creation-tab"]',
                'div[role="button"][class*="x1i10h51"][class*="x6umtig"][class*="x1b1mb9l"]'
            ]
            
            create_button = None
            for selector in create_button_selectors:
                try:
                    self.log(f"[{username}] 🎯 Trying create button selector: {selector}")
                    create_button = await page.wait_for_selector(selector, timeout=5000)
                    if create_button:
                        await create_button.click()
                        self.log(f"[{username}] ✅ Clicked 'Create' button with selector: {selector}")
                        break
                except Exception as e:
                    self.log(f"[{username}] ⚠️ Selector failed: {selector} - {str(e)[:100]}")
                    continue
            
            if not create_button:
                self.log(f"[{username}] ❌ Could not find 'Create' button after all attempts. Aborting post.", "ERROR")
                return False
                
            await self.human_delay(3000, 5000)
            
            # Select the "Select from computer" button
            self.log(f"[{username}] 🖥️ Looking for 'Select from computer' button...")
            select_from_computer_button_selectors = [
                'text="Select from computer"',
                'button:has-text("Select from computer")',
                'div[role="button"]:has-text("Select from computer")',
                '[role="button"]:has-text("Select from computer")',
                'div:has-text("Select from computer")'
            ]
            
            select_button = None
            for selector in select_from_computer_button_selectors:
                try:
                    select_button = await page.wait_for_selector(selector, timeout=5000)
                    if select_button:
                        self.log(f"[{username}] ✅ Found 'Select from computer' button with selector: {selector}")
                        break
                except:
                    continue
            
            if not select_button:
                self.log(f"[{username}] ❌ Could not find 'Select from computer' button. Aborting post.", "ERROR")
                return False
                
            # Get the file chooser for the input element
            async with page.expect_file_chooser() as fc_info:
                await select_button.click()
            file_chooser = await fc_info.value
            
            # Upload the media file
            self.log(f"[{username}] 📤 Uploading media file: {self.media_file}")
            await file_chooser.set_files(self.media_file)
            self.log(f"[{username}] ✅ Media file uploaded successfully")
            
            # Wait for file to load
            await self.human_delay(5000, 7000)
            
            # -----------------------------------------------------------
            # REVISED LOGIC FOR CLICKING 'NEXT' BUTTON
            # -----------------------------------------------------------
            next_button_selectors = [
                'button:has-text("Next")',
                'div[role="button"]:has-text("Next")',
                'div[aria-label="Next"]',
                'svg[aria-label="Next"]',
                '[data-testid="next-button"]',
                'button[class*="x1q0g3np"][type="button"]',
                'button[class*="_aswp"][class*="_aswr"]'
            ]
            
            next_clicked = True
            start_time = time.time()
            max_duration = 60 # seconds to wait for all 'Next' steps
            
            while next_clicked and time.time() - start_time < max_duration:
                next_clicked = False
                for i, selector in enumerate(next_button_selectors):
                    try:
                        self.log(f"[{username}] ➡️ Looking for 'Next' button (attempt {i+1})...")
                        next_button = await page.wait_for_selector(selector, timeout=5000)
                        if next_button and await next_button.is_visible():
                            await next_button.click()
                            self.log(f"[{username}] 🚀 Clicked 'Next' button with selector: {selector}")
                            next_clicked = True
                            await self.human_delay(2000, 3000)
                            break # Break the inner loop and check again for another 'Next' button
                    except TimeoutError:
                        continue # Selector not found, try the next one
                    except Exception as e:
                        self.log(f"[{username}] ⚠️ Selector for 'Next' failed: {selector} - {str(e)[:100]}")
                        
            if next_clicked: # If the loop exited because `next_clicked` was still true, it means a button was found and clicked on the last pass. Wait a bit more.
                await self.human_delay(2000, 3000)
            
            self.log(f"[{username}] ✅ All 'Next' buttons have been handled. Proceeding to caption step.")
            # -----------------------------------------------------------
            # END OF REVISED LOGIC
            # -----------------------------------------------------------
            
            # Add caption
            if caption:
                self.log(f"[{username}] 📝 Adding caption...")
                caption_input_selectors = [
                    'textarea[aria-label="Write a caption..."]',
                    'textarea[placeholder="Write a caption..."]',
                    '[data-testid="caption-input"]',
                    'div[role="textbox"]',
                    'div[contenteditable="true"]',
                    'div[class*="x1i10h51"][class*="x1ejq31s"][class*="x1d50bp1"]' # Broad class match for caption div
                ]
                
                caption_input = None
                for selector in caption_input_selectors:
                    try:
                        self.log(f"[{username}] 🎯 Trying caption input selector: {selector}")
                        caption_input = await page.wait_for_selector(selector, timeout=5000)
                        if caption_input:
                            await caption_input.click()
                            self.log(f"[{username}] ✅ Found caption input with selector: {selector}")
                            break
                    except:
                        continue
                
                if caption_input:
                    await self.human_type(page, selector, caption, delay_range=(10, 50))
                    self.log(f"[{username}] ✅ Caption entered successfully")
                else:
                    self.log(f"[{username}] ❌ Could not find caption input. Skipping caption.", "ERROR")
            else:
                self.log(f"[{username}] ℹ️ No caption provided. Skipping.")
                
            await self.human_delay(2000, 3000)
            
            # -----------------------------------------------------------
            # IMPROVED LOGIC FOR CLICKING 'SHARE' AND CONFIRMING SUCCESS
            # -----------------------------------------------------------
            try:
                self.log(f"[{username}] 📤 Attempting to find and click the 'Share' button...")
                
                # Wait for the page to be fully loaded before looking for Share button
                await self.human_delay(3000, 5000)
                
                # More comprehensive Share button selectors based on Instagram's current structure
                share_button_selectors = [
                    # Primary selectors - most likely to work
                    'div[role="button"]:has-text("Share")',
                    'button:has-text("Share")',
                    'div[role="button"]:has-text("Publish")',
                    'button:has-text("Publish")',
                    
                    # Instagram-specific class combinations (updated for current UI)
                    'div._acan._acao._acas._aj1-._ap30[role="button"]',
                    'div.x1i10hfl.xjqpnuy.xa49m3k.xqeqjp1.x2hbi6w.x13fuv20.xu3j5b3.x1q0q8m5.x26u7qi.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1ypdohk.xdl72j9.xe8uvvx.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x2lwn1j.xeuugli.x16tdsg8.xggy1nq.x1ja2u2z.x1t137rt.x6s0dn4.x1ejq31n.xd10rxx.x1sy0etr.x17r0tee.x3nfvp2[role="button"]',
                    'div.x1n2onr6:has-text("Share")',
                    'div.x1n2onr6:has-text("Publish")',
                    
                    # Aria-label based selectors
                    '[aria-label="Share"]',
                    '[aria-label="Publish"]',
                    '[aria-label="Share post"]',
                    '[aria-label="Publish post"]',
                    
                    # Data attributes
                    '[data-testid="share-button"]',
                    '[data-testid="publish-button"]',
                    '[data-testid="post-button"]',
                    
                    # Text-based selectors with exact match
                    'text="Share"',
                    'text="Publish"',
                    ':text-is("Share")',
                    ':text-is("Publish")',
                    
                    # Broader selectors for fallback
                    'div[role="button"]:visible:has-text("Share")',
                    'button:visible:has-text("Share")',
                    'div[role="button"]:visible:has-text("Publish")',
                    'button:visible:has-text("Publish")',
                    
                    # XPath selectors as last resort
                    '//div[@role="button" and contains(text(), "Share")]',
                    '//button[contains(text(), "Share")]',
                    '//div[@role="button" and contains(text(), "Publish")]',
                    '//button[contains(text(), "Publish")]',
                    
                    # Generic button selectors (very last resort)
                    'div[role="button"]:last-child',
                    'button[type="button"]:last-child'
                ]
                
                # First attempt: Try each selector with a short timeout
                share_button_found = False
                for i, selector in enumerate(share_button_selectors):
                    if self.should_stop():
                        return False
                        
                    try:
                        self.log(f"[{username}] 🎯 Trying Share button selector {i+1}/{len(share_button_selectors)}: {selector[:50]}...")
                        
                        # Wait for element to be visible
                        element = await page.wait_for_selector(selector, state='visible', timeout=8000)
                        
                        if element:
                            # Verify it's actually clickable and visible
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            
                            if is_visible and is_enabled:
                                # Get element text to confirm it's the right button
                                element_text = await element.text_content()
                                element_text = element_text.strip() if element_text else ""
                                
                                # Check if it contains Share/Publish text or if it's the last button in the sequence
                                if any(keyword in element_text.lower() for keyword in ['share', 'publish']) or i >= len(share_button_selectors) - 2:
                                    self.log(f"[{username}] ✅ Found Share button with text: '{element_text}' using selector {i+1}")
                                    
                                    # Scroll element into view if needed
                                    await element.scroll_into_view_if_needed()
                                    await self.human_delay(500, 1000)
                                    
                                    # Click the button
                                    await element.click()
                                    self.log(f"[{username}] 🚀 Successfully clicked Share button!")
                                    share_button_found = True
                                    break
                                else:
                                    self.log(f"[{username}] ⚠️ Button found but text doesn't match: '{element_text}'")
                                    continue
                            else:
                                self.log(f"[{username}] ⚠️ Element found but not visible/enabled")
                                continue
                        
                    except TimeoutError:
                        self.log(f"[{username}] ⚠️ Share button selector {i+1} timed out")
                        continue
                    except Exception as e:
                        self.log(f"[{username}] ⚠️ Share button selector {i+1} failed: {str(e)[:100]}")
                        continue
                
                # Second attempt: Use Playwright's modern locators if first attempt failed
                if not share_button_found:
                    self.log(f"[{username}] 🔄 Trying modern Playwright locators for Share button...")
                    
                    try:
                        # Try get_by_text with exact match
                        share_locator = page.get_by_text("Share", exact=True)
                        if await share_locator.count() > 0:
                            await share_locator.click(timeout=10000)
                            self.log(f"[{username}] ✅ Clicked Share button with get_by_text locator")
                            share_button_found = True
                        else:
                            # Try with "Publish" text
                            publish_locator = page.get_by_text("Publish", exact=True)
                            if await publish_locator.count() > 0:
                                await publish_locator.click(timeout=10000)
                                self.log(f"[{username}] ✅ Clicked Publish button with get_by_text locator")
                                share_button_found = True
                    except Exception as e:
                        self.log(f"[{username}] ⚠️ Modern locators failed: {str(e)[:100]}")
                
                # Third attempt: Use get_by_role if still not found
                if not share_button_found:
                    self.log(f"[{username}] 🔄 Trying get_by_role locator for Share button...")
                    
                    try:
                        # Try get_by_role for button with Share text
                        share_role = page.get_by_role("button", name=re.compile("share|publish", re.IGNORECASE))
                        if await share_role.count() > 0:
                            await share_role.click(timeout=10000)
                            self.log(f"[{username}] ✅ Clicked Share button with get_by_role locator")
                            share_button_found = True
                    except Exception as e:
                        self.log(f"[{username}] ⚠️ get_by_role locator failed: {str(e)[:100]}")
                
                # Fourth attempt: Look for any button in the footer/action area
                if not share_button_found:
                    self.log(f"[{username}] 🔄 Looking for any action button in footer area...")
                    
                    try:
                        # Look for buttons in common footer/action areas
                        footer_button_selectors = [
                            'div[role="dialog"] div:last-child button',
                            'div[role="dialog"] div:last-child div[role="button"]',
                            'form button[type="button"]:last-child',
                            'div[data-testid*="footer"] button',
                            'div[data-testid*="action"] button'
                        ]
                        
                        for selector in footer_button_selectors:
                            try:
                                buttons = await page.query_selector_all(selector)
                                if buttons:
                                    # Click the last button (usually the primary action)
                                    last_button = buttons[-1]
                                    if await last_button.is_visible() and await last_button.is_enabled():
                                        button_text = await last_button.text_content()
                                        await last_button.click()
                                        self.log(f"[{username}] ✅ Clicked footer button with text: '{button_text}'")
                                        share_button_found = True
                                        break
                            except:
                                continue
                                
                    except Exception as e:
                        self.log(f"[{username}] ⚠️ Footer button search failed: {str(e)[:100]}")
                
                if not share_button_found:
                    self.log(f"[{username}] ❌ Could not find Share button after all attempts. Aborting post.", "ERROR")
                    return False

                # Wait for upload to complete
                self.log(f"[{username}] ⏳ Waiting for post to upload...")
                await self.human_delay(5000, 8000)

                # Check for success with improved detection
                success_message_selectors = [
                    'text="Your post has been shared."',
                    'text="Your post was shared."',
                    'text="Post shared"',
                    'text="Post published"',
                    'text="Your post is now live"',
                    'text="Posted"',
                    'div:has-text("shared")',
                    'div:has-text("published")',
                    'div:has-text("posted")'
                ]
                
                post_successful = False
                for selector in success_message_selectors:
                    try:
                        await page.wait_for_selector(selector, state='attached', timeout=30000)
                        self.log(f"[{username}] 🎉 Post uploaded successfully! Success message found.")
                        post_successful = True
                        break
                    except TimeoutError:
                        continue
                
                # Alternative success check: URL change or modal disappearance
                if not post_successful:
                    self.log(f"[{username}] 🔄 Checking alternative success indicators...")
                    
                    try:
                        # Check if we're redirected to home or profile
                        current_url = page.url
                        if any(indicator in current_url for indicator in ['/instagram.com/', '/instagram.com/p/', f'/instagram.com/{username}/']):
                            self.log(f"[{username}] ✅ URL changed to: {current_url} - Post likely successful")
                            post_successful = True
                        else:
                            # Check if create post modal is gone
                            modal_selectors = [
                                '[aria-label="Create new post"]',
                                '[role="dialog"]',
                                'div[role="dialog"]:has-text("Create")'
                            ]
                            
                            modal_gone = True
                            for modal_selector in modal_selectors:
                                try:
                                    modal = await page.query_selector(modal_selector)
                                    if modal and await modal.is_visible():
                                        modal_gone = False
                                        break
                                except:
                                    continue
                            
                            if modal_gone:
                                self.log(f"[{username}] ✅ Create post modal disappeared - Post likely successful")
                                post_successful = True
                            else:
                                self.log(f"[{username}] ❌ Post creation modal still visible - Post may have failed")
                    
                    except Exception as e:
                        self.log(f"[{username}] ⚠️ Alternative success check failed: {e}")
                
                return post_successful
                
            except Exception as e:
                self.log(f"[{username}] ❌ An error occurred during the final share step: {e}", "ERROR")
                traceback.print_exc()
                return False
            # -----------------------------------------------------------
            # END OF IMPROVED LOGIC
            # -----------------------------------------------------------
            
        except Exception as e:
            self.log(f"[{username}] ❌ An error occurred during the posting process: {e}", "ERROR")
            traceback.print_exc()
            return False

    async def run_individual_post(self, account_details, media_file, caption, script_id, log_callback, stop_callback, lock):
        """Run the posting script for a single account within a concurrent setup."""
        username = account_details.get("username")
        password = account_details.get("password")
        
        # Instantiate a new automation object for each account
        automation = InstagramDailyPostAutomation(script_id, log_callback, stop_callback)
        automation.set_media_file(media_file)
        
        async with lock:
            if automation.should_stop():
                automation.log(f"[{username}] ⚠️ Stop flag detected before starting account process. Skipping.")
                return False
        
        try:
            success = await automation.instagram_post_script(username, password, account_details.get("account_number", "N/A"), caption)
            return success
        except Exception as e:
            automation.log(f"[{username}] ❌ An error occurred during run_individual_post: {e}", "ERROR")
            traceback.print_exc()
            return False

    async def run_automation(self, accounts_file, media_file, concurrent_accounts=5, caption="", auto_generate_caption=True):
        """Main function to run the automation for all accounts concurrently."""
        self.log("🏁 Starting Instagram Daily Post Automation...")

        if self.should_stop():
            self.log("⚠️ Stop flag detected at the start. Aborting.", "WARNING")
            return False
            
        # Set the media file for the entire automation run
        self.set_media_file(media_file)

        # Load accounts from file
        accounts = self.load_accounts_from_file(accounts_file)
        if not accounts:
            self.log("❌ No accounts loaded. Automation stopped.", "ERROR")
            return False
            
        self.log(f"⚙️ Running automation for {len(accounts)} accounts with concurrency limit: {concurrent_accounts}")
        
        # Create a lock to manage concurrent access to shared resources (if any)
        lock = asyncio.Lock()
        
        tasks = []
        for i, (username, password) in enumerate(accounts):
            account_details = {
                "username": username,
                "password": password,
                "account_number": i + 1,
                "totp_secret": get_account_details(username).get('totp_secret') # Fetch TOTP secret
            }
            task = asyncio.create_task(
                self.run_individual_post(account_details, media_file, caption, self.script_id, self.log_callback, self.stop_flag_callback, lock)
            )
            tasks.append(task)
            
            # Wait for a number of tasks to complete before adding more
            if len(tasks) >= concurrent_accounts:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending) # Keep only pending tasks
                
        # Wait for any remaining tasks to finish
        if tasks:
            results = await asyncio.gather(*tasks)
            successful_count = sum(1 for result in results if result)
            
            if successful_count > 0:
                self.log(f"⚠️ Partial success: {successful_count}/{len(accounts)} accounts completed successfully.", "WARNING")
            else:
                self.log(f"❌ No accounts completed successfully. {len(accounts)} accounts failed.", "ERROR")
            
            self.log(f"Automation finished! {successful_count}/{len(accounts)} accounts processed successfully.")
            return successful_count > 0
        
        return True

# Async function to run the automation (to be called from Flask)
async def run_daily_post_automation(script_id, accounts_file, media_file, concurrent_accounts=5, 
                                   caption="", auto_generate_caption=True,
                                   log_callback=None, stop_callback=None):
    """Main function to run the automation"""
    automation = InstagramDailyPostAutomation(script_id, log_callback, stop_callback)
    
    try:
        success = await automation.run_automation(
            accounts_file=accounts_file,
            media_file=media_file,
            concurrent_accounts=concurrent_accounts,
            caption=caption,
            auto_generate_caption=auto_generate_caption
        )
        return success
    except Exception as e:
        if log_callback:
            log_callback(f"Automation failed: {e}", "ERROR")
        return False