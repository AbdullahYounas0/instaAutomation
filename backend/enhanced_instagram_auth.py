"""
Enhanced Instagram Authentication System
Integrates cookie-based authentication with proxy management and 2FA support
"""

import asyncio
import random
import time
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from playwright.async_api import Page, BrowserContext
import pyotp

from instagram_cookie_manager import cookie_manager
from instagram_accounts import get_account_details
from proxy_manager import proxy_manager

logger = logging.getLogger(__name__)

class EnhancedInstagramAuth:
    def __init__(self):
        self.login_attempts = {}
        self.session_info = {}
    
    async def authenticate_with_cookies_and_proxy(
        self, 
        context: BrowserContext, 
        username: str, 
        password: str = None, 
        log_callback: callable = None
    ) -> Tuple[bool, Dict]:
        """
        Enhanced authentication flow:
        1. Load proxy for the account
        2. Check and load existing cookies first
        3. If cookies fail or don't exist, perform credential login with 2FA
        4. Save new cookies after successful login
        
        Args:
            context: Playwright browser context
            username: Instagram username
            password: Instagram password (optional if cookies exist)
            log_callback: Function to call for logging messages
            
        Returns:
            Tuple[bool, Dict]: (success, info_dict)
        """
        info = {
            'username': username,
            'authentication_method': None,
            'proxy_used': None,
            'cookies_loaded': False,
            'cookies_saved': False,
            'login_time': datetime.now().isoformat(),
            'session_valid': False,
            'errors': []
        }
        
        def log(message: str, level: str = "INFO"):
            if log_callback:
                log_callback(f"[{username}] {message}")
            logger.log(getattr(logging, level, logging.INFO), f"[{username}] {message}")
        
        try:
            # Step 1: Get and set up proxy
            proxy_info = await self._setup_proxy_for_account(context, username, log)
            info['proxy_used'] = proxy_info
            
            # Step 2: Use default page or create new page
            pages = context.pages
            if pages:
                page = pages[0]  # Use the first (default) page
                log("✅ Using default browser page")
            else:
                # Fallback: create a new page if no default page exists
                page = await context.new_page()
                log("✅ Created new browser page")
            
            # Block Facebook domains to prevent redirects
            await page.route("**facebook.com**", lambda route: route.abort())
            await page.route("**fb.com**", lambda route: route.abort())
            await page.route("**fbcdn.net**", lambda route: route.abort())
            log("🚫 Blocked Facebook domains to prevent redirects")
            
            # Set user agent and other headers to appear more human
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Execute JavaScript to hide automation indicators
            await page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock languages and plugins
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override the `plugins` property to use a custom getter.
                Object.defineProperty(navigator, 'plugins', {
                    get: function() {
                        return [
                            {
                                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Plugin"
                            },
                            {
                                0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin},
                                description: "",
                                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                                length: 1,
                                name: "Chrome PDF Viewer"
                            }
                        ];
                    }
                });
                
                // Overwrite the `chrome` object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Mock screen properties
                Object.defineProperty(screen, 'colorDepth', {
                    get: () => 24,
                });
                
                Object.defineProperty(screen, 'pixelDepth', {
                    get: () => 24,
                });
                
                // Block any attempts to redirect to Facebook
                const originalLocation = window.location;
                Object.defineProperty(window, 'location', {
                    get: function() {
                        return originalLocation;
                    },
                    set: function(url) {
                        if (typeof url === 'string' && (url.includes('facebook.com') || url.includes('fb.com'))) {
                            console.log('Blocked Facebook redirect attempt');
                            return;
                        }
                        originalLocation.href = url;
                    }
                });
            """)
            
            log("🛡️ Applied anti-detection and anti-redirect measures")
            
            # Step 3: Try cookie-based authentication first (with extended session timeout)
            log("🍪 Checking for existing cookies...")
            if cookie_manager.are_cookies_valid(username):
                log("✅ Valid cookies found, attempting cookie-based login...")
                success = await self._authenticate_with_cookies(page, username, log)
                
                if success:
                    info['authentication_method'] = 'cookies'
                    info['cookies_loaded'] = True
                    info['session_valid'] = True
                    log("🎉 Cookie-based authentication successful!")
                    # Don't close the page - return success but keep page open for daily post workflow
                    return True, info
                else:
                    log("⚠️ Cookie-based authentication failed, falling back to credentials...")
                    # Clean up invalid cookies
                    cookie_manager.delete_cookies(username)
            else:
                # Check if cookies exist but are expired 
                cookie_data = cookie_manager.load_cookies(username)
                if cookie_data:
                    log("⚠️ Cookies exist but appear to be expired or invalid, will attempt to refresh...")
                    # Clean up expired cookies
                    cookie_manager.delete_cookies(username)
                else:
                    log("ℹ️ No valid cookies found, proceeding with credential login...")
            
            # Step 4: Credential-based authentication with 2FA
            if not password:
                log("❌ No password provided and cookies failed")
                info['errors'].append("No password provided and cookies failed")
                await page.close()
                return False, info
            
            log("🔑 Starting credential-based authentication...")
            success, totp_secret = await self._authenticate_with_credentials(page, username, password, log)
            
            if success:
                info['authentication_method'] = 'credentials'
                info['session_valid'] = True
                
                # Step 5: Save cookies after successful credential login
                log("💾 Saving session cookies...")
                if await self._save_session_cookies(page, username, proxy_info, log):
                    info['cookies_saved'] = True
                    log("✅ Cookies saved successfully!")
                else:
                    log("⚠️ Failed to save cookies")
                    info['errors'].append("Failed to save cookies after successful login")
                
                log("🎉 Credential-based authentication successful!")
                # Don't close the page - return success but keep page open for daily post workflow
                return True, info
            else:
                log("❌ Credential-based authentication failed")
                info['errors'].append("Credential-based authentication failed")
                # Close page on failure
                await page.close()
                return False, info
        
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            log(error_msg, "ERROR")
            info['errors'].append(error_msg)
            try:
                if 'page' in locals():
                    await page.close()
            except:
                pass
            return False, info
    
    async def _setup_proxy_for_account(self, context: BrowserContext, username: str, log: callable) -> Optional[Dict]:
        """Get proxy information for the account (proxy is already configured in context)"""
        try:
            # Get the proxy that was already set up for this account
            proxy_string = proxy_manager.get_account_proxy(username)
            
            if proxy_string:
                parsed_proxy = proxy_manager.parse_proxy(proxy_string)
                if parsed_proxy:
                    proxy_info = {
                        'proxy': proxy_string,
                        'host': parsed_proxy['host'],
                        'port': parsed_proxy['port'],
                        'index': proxy_manager.get_all_proxies().index(proxy_string) + 1 if proxy_string in proxy_manager.get_all_proxies() else 0
                    }
                    log(f"📡 Using assigned proxy: {proxy_info['host']}:{proxy_info['port']} (Index: {proxy_info['index']})")
                    return proxy_info
            
            # If no proxy assigned, try to assign one
            try:
                assigned_proxy = proxy_manager.assign_proxy_to_account(username)
                if assigned_proxy:
                    parsed_proxy = proxy_manager.parse_proxy(assigned_proxy)
                    proxy_info = {
                        'proxy': assigned_proxy,
                        'host': parsed_proxy['host'],
                        'port': parsed_proxy['port'],
                        'index': proxy_manager.get_all_proxies().index(assigned_proxy) + 1
                    }
                    log(f"🆕 Auto-assigned proxy: {proxy_info['host']}:{proxy_info['port']} (Index: {proxy_info['index']})")
                    return proxy_info
            except Exception as e:
                    log(f"⚠️ Could not assign proxy: {e}")
                    return None
        except Exception as e:
            log(f"⚠️ Error setting up proxy: {e}")
            return None
    
    async def _authenticate_with_cookies(self, page: Page, username: str, log: callable) -> bool:
        """Authenticate using saved cookies"""
        try:
            # Load cookies
            cookie_data = cookie_manager.load_cookies(username)
            if not cookie_data or not cookie_data.get('cookies'):
                return False
            
            cookies = cookie_data['cookies']
            
            # Go to Instagram homepage first with redirect protection
            log("🌐 Navigating to Instagram homepage...")
            
            # Multiple attempts to avoid Facebook redirects
            for attempt in range(3):
                await page.goto("about:blank")
                await self._human_delay(1000, 2000)
                
                await page.goto("https://www.instagram.com/", wait_until='domcontentloaded', timeout=30000)
                
                current_url = page.url.lower()
                if "facebook.com" in current_url:
                    log(f"⚠️ Facebook redirect detected on cookie auth attempt {attempt + 1}")
                    if attempt < 2:
                        await self._human_delay(3000, 5000)
                        continue
                    else:
                        log("⚠️ Persistent Facebook redirect during cookie auth")
                        return False
                elif "instagram.com" in current_url:
                    log("✅ Successfully reached Instagram for cookie auth")
                    break
                else:
                    log(f"⚠️ Unexpected URL during cookie auth: {current_url}")
                    return False
            
            await self._human_delay(2000, 4000)
            
            # Add cookies to the page
            await page.context.add_cookies(cookies)
            log(f"🍪 Loaded {len(cookies)} cookies")
            
            # Navigate to Instagram again to use cookies
            log("🔄 Reloading page with cookies...")
            await page.goto("https://www.instagram.com/", wait_until='domcontentloaded', timeout=30000)
            
            # Check for Facebook redirect again
            current_url = page.url
            if "facebook.com" in current_url.lower():
                log("⚠️ Facebook redirect detected after adding cookies")
                return False
            
            await self._human_delay(3000, 5000)
            
            # Check if we're logged in
            if await self._is_logged_in(page):
                log("✅ Cookie authentication successful")
                return True
            else:
                log("❌ Cookies didn't work, may be expired")
                return False
                
        except Exception as e:
            log(f"❌ Error during cookie authentication: {e}", "ERROR")
            return False
    
    async def _authenticate_with_credentials(self, page: Page, username: str, password: str, log: callable) -> Tuple[bool, str]:
        """Authenticate using username/password with 2FA support"""
        try:
            # Get account details for TOTP secret
            account_details = get_account_details(username)
            totp_secret = account_details.get('totp_secret', '') if account_details else ''
            
            # Navigate to login page with Facebook redirect prevention
            log("🌐 Navigating to Instagram login page...")
            
            # First, ensure we're starting fresh and not getting redirected
            max_redirect_attempts = 3
            for attempt in range(max_redirect_attempts):
                try:
                    log(f"🔄 Navigation attempt {attempt + 1}/{max_redirect_attempts}")
                    
                    # Clear any existing navigation
                    await page.goto("about:blank")
                    await self._human_delay(1000, 2000)
                    
                    # Navigate directly to Instagram login
                    await page.goto("https://www.instagram.com/accounts/login/", 
                                  wait_until='domcontentloaded', timeout=45000)
                    
                    await self._human_delay(2000, 3000)
                    
                    # Check the final URL after navigation
                    current_url = page.url.lower()
                    log(f"📍 Current URL after navigation: {current_url}")
                    
                    if "facebook.com" in current_url:
                        log(f"⚠️ Facebook redirect detected on attempt {attempt + 1}")
                        if attempt < max_redirect_attempts - 1:
                            log("🔄 Retrying with different approach...")
                            # Try going to main Instagram page first
                            await page.goto("https://www.instagram.com/", 
                                          wait_until='domcontentloaded', timeout=30000)
                            await self._human_delay(3000, 5000)
                            continue
                        else:
                            log("❌ Persistent Facebook redirect - likely proxy/network issue")
                            return False, totp_secret
                    
                    elif "instagram.com" in current_url:
                        log("✅ Successfully reached Instagram")
                        break
                    else:
                        log(f"⚠️ Unexpected URL: {current_url}")
                        if attempt < max_redirect_attempts - 1:
                            continue
                        else:
                            log("❌ Failed to reach Instagram after all attempts")
                            return False, totp_secret
                            
                except Exception as e:
                    log(f"⚠️ Navigation attempt {attempt + 1} failed: {e}")
                    if attempt == max_redirect_attempts - 1:
                        log("❌ All navigation attempts failed")
                        return False, totp_secret
                    await self._human_delay(2000, 4000)
            
            await self._human_delay(3000, 5000)
            
            # Handle multiple potential blocking dialogs
            await self._handle_initial_dialogs(page, log)
            
            # Wait for login form with better error handling and multiple selectors
            log("⏳ Waiting for login form to load...")
            
            # First, check for and dismiss any blocking dialogs or overlays
            await self._dismiss_blocking_elements(page, log)
            
            # Wait longer for Instagram's dynamic content to load
            await self._human_delay(5000, 8000)
            
            login_form_selectors = [
                'input[name="username"]',
                'input[aria-label="Phone number, username, or email"]',
                'input[aria-label="Phone number, username or email address"]',
                '#loginForm input[name="username"]',
                'form input[name="username"]',
                'input[placeholder*="username"]',
                'input[placeholder*="email"]',
                'input[type="text"]',  # More generic fallback
                'form input[type="text"]:first-child'  # Very generic fallback
            ]
            
            form_found = False
            working_selector = None
            
            # First try to wait a bit and see if the page stabilizes
            await self._human_delay(3000, 5000)
            
            for i, selector in enumerate(login_form_selectors, 1):
                try:
                    log(f"🎯 Trying login form selector {i}/{len(login_form_selectors)}: {selector}")
                    await page.wait_for_selector(selector, state='visible', timeout=8000)
                    
                    # Double check the element is actually a username field
                    element = await page.query_selector(selector)
                    if element:
                        element_attrs = await element.evaluate('el => ({name: el.name, placeholder: el.placeholder, type: el.type, ariaLabel: el.ariaLabel})')
                        log(f"✅ Found element with attributes: {element_attrs}")
                        
                        # Verify it's likely a username field
                        attrs_str = str(element_attrs).lower()
                        if any(keyword in attrs_str for keyword in ['username', 'email', 'phone']):
                            log(f"✅ Login form detected with selector {i}")
                            working_selector = selector
                            form_found = True
                            break
                        else:
                            log(f"⚠️ Element found but doesn't seem like username field: {element_attrs}")
                    
                except Exception as e:
                    log(f"⚠️ Form selector {i} failed: {str(e)[:100]}")
                    continue
            
            if not form_found:
                # Log debugging info without screenshot for VPS
                page_title = await page.title()
                page_url = page.url
                log(f"📄 Page title: {page_title}")
                log(f"🔗 Page URL: {page_url}")
                
                # Check if we're still on Facebook or another wrong page
                if "facebook.com" in page_url.lower():
                    log("❌ Still on Facebook page, this indicates proxy/network issue")
                elif "instagram.com" not in page_url.lower():
                    log(f"❌ On wrong page: {page_url}")
                else:
                    log("❌ Login form not found on Instagram page - checking for alternative layouts")
                    
                    # Try to find any input fields at all
                    all_inputs = await page.query_selector_all('input')
                    log(f"🔍 Found {len(all_inputs)} input fields on page")
                    
                    for idx, input_elem in enumerate(all_inputs[:5]):  # Check first 5 inputs
                        try:
                            attrs = await input_elem.evaluate('el => ({name: el.name, placeholder: el.placeholder, type: el.type, ariaLabel: el.ariaLabel, id: el.id})')
                            log(f"Input {idx + 1}: {attrs}")
                        except:
                            pass
                
                return False, totp_secret
            
            log("✅ Login form is ready for input")
            
            log("⌨️ Entering login credentials...")
            
            # Use the working selector we found
            username_selector = working_selector or 'input[name="username"]'
            
            # Clear and enter username with better error handling
            username_field = await page.query_selector(username_selector)
            if username_field:
                await username_field.click()
                await username_field.fill('')  # Clear any existing text
                await self._human_type(page, username_selector, username)
                log(f"✅ Entered username: {username}")
            else:
                log("❌ Could not find username field with working selector")
                return False, totp_secret
            
            await self._human_delay(800, 1500)
            
            # Wait a bit longer for the page to fully load the password field
            await self._human_delay(1000, 2000)
            
            # Find and enter password with multiple selectors
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[aria-label="Password"]',
                'input[placeholder*="password"]',
                'input[placeholder*="Password"]',
                '#loginForm input[type="password"]',
                'form input[type="password"]',
                'input[autocomplete="current-password"]',
                'input[autocomplete="password"]'
            ]
            
            password_entered = False
            # Try multiple times with increasing waits
            for attempt in range(3):
                if password_entered:
                    break
                    
                for i, pass_selector in enumerate(password_selectors, 1):
                    try:
                        log(f"🎯 Trying password selector {i}/{len(password_selectors)} (attempt {attempt + 1}): {pass_selector}")
                        
                        # Wait for password field to appear
                        password_field = await page.wait_for_selector(pass_selector, state='visible', timeout=5000)
                        if password_field:
                            await password_field.click()
                            await self._human_delay(300, 600)  # Wait after click
                            await password_field.fill('')  # Clear any existing text
                            await self._human_type(page, pass_selector, password)
                            log("✅ Entered password")
                            password_entered = True
                            break
                    except Exception as e:
                        log(f"⚠️ Password selector {i} failed: {str(e)[:100]}")
                        continue
                
                if not password_entered and attempt < 2:
                    log(f"⏳ Password field not found on attempt {attempt + 1}, waiting longer...")
                    await self._human_delay(2000, 4000)
            
            if not password_entered:
                log("❌ Could not find password field after all attempts")
                
                # Debug: List all input fields on the page
                all_inputs = await page.query_selector_all('input')
                log(f"🔍 Found {len(all_inputs)} input fields on page for debugging:")
                for idx, input_elem in enumerate(all_inputs[:8]):  # Check first 8 inputs
                    try:
                        attrs = await input_elem.evaluate('el => ({name: el.name, placeholder: el.placeholder, type: el.type, ariaLabel: el.ariaLabel, id: el.id, visible: el.offsetParent !== null})')
                        log(f"Input {idx + 1}: {attrs}")
                    except:
                        pass
                        
                return False, totp_secret
            
            await self._human_delay(1000, 2000)
            
            # Find and click login button with multiple selectors
            log("🔍 Looking for login button...")
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Log In")',
                'div[role="button"]:has-text("Log in")',
                'div[role="button"]:has-text("Log In")',
                '//button[contains(text(), "Log")]'
            ]
            
            login_clicked = False
            for i, selector in enumerate(login_button_selectors, 1):
                try:
                    log(f"🎯 Trying login button selector {i}/{len(login_button_selectors)}")
                    login_button = await page.wait_for_selector(selector, timeout=5000)
                    if login_button and await login_button.is_visible():
                        await login_button.click()
                        log("✅ Successfully clicked login button")
                        login_clicked = True
                        break
                except Exception as e:
                    log(f"⚠️ Login selector {i} failed: {str(e)[:100]}")
                    continue
            
            if not login_clicked:
                log("❌ Could not find or click login button")
                return False, totp_secret
            
            log("🚀 Submitted login form")
            await self._human_delay(3000, 5000)
            
            # Handle post-login scenarios with improved error handling
            max_attempts = 5  # Increased attempts
            for attempt in range(max_attempts):
                try:
                    current_url = page.url
                    log(f"🔍 Current URL (attempt {attempt + 1}/{max_attempts}): {current_url}")
                    log(f"📄 Page title: {await page.title()}")
                    
                    # Check for account suspension first
                    if "suspended" in current_url.lower():
                        log("🚫 Account is suspended - cannot proceed")
                        return False, totp_secret
                    
                    # Check for Facebook redirect (blocking didn't work)
                    if "facebook.com" in current_url or "fb.com" in current_url:
                        log("⚠️ Facebook redirect detected - Instagram may be linking accounts")
                        log("🔄 Attempting to navigate back to Instagram...")
                        try:
                            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
                            await self._human_delay(3000, 5000)
                            current_url = page.url
                            log(f"🔍 After redirect fix, current URL: {current_url}")
                            if "facebook.com" in current_url:
                                log("❌ Persistent Facebook redirect - account may be linked to Facebook")
                                return False, totp_secret
                        except Exception as e:
                            log(f"❌ Failed to navigate back from Facebook: {e}")
                            return False, totp_secret
                    
                    # Check for various scenarios
                    log("🔍 Checking if login successful...")
                    if await self._is_logged_in(page):
                        log("✅ Login successful!")
                        return True, totp_secret
                    
                    log("🔍 Checking if 2FA required...")
                    if await self._is_2fa_required(page):
                        log("🔐 2FA verification required...")
                        if totp_secret:
                            success = await self._handle_2fa_verification(page, username, totp_secret, log)
                            if success:
                                log("✅ 2FA verification successful!")
                                return True, totp_secret
                            else:
                                log("❌ 2FA verification failed")
                                return False, totp_secret
                        else:
                            log("❌ 2FA required but no TOTP secret available")
                            return False, totp_secret
                    
                    log("🔍 Checking if checkpoint required...")
                    if await self._is_checkpoint_required(page):
                        log("🚫 Account checkpoint/challenge required")
                        return False, totp_secret
                    
                    log("🔍 Checking for login errors...")
                    if "login" in current_url and await self._has_login_error(page):
                        log("❌ Login failed - invalid credentials or account locked")
                        return False, totp_secret
                    
                    else:
                        log(f"⏳ Page still loading, waiting... (attempt {attempt + 1}/{max_attempts})")
                        await self._human_delay(3000, 5000)  # Longer wait
                
                except Exception as e:
                    log(f"⚠️ Error during login attempt {attempt + 1}: {e}")
                    if attempt == max_attempts - 1:
                        raise
                    await self._human_delay(2000, 4000)
            
            log("❌ Login failed after all attempts")
            return False, totp_secret
        
        except Exception as e:
            log(f"❌ Error during credential authentication: {e}", "ERROR")
            return False, ""
    
    async def _save_session_cookies(self, page: Page, username: str, proxy_info: Optional[Dict], log: callable) -> bool:
        """Save current session cookies"""
        try:
            # Get all cookies from the context
            cookies = await page.context.cookies()
            
            # Filter Instagram cookies
            instagram_cookies = [
                cookie for cookie in cookies 
                if 'instagram.com' in cookie.get('domain', '') or 
                   cookie.get('domain', '').endswith('.instagram.com')
            ]
            
            if not instagram_cookies:
                log("⚠️ No Instagram cookies found to save")
                return False
            
            # Save cookies with proxy info
            success = cookie_manager.save_cookies(username, instagram_cookies, proxy_info)
            
            if success:
                log(f"💾 Saved {len(instagram_cookies)} Instagram cookies")
                return True
            else:
                log("❌ Failed to save cookies")
                return False
                
        except Exception as e:
            log(f"❌ Error saving cookies: {e}", "ERROR")
            return False
    
    async def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in to Instagram"""
        try:
            # First, handle "Save login info" dialog if present
            await self._handle_save_login_info_dialog(page)
            
            # Look for indicators that we're logged in
            login_indicators = [
                "nav[aria-label='Primary navigation']",
                "[aria-label='Home']",
                "svg[aria-label='Home']",
                "a[href='/']",
                "[data-testid='home-icon']",
                "div[role='main'] nav"
            ]
            
            for indicator in login_indicators:
                element = await page.query_selector(indicator)
                if element:
                    # Additional check to make sure we're not on a login-related page
                    current_url = page.url
                    if not any(keyword in current_url.lower() for keyword in ['login', 'signup', 'accounts/emailsignup']):
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def _handle_save_login_info_dialog(self, page: Page):
        """Handle the 'Save login info' dialog by clicking 'Save info'"""
        try:
            # Wait a bit for dialog to appear
            await self._human_delay(1000, 2000)
            
            # Look for Save info button selectors
            save_info_selectors = [
                'button:has-text("Save Info")',
                'button:has-text("Save info")', 
                'button:has-text("Save")',
                'div[role="button"]:has-text("Save Info")',
                'div[role="button"]:has-text("Save info")',
                'div[role="button"]:has-text("Save")',
                'button._acan._acap._acas._aj1-._ap30',  # Instagram's CSS classes
                '//button[contains(text(), "Save")]'
            ]
            
            for selector in save_info_selectors:
                try:
                    save_button = await page.wait_for_selector(selector, timeout=2000)
                    if save_button and await save_button.is_visible():
                        await save_button.click()
                        await self._human_delay(2000, 3000)
                        return  # Successfully clicked, exit
                except:
                    continue
                    
        except Exception:
            # Dialog might not be present, which is fine
            pass
    
    async def _is_2fa_required(self, page: Page) -> bool:
        """Check if 2FA verification is required"""
        try:
            current_url = page.url.lower()
            
            # Check URL patterns
            if any(pattern in current_url for pattern in ['two_factor', '2fa', 'challenge']):
                return True
            
            # Check for 2FA form elements
            totp_selectors = [
                'input[name="verificationCode"]',
                'input[name="security_code"]',
                'input[aria-label*="security code"]',
                'input[placeholder*="security code"]',
                'input[placeholder*="verification code"]',
                'input[type="text"][maxlength="6"]'
            ]
            
            for selector in totp_selectors:
                if await page.query_selector(selector):
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _is_checkpoint_required(self, page: Page) -> bool:
        """Check if checkpoint/challenge is required"""
        try:
            current_url = page.url.lower()
            checkpoint_keywords = ['checkpoint', 'challenge', 'suspended', 'confirm']
            
            return any(keyword in current_url for keyword in checkpoint_keywords)
            
        except Exception:
            return False
    
    async def _has_login_error(self, page: Page) -> bool:
        """Check if there's a login error on the page"""
        try:
            error_selectors = [
                'div[id="slfErrorAlert"]',
                'div[role="alert"]',
                '[data-testid="login-error"]',
                'div:has-text("incorrect")',
                'div:has-text("doesn\'t match")',
                'p:has-text("incorrect")'
            ]
            
            for selector in error_selectors:
                if await page.query_selector(selector):
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _handle_2fa_verification(self, page: Page, username: str, totp_secret: str, log: callable) -> bool:
        """Handle 2FA verification using TOTP"""
        try:
            log("🔐 Handling 2FA verification...")
            
            # Generate TOTP code
            totp_code = await self._generate_totp_code(username, totp_secret, log)
            if not totp_code:
                return False
            
            await self._human_delay(1000, 2000)
            
            # Find 2FA input field with more comprehensive selectors
            totp_selectors = [
                'input[name="verificationCode"]',
                'input[name="security_code"]',
                'input[aria-label*="security code"]',
                'input[aria-label*="Security code"]',
                'input[aria-label*="verification code"]',
                'input[aria-label*="Verification code"]',
                'input[placeholder*="security code"]',
                'input[placeholder*="Security code"]',
                'input[placeholder*="verification code"]',
                'input[placeholder*="Verification code"]',
                'input[placeholder*="6-digit code"]',
                'input[placeholder*="Enter the 6-digit code"]',
                'input[type="text"][maxlength="6"]',
                'input[type="text"][pattern="[0-9]*"]',
                'input[autocomplete="one-time-code"]',
                'input[data-testid="confirmation-code-input"]',
                'form input[type="text"]:only-of-type',
                '#react-root input[type="text"]'
            ]
            
            totp_input = None
            for i, selector in enumerate(totp_selectors, 1):
                try:
                    log(f"🎯 Trying 2FA selector {i}/{len(totp_selectors)}: {selector}")
                    totp_input = await page.wait_for_selector(selector, timeout=8000)
                    if totp_input and await totp_input.is_visible():
                        log(f"📱 Found 2FA input field with selector {i}")
                        break
                    else:
                        totp_input = None
                except Exception as e:
                    log(f"⚠️ 2FA selector {i} failed: {str(e)[:80]}")
                    continue
            
            if not totp_input:
                log("❌ Could not find 2FA input field after trying all selectors")
                log(f"📍 Current URL: {page.url}")
                log(f"📄 Page title: {await page.title()}")
                
                # Debug: List all input fields on the page
                all_inputs = await page.query_selector_all('input')
                log(f"🔍 Found {len(all_inputs)} input fields on page for 2FA debugging:")
                for idx, input_elem in enumerate(all_inputs[:10]):  # Check first 10 inputs
                    try:
                        attrs = await input_elem.evaluate('el => ({name: el.name, placeholder: el.placeholder, type: el.type, ariaLabel: el.ariaLabel, id: el.id, visible: el.offsetParent !== null, maxLength: el.maxLength})')
                        log(f"Input {idx + 1}: {attrs}")
                    except:
                        pass
                
                return False
            
            # Enter TOTP code
            await totp_input.click()
            await page.keyboard.press('Control+a')
            await totp_input.fill(totp_code)
            log(f"✅ Entered TOTP code: {totp_code}")
            
            await self._human_delay(1500, 2500)
            
            # Submit 2FA form
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Confirm")',
                'button:has-text("Continue")',
                'button:has-text("Submit")',
                'button:has-text("Verify")'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    submit_button = await page.wait_for_selector(selector, timeout=3000)
                    if submit_button:
                        await submit_button.click()
                        log("🚀 Clicked 2FA submit button")
                        submitted = True
                        break
                except:
                    continue
            
            if not submitted:
                await page.keyboard.press('Enter')
                log("⌨️ Pressed Enter for 2FA verification")
            
            await self._human_delay(4000, 6000)
            
            # Check if 2FA was successful
            try:
                await page.wait_for_url(lambda url: "two_factor" not in url.lower(), timeout=15000)
                if await self._is_logged_in(page):
                    log("✅ 2FA verification successful!")
                    return True
                else:
                    log("❌ 2FA verification failed")
                    return False
            except:
                # Timeout - check current state
                if await self._is_logged_in(page):
                    log("✅ 2FA verification successful!")
                    return True
                else:
                    log("❌ 2FA verification failed")
                    return False
                    
        except Exception as e:
            log(f"❌ Error during 2FA verification: {e}", "ERROR")
            return False
    
    async def _generate_totp_code(self, username: str, totp_secret: str, log: callable) -> Optional[str]:
        """Generate TOTP code for 2FA authentication"""
        try:
            if not totp_secret:
                log("❌ No TOTP secret provided")
                return None
            
            # Clean the secret
            clean_secret = totp_secret.replace(' ', '').upper()
            
            # Validate secret
            if len(clean_secret) not in [16, 32]:
                log(f"❌ Invalid TOTP secret length: {len(clean_secret)}")
                return None
            
            if not re.match(r'^[A-Z2-7]+$', clean_secret):
                log("❌ Invalid TOTP secret format")
                return None
            
            # Generate TOTP code
            totp = pyotp.TOTP(clean_secret)
            code = totp.now()
            
            log(f"🔑 Generated TOTP code: {code}")
            return code
            
        except Exception as e:
            log(f"❌ Error generating TOTP code: {e}", "ERROR")
            return None
    
    async def _handle_initial_dialogs(self, page: Page, log: callable):
        """Handle cookie consent and other blocking dialogs"""
        try:
            # Handle cookie consent
            consent_selectors = [
                'button:has-text("Allow all cookies")',
                'button:has-text("Accept all")',
                'button:has-text("Accept")',
                'button:has-text("Allow All")',
                '[data-testid="cookie-accept"]',
                'button[aria-label="Allow all cookies"]'
            ]
            
            for selector in consent_selectors:
                try:
                    consent_button = await page.wait_for_selector(selector, timeout=3000)
                    if consent_button and await consent_button.is_visible():
                        await consent_button.click()
                        log("🍪 Accepted cookie consent")
                        await self._human_delay(2000, 3000)
                        break
                except:
                    continue
            
            # Handle age verification or other blocking dialogs
            blocking_dialogs = [
                'button:has-text("Continue")',
                'button:has-text("OK")',
                'button:has-text("Got it")',
                'button:has-text("Dismiss")',
                'button[aria-label="Close"]',
                '[data-testid="modal-close-button"]'
            ]
            
            for selector in blocking_dialogs:
                try:
                    dialog_button = await page.wait_for_selector(selector, timeout=2000)
                    if dialog_button and await dialog_button.is_visible():
                        await dialog_button.click()
                        log(f"✅ Dismissed blocking dialog: {selector}")
                        await self._human_delay(1000, 2000)
                        break
                except:
                    continue
                    
        except Exception as e:
            log(f"⚠️ Error handling initial dialogs: {e}")
            # Continue anyway as dialogs might not be present
    
    async def _dismiss_blocking_elements(self, page: Page, log: callable):
        """Dismiss various blocking elements that might prevent login form access"""
        try:
            # List of selectors for blocking elements
            blocking_selectors = [
                # Cookie banners
                'button:has-text("Allow all cookies")',
                'button:has-text("Accept all")',
                'button:has-text("Accept")',
                'button:has-text("Allow All")',
                '[data-testid="cookie-accept"]',
                'button[aria-label="Allow all cookies"]',
                
                # Age verification and other dialogs
                'button:has-text("Continue")',
                'button:has-text("OK")',
                'button:has-text("Got it")',
                'button:has-text("Dismiss")',
                'button:has-text("Not Now")',
                'button:has-text("Later")',
                'button[aria-label="Close"]',
                '[data-testid="modal-close-button"]',
                
                # Instagram specific blocking elements
                'button:has-text("Turn on Notifications")',
                'button:has-text("Not now")',
                'button[role="button"]:has-text("Not now")',
                
                # General modal closers
                '.modal button',
                '[role="dialog"] button',
                '.dialog button'
            ]
            
            dismissed_count = 0
            for selector in blocking_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        await element.click()
                        log(f"✅ Dismissed blocking element: {selector}")
                        dismissed_count += 1
                        await self._human_delay(1500, 2500)
                        
                        # Don't try to dismiss too many elements
                        if dismissed_count >= 3:
                            break
                except:
                    continue
            
            if dismissed_count > 0:
                log(f"✅ Dismissed {dismissed_count} blocking elements")
                await self._human_delay(2000, 3000)  # Wait for page to stabilize
            
        except Exception as e:
            log(f"⚠️ Error dismissing blocking elements: {e}")
            # Continue anyway as blocking elements might not be present
    
    async def _human_type(self, page: Page, selector: str, text: str):
        """Type text with human-like delays"""
        await page.type(selector, text, delay=random.uniform(50, 150))
    
    async def _human_delay(self, min_ms: int = 1000, max_ms: int = 3000):
        """Add human-like delay"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)
    
    def get_authentication_stats(self) -> Dict:
        """Get statistics about authentication attempts"""
        return {
            'total_attempts': len(self.login_attempts),
            'successful_logins': sum(1 for attempt in self.login_attempts.values() if attempt.get('success', False)),
            'active_sessions': len(self.session_info),
            'stored_accounts': len(cookie_manager.get_all_stored_accounts())
        }

# Global instance
enhanced_auth = EnhancedInstagramAuth()