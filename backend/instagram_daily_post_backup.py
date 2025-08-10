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
        
    def log(self, message, level="INFO"):
        """Log message using the callback with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        self.log_callback(formatted_message, level)

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

    async def load_cookies_for_account(self, context, username, proxy_info=None):
        """Load stored cookies for an account if they exist and are valid"""
        try:
            self.log(f"[{username}] 🍪 Checking for stored cookies...")
            
            # Check if cookies exist and are valid
            if not cookie_manager.are_cookies_valid(username):
                self.log(f"[{username}] ℹ️ No valid cookies found - will need to login normally")
                return False
            
            # Load cookies
            cookie_data = cookie_manager.load_cookies(username)
            if not cookie_data:
                self.log(f"[{username}] ❌ Failed to load cookie data")
                return False
            
            cookies = cookie_data.get('cookies', [])
            if not cookies:
                self.log(f"[{username}] ❌ No cookies in cookie data")
                return False
            
            # Verify proxy consistency if proxy is being used
            stored_proxy_info = cookie_data.get('proxy_info')
            if proxy_info and stored_proxy_info:
                if (proxy_info.get('host') != stored_proxy_info.get('host') or 
                    proxy_info.get('port') != stored_proxy_info.get('port')):
                    self.log(f"[{username}] ⚠️ Proxy mismatch detected - cookies may not work with different proxy")
                    self.log(f"[{username}] 🔄 Clearing cookies due to proxy change")
                    cookie_manager.delete_cookies(username)
                    return False
            
            # Add cookies to browser context
            await context.add_cookies(cookies)
            self.log(f"[{username}] ✅ Loaded {len(cookies)} cookies successfully")
            
            return True
            
        except Exception as e:
            self.log(f"[{username}] ❌ Error loading cookies: {e}", "ERROR")
            return False

    async def save_cookies_for_account(self, context, username, proxy_info=None):
        """Save cookies for an account after successful login"""
        try:
            self.log(f"[{username}] 💾 Saving cookies for future use...")
            
            # Get cookies from browser context
            cookies = await context.cookies()
            
            if not cookies:
                self.log(f"[{username}] ⚠️ No cookies to save")
                return False
            
            # Filter out expired cookies and keep only Instagram cookies
            valid_cookies = []
            for cookie in cookies:
                # Only save Instagram domain cookies
                if 'instagram.com' in cookie.get('domain', ''):
                    # Check if cookie is not expired
                    if 'expires' not in cookie or cookie['expires'] == -1 or cookie['expires'] > time.time():
                        valid_cookies.append(cookie)
            
            if not valid_cookies:
                self.log(f"[{username}] ⚠️ No valid Instagram cookies to save")
                return False
            
            # Save cookies using cookie manager
            success = cookie_manager.save_cookies(username, valid_cookies, proxy_info)
            
            if success:
                self.log(f"[{username}] ✅ Saved {len(valid_cookies)} cookies successfully")
                return True
            else:
                self.log(f"[{username}] ❌ Failed to save cookies")
                return False
                
        except Exception as e:
            self.log(f"[{username}] ❌ Error saving cookies: {e}", "ERROR")
            return False

    async def login_with_cookies(self, page, username, account_number):
        """Attempt to login using stored cookies"""
        try:
            self.log(f"[Account {account_number}] 🍪 Attempting cookie-based login for {username}...")
            await self.update_visual_status(page, "Logging in with cookies...", 2)
            
            # Navigate to Instagram home page
            await page.goto("https://www.instagram.com/", wait_until='domcontentloaded', timeout=30000)
            await self.human_delay(3000, 5000)
            
            # Check if we're logged in by looking for authenticated elements
            current_url = page.url
            self.log(f"[Account {account_number}] 🔍 Current URL after cookie login: {current_url}")
            
            # Check for login indicators
            authenticated_selectors = [
                'svg[aria-label="New post"]',  # Create post button
                'a[href*="/direct/"]',         # Messages link
                'svg[aria-label="Activity Feed"]', # Activity feed
                '[data-testid="user-avatar"]',     # User avatar
                'nav[aria-label="Primary navigation"]' # Main navigation
            ]
            
            is_authenticated = False
            for selector in authenticated_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        self.log(f"[Account {account_number}] ✅ Found authenticated element: {selector}")
                        is_authenticated = True
                        break
                except:
                    continue
            
            # Additional check: ensure we're not on login page
            if "/accounts/login/" in current_url:
                self.log(f"[Account {account_number}] ❌ Still on login page - cookies not working")
                is_authenticated = False
            
            # Check for any challenge/verification pages
            verification_indicators = ["challenge", "checkpoint", "verify", "suspicious"]
            if any(indicator in current_url.lower() for indicator in verification_indicators):
                self.log(f"[Account {account_number}] ⚠️ Account requires verification - cookies invalid")
                is_authenticated = False
            
            if is_authenticated:
                self.log(f"[Account {account_number}] ✅ Cookie-based login successful!")
                await self.update_visual_status(page, "Cookie login successful!", 3)
                return True
            else:
                self.log(f"[Account {account_number}] ❌ Cookie-based login failed - will try normal login")
                # Delete invalid cookies
                cookie_manager.delete_cookies(username)
                return False
                
        except Exception as e:
            self.log(f"[Account {account_number}] ❌ Error during cookie login: {e}", "ERROR")
            # Delete potentially corrupted cookies
            cookie_manager.delete_cookies(username)
            return False

    async def login_instagram_with_2fa(self, page, username, password, account_number):
        """Enhanced login with cookies management and automatic 2FA handling"""
        try:
            # Get account details including TOTP secret
            self.log(f"[Account {account_number}] 🔍 Looking up account details for {username}...")
            account_details = get_account_details(username)
            totp_secret = account_details.get('totp_secret') if account_details else None
            
            # Get proxy information for cookie consistency
            proxy_string = proxy_manager.get_account_proxy(username)
            proxy_info = None
            if proxy_string:
                proxy_info = proxy_manager.parse_proxy(proxy_string)
                self.log(f"[Account {account_number}] 🔗 Using proxy: {proxy_info['host']}:{proxy_info['port']}")
            
            if totp_secret:
                self.log(f"[Account {account_number}] 🔐 TOTP secret found - automatic 2FA enabled")
            else:
                self.log(f"[Account {account_number}] ℹ️ No TOTP secret found - manual 2FA may be required")
            
            # STEP 1: Try cookie-based login first
            self.log(f"[Account {account_number}] 🍪 Attempting cookie-based login...")
            if await self.login_with_cookies(page, username, account_number):
                self.log(f"[Account {account_number}] ✅ Cookie-based login successful - skipping credential login")
                return True
            
            # STEP 2: Cookie login failed, proceed with normal login
            self.log(f"[Account {account_number}] 🚀 Starting credential-based login process...")
            await self.update_visual_status(page, f"Logging in as {username}...", 2)
            
            # Navigate to login page with timeout handling
            try:
                self.log(f"[Account {account_number}] 🌐 Navigating to Instagram login page...")
                await page.goto("https://www.instagram.com/accounts/login/", 
                               wait_until='domcontentloaded', 
                               timeout=30000)
                self.log(f"[Account {account_number}] ✅ Login page loaded successfully")
                await self.human_delay(3000, 5000)
            except Exception as nav_error:
                self.log(f"[Account {account_number}] ❌ Failed to navigate to login page: {nav_error}", "ERROR")
                return False
            
            # Handle cookie consent with multiple attempts
            try:
                self.log(f"[Account {account_number}] 🍪 Checking for cookie consent...")
                cookie_selectors = [
                    'button:has-text("Allow all cookies")',
                    'button:has-text("Accept All")',
                    'button:has-text("Accept")',
                    '[data-testid="cookie-banner-accept"]',
                    'button[class*="sqdOP"]'
                ]
                
                for selector in cookie_selectors:
                    try:
                        cookie_button = await page.wait_for_selector(selector, timeout=3000)
                        if cookie_button:
                            await cookie_button.click()
                            self.log(f"[Account {account_number}] ✅ Cookie consent accepted")
                            await self.human_delay(1000, 2000)
                            break
                    except:
                        continue
                        
            except Exception as cookie_error:
                self.log(f"[Account {account_number}] ℹ️ No cookie consent found or already accepted")
            
            # Wait for and find login form with multiple selectors
            self.log(f"[Account {account_number}] 🔍 Looking for login form...")
            
            username_selectors = [
                'input[name="username"]',
                'input[aria-label="Phone number, username, or email"]',
                'input[placeholder*="username"]',
                'input[placeholder*="email"]',
                'input[type="text"][autocomplete="username"]',
                'input[data-testid="royal_email"]'
            ]
            
            username_input = None
            for i, selector in enumerate(username_selectors):
                try:
                    self.log(f"[Account {account_number}] 🎯 Trying username selector {i+1}: {selector}")
                    username_input = await page.wait_for_selector(selector, 
                                                                 state='visible', 
                                                                 timeout=10000)
                    if username_input:
                        self.log(f"[Account {account_number}] ✅ Username field found with selector {i+1}")
                        break
                except:
                    continue
            
            if not username_input:
                self.log(f"[Account {account_number}] ❌ Username field not found after trying all selectors", "ERROR")
                return False
            
            # Enter credentials
            self.log(f"[Account {account_number}] ⌨️ Entering login credentials...")
            await self.human_type(page, username_selectors[0], username)
            await self.human_delay(500, 1000)
            
            password_selectors = [
                'input[name="password"]',
                'input[aria-label="Password"]',
                'input[type="password"]',
                'input[data-testid="royal_pass"]'
            ]
            
            for selector in password_selectors:
                try:
                    await page.wait_for_selector(selector, state='visible', timeout=5000)
                    await self.human_type(page, selector, password)
                    break
                except:
                    continue
            
            await self.human_delay(1000, 2000)
            
            # Click login button
            login_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Log In")',
                'div[role="button"]:has-text("Log in")',
                'input[type="submit"]'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    login_button = await page.wait_for_selector(selector, timeout=5000)
                    if login_button:
                        await login_button.click()
                        self.log(f"[Account {account_number}] 🔑 Login button clicked")
                        login_clicked = True
                        break
                except:
                    continue
                    
            if not login_clicked:
                # Fallback to Enter key
                await page.keyboard.press('Enter')
                self.log(f"[Account {account_number}] ⌨️ Pressed Enter to submit login")
            
            await self.update_visual_status(page, "Processing login...", 3)
            await self.human_delay(5000, 7000)
            
            # Handle post-login scenarios
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    current_url = page.url
                    self.log(f"[Account {account_number}] 🔍 Current URL: {current_url}")
                    
                    # Success: Direct redirect to home page
                    if current_url == "https://www.instagram.com/" or current_url.startswith("https://www.instagram.com/?"):
                        self.log(f"[Account {account_number}] ✅ Login successful! Redirected to home page")
                        await self.update_visual_status(page, "Login successful!", 4)
                        # Save cookies after successful login
                        await self.save_cookies_for_account(page.context, username, proxy_info)
                        return True
                    
                    # Handle "Save your login info?" dialog
                    if "accounts/onetap" in current_url:
                        self.log(f"[Account {account_number}] 💾 Handling 'Save login info' dialog...")
                        await self.update_visual_status(page, "Handling save login dialog...", 4)
                        
                        if await self.handle_login_info_save_dialog(page, account_number):
                            await self.human_delay(2000, 3000)
                            final_url = page.url
                            if final_url == "https://www.instagram.com/" or final_url.startswith("https://www.instagram.com/?"):
                                self.log(f"[Account {account_number}] ✅ Successfully reached Instagram home page!")
                                await self.update_visual_status(page, "Login successful!", 5)
                                # Save cookies after successful login
                                await self.save_cookies_for_account(page.context, username, proxy_info)
                                return True
                    
                    # Handle 2FA verification
                    if await self.is_verification_required(page):
                        self.log(f"[Account {account_number}] 🔐 2FA verification required")
                        await self.update_visual_status(page, "2FA verification required...", 4)
                        
                        if totp_secret:
                            self.log(f"[Account {account_number}] 🤖 Attempting automatic 2FA with TOTP secret...")
                            await self.update_visual_status(page, "Entering 2FA code...", 5)
                            
                            if await self.handle_2fa_verification(page, f"Account {account_number}", totp_secret):
                                await self.human_delay(3000, 5000)
                                
                                # Check if we're now on home page
                                current_url = page.url
                                if current_url == "https://www.instagram.com/" or "accounts/onetap" in current_url:
                                    if "accounts/onetap" in current_url:
                                        await self.handle_login_info_save_dialog(page, account_number)
                                    
                                    self.log(f"[Account {account_number}] ✅ Login successful with automatic 2FA!")
                                    await self.update_visual_status(page, "2FA successful! Login complete!", 6)
                                    # Save cookies after successful login with 2FA
                                    await self.save_cookies_for_account(page.context, username, proxy_info)
                                    return True
                                else:
                                    self.log(f"[Account {account_number}] 🔄 2FA completed, checking page status...")
                                    continue
                            else:
                                self.log(f"[Account {account_number}] ❌ Automatic 2FA failed")
                                await self.update_visual_status(page, "2FA failed", 6)
                                return False
                        else:
                            self.log(f"[Account {account_number}] ⚠️ 2FA required but no TOTP secret provided", "ERROR")
                            self.log(f"[Account {account_number}] ❌ Cannot proceed without TOTP secret - account login failed", "ERROR")
                            await self.update_visual_status(page, "2FA failed - no TOTP secret", 6)
                            return False
                    
                    # Check for login errors
                    error_selectors = [
                        'p:has-text("Sorry, your password was incorrect")',
                        'p:has-text("The username you entered")',
                        'div:has-text("There was a problem logging you into Instagram")',
                        '[data-testid="login-error-message"]'
                    ]
                    
                    for error_selector in error_selectors:
                        if await page.query_selector(error_selector):
                            self.log(f"[Account {account_number}] ❌ Login error detected - invalid credentials", "ERROR")
                            await self.update_visual_status(page, "Login failed - invalid credentials", 4)
                            return False
                    
                    # If we're still on login page, there might be an issue
                    if "/accounts/login/" in current_url:
                        self.log(f"[Account {account_number}] ⚠️ Still on login page, attempt {attempt + 1}/{max_attempts}")
                        if attempt < max_attempts - 1:
                            await self.human_delay(2000, 4000)
                            continue
                        else:
                            self.log(f"[Account {account_number}] ❌ Login failed after {max_attempts} attempts", "ERROR")
                            await self.update_visual_status(page, "Login failed after multiple attempts", 4)
                            return False
                    
                    # Unknown page - wait and retry
                    self.log(f"[Account {account_number}] 🤔 Unexpected page state, retrying...")
                    await self.human_delay(3000, 5000)
                    
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ Exception during login attempt {attempt + 1}: {e}")
                    if attempt == max_attempts - 1:
                        raise
                    await self.human_delay(2000, 4000)
            
            self.log(f"[Account {account_number}] ❌ Login failed after all attempts", "ERROR")
            await self.update_visual_status(page, "Login failed", 4)
            return False

        except Exception as e:
            self.log(f"[Account {account_number}] ❌ Login error: {e}", "ERROR")
            await self.update_visual_status(page, "Login error", 4)
            return False
                    
                    # Handle "Save your login info?" dialog
                    if "accounts/onetap" in current_url:
                        self.log(f"[Account {account_number}] � Handling 'Save login info' dialog...")
                        await self.update_visual_status(page, "Handling save login dialog...", 4)
                        
                        if await self.handle_login_info_save_dialog(page, account_number):
                            await self.human_delay(2000, 3000)
                            final_url = page.url
                            if final_url == "https://www.instagram.com/" or final_url.startswith("https://www.instagram.com/?"):
                                self.log(f"[Account {account_number}] ✅ Successfully reached Instagram home page!")
                                await self.update_visual_status(page, "Login successful!", 5)
                                return True
                    
                    # Handle 2FA verification
                    if await self.is_verification_required(page):
                        self.log(f"[Account {account_number}] 🔐 2FA verification required")
                        await self.update_visual_status(page, "2FA verification required...", 4)
                        
                        if totp_secret:
                            self.log(f"[Account {account_number}] 🤖 Attempting automatic 2FA with TOTP secret...")
                            await self.update_visual_status(page, "Entering 2FA code...", 5)
                            
                            if await self.handle_2fa_verification(page, f"Account {account_number}", totp_secret):
                                await self.human_delay(3000, 5000)
                                
                                # Check if we're now on home page
                                current_url = page.url
                                if current_url == "https://www.instagram.com/" or "accounts/onetap" in current_url:
                                    if "accounts/onetap" in current_url:
                                        await self.handle_login_info_save_dialog(page, account_number)
                                    
                                    self.log(f"[Account {account_number}] ✅ Login successful with automatic 2FA!")
                                    await self.update_visual_status(page, "2FA successful! Login complete!", 6)
                                    return True
                                else:
                                    self.log(f"[Account {account_number}] 🔄 2FA completed, checking page status...")
                                    continue
                            else:
                                self.log(f"[Account {account_number}] ❌ Automatic 2FA failed")
                                await self.update_visual_status(page, "2FA failed", 6)
                                return False
                        else:
                            self.log(f"[Account {account_number}] ⚠️ 2FA required but no TOTP secret provided", "ERROR")
                            self.log(f"[Account {account_number}] ❌ Cannot proceed without TOTP secret - account login failed", "ERROR")
                            await self.update_visual_status(page, "2FA failed - no TOTP secret", 6)
                            return False
                    
                    # Check for login errors
                    error_selectors = [
                        'p:has-text("Sorry, your password was incorrect")',
                        'p:has-text("The username you entered")',
                        'div:has-text("There was a problem logging you into Instagram")',
                        '[data-testid="login-error-message"]'
                    ]
                    
                    for error_selector in error_selectors:
                        if await page.query_selector(error_selector):
                            self.log(f"[Account {account_number}] ❌ Login error detected - invalid credentials", "ERROR")
                            await self.update_visual_status(page, "Login failed - invalid credentials", 4)
                            return False
                    
                    # If we're still on login page, there might be an issue
                    if "/accounts/login/" in current_url:
                        self.log(f"[Account {account_number}] ⚠️ Still on login page, attempt {attempt + 1}/{max_attempts}")
                        if attempt < max_attempts - 1:
                            await self.human_delay(2000, 4000)
                            continue
                        else:
                            self.log(f"[Account {account_number}] ❌ Login failed after {max_attempts} attempts", "ERROR")
                            await self.update_visual_status(page, "Login failed after multiple attempts", 4)
                            return False
                    
                    # Unknown page - wait and retry
                    self.log(f"[Account {account_number}] 🤔 Unexpected page state, retrying...")
                    await self.human_delay(3000, 5000)
                    
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ Exception during login attempt {attempt + 1}: {e}")
                    if attempt == max_attempts - 1:
                        raise
                    await self.human_delay(2000, 4000)
            
            self.log(f"[Account {account_number}] ❌ Login failed after all attempts", "ERROR")
            await self.update_visual_status(page, "Login failed", 4)
            return False

        except Exception as e:
            self.log(f"[Account {account_number}] ❌ Login error: {e}", "ERROR")
            await self.update_visual_status(page, "Login error", 4)
            return False

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
        """Handle the 'Save your login info?' dialog by clicking 'Not now' - Enhanced version"""
        try:
            self.log(f"[Account {account_number}] 🔍 Checking for 'Save login info' dialog...")
            
            # Wait a moment for the dialog to fully load
            await self.human_delay(2000, 3000)
            
            # Check if we're on the save login info page
            current_url = page.url
            if "accounts/onetap" not in current_url:
                self.log(f"[Account {account_number}] ℹ️ Not on save login info page, current URL: {current_url}")
                return True  # Not an error, just not on that page
            
            self.log(f"[Account {account_number}] 🔧 On save login info page - looking for 'Save info' or 'Not now' button...")
            self.log(f"[Account {account_number}] 📊 Page title: {await page.title()}")
            
            # Strategy 1: Try selectors for both "Save info" and "Not now" buttons
            simple_selectors = [
                # Save info button (preferred action based on user requirement)
                'button.aswp._aswr._aswu._asw_._asx2:has-text("Save info")',
                'button:has-text("Save info")',
                ':text-is("Save info")',
                'text="Save info"',
                'button[type="button"]:has-text("Save info")',
                # Fallback to Not now if Save info not found
                ':text-is("Not now")',
                'text="Not now"',
                ':text-is("Not Now")',
                'text="Not Now"',
                'button:has-text("Not now")',
                'div[role="button"]:has-text("Not now")',
                '[role="button"]:has-text("Not now")',
                'button:has-text("Not")',
                'div:has-text("Not now")',
                '*:has-text("Not now")'
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
                                self.log(f"[Account {account_number}] ✅ Successfully dismissed save login dialog!")
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
                    # Try get_by_text approach with exact match
                    # Try both "Save info" and "Not now" with get_by_text
                    try:
                        save_info_locator = page.get_by_text("Save info", exact=True)
                        await save_info_locator.click(timeout=3000)
                        self.log(f"[Account {account_number}] ✅ Clicked 'Save info' button with get_by_text locator")
                    except:
                        not_now_locator = page.get_by_text("Not now", exact=True)
                        await not_now_locator.click(timeout=5000)
                        self.log(f"[Account {account_number}] ✅ Clicked 'Not now' button with get_by_text locator")
                    
                    await self.human_delay(3000, 4000)
                    new_url = page.url
                    if "accounts/onetap" not in new_url:
                        self.log(f"[Account {account_number}] ✅ Successfully dismissed save login dialog!")
                        return True
                        
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ get_by_text locator failed: {str(e)[:100]}")
                
                try:
                    # Try get_by_role approach - try Save info first, then Not now
                    try:
                        save_info_role = page.get_by_role("button", name=re.compile("save info", re.IGNORECASE))
                        await save_info_role.click(timeout=3000)
                        self.log(f"[Account {account_number}] ✅ Clicked 'Save info' button with get_by_role locator")
                    except:
                        not_now_role = page.get_by_role("button", name=re.compile("not now", re.IGNORECASE))
                        await not_now_role.click(timeout=5000)
                        self.log(f"[Account {account_number}] ✅ Clicked 'Not now' button with get_by_role locator")
                    
                    await self.human_delay(3000, 4000)
                    new_url = page.url
                    if "accounts/onetap" not in new_url:
                        self.log(f"[Account {account_number}] ✅ Successfully dismissed save login dialog!")
                        return True
                        
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ get_by_role locator failed: {str(e)[:100]}")
            
            # Strategy 3: Keyboard navigation fallbacks with timeout
            if time.time() - start_time <= max_duration:
                self.log(f"[Account {account_number}] 🔄 Trying keyboard navigation...")
                
                try:
                    # Try pressing Tab to focus the "Not now" button, then Enter
                    await page.keyboard.press('Tab')
                    await self.human_delay(500, 1000)
                    await page.keyboard.press('Tab')  # In case there are multiple buttons
                    await self.human_delay(500, 1000)
                    await page.keyboard.press('Enter')
                    await self.human_delay(2000, 3000)
                    
                    new_url = page.url
                    if "accounts/onetap" not in new_url:
                        self.log(f"[Account {account_number}] ✅ Keyboard navigation worked!")
                        return True
                        
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ Keyboard navigation failed: {e}")
            
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

    async def instagram_post_script(self, username, password, account_number, caption=""):
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
                
                # Configure browser launch args
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-gpu'
                ]
                
                # Full size for headless mode
                viewport_width = 1920
                viewport_height = 1080
                
                browser = None
                try:
                    # Try Chromium first (more reliable)
                    self.log(f"[Account {account_number}] 🔧 Attempting to launch Chromium browser...")
                    browser = await p.chromium.launch(
                        headless=False,  # Show browser for debugging
                        args=browser_args,
                        proxy=proxy_config,
                        slow_mo=100  # Small delay for visibility
                    )
                    self.log(f"[Account {account_number}] ✅ Chromium browser launched successfully")
                except Exception as chrome_error:
                    self.log(f"[Account {account_number}] ⚠️ Chromium launch failed: {chrome_error}")
                    
                    # Fallback to basic launch without extra features
                    try:
                        self.log(f"[Account {account_number}] 🔄 Attempting basic browser launch...")
                        browser = await p.chromium.launch(
                            headless=False,
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
                        viewport={'width': viewport_width, 'height': viewport_height}
                    )
                    self.log(f"[Account {account_number}] ✅ Browser context created successfully")
                    
                    # Load cookies for this account if they exist
                    proxy_info = proxy_manager.parse_proxy(proxy_string) if proxy_string else None
                    await self.load_cookies_for_account(context, username, proxy_info)
                    
                except Exception as e:
                    self.log(f"[Account {account_number}] ❌ Failed to create browser context: {e}", "ERROR")
                    await browser.close()
                    return False
                
                try:
                    page = await context.new_page()
                    self.log(f"[Account {account_number}] ✅ Browser page created successfully")
                except Exception as e:
                    self.log(f"[Account {account_number}] ❌ Failed to create browser page: {e}", "ERROR")
                    await browser.close()
                    return False
                
                # Set page title for headless mode
                await page.evaluate(f'''
                    document.title = "Account {account_number}: {username}";
                ''')

                try:
                    if self.should_stop():
                        self.log(f"[Account {account_number}] ⚠️ Stop flag detected, terminating script", "WARNING")
                        return
                        
                    # Simple direct login with 2FA support
                    self.log(f"[Account {account_number}] 🚀 Starting login process...")
                    login_success = await self.login_instagram_with_2fa(page, username, password, account_number)
                    
                    if not login_success:
                        self.log(f"[Account {account_number}] ❌ Login failed - terminating script for this account", "ERROR")
                        await self.update_visual_status(page, "❌ Login failed - terminating", 4)
                        return False

                    if self.should_stop():
                        self.log(f"[Account {account_number}] ⚠️ Stop flag detected after login, terminating script", "WARNING")
                        return

                    self.log(f"[Account {account_number}] ✅ Login successful! Current URL: {page.url}")
                    self.log(f"[Account {account_number}] 🔄 Proceeding to handle popups...")

                    # Handle popups
                    await self.handle_popups(page, account_number)

                    if self.should_stop():
                        self.log(f"[Account {account_number}] ⚠️ Stop flag detected after popup handling, terminating script", "WARNING")
                        return

                    self.log(f"[Account {account_number}] ✅ Popups handled! Current URL: {page.url}")

                    # Navigate to create post
                    self.log(f"[Account {account_number}] 📝 Looking for 'Create' button...")
                    self.log(f"[Account {account_number}] 📊 Page title: {await page.title()}")
                    await self.update_visual_status(page, "Looking for Create button...", 5)
                    await self.human_delay(2000, 4000)
                    
                    create_selectors = [
                        # Updated selector based on current Instagram structure
                        'div.x9f619.x3nfvp2.xr9ek0c.xjpr12u.xo237n4.x6pnmvc.x7nr27j.x12dmmrz.xz9dl7a.xpdmqnj.xsag5q8.x1g0dm76.x80pfx3.x159b3zp.x1dn74xm.xif99yt.x172qv1o.x4afuhf.x1lhsz42.x10v4vz6.xdoji71.x1dejxi8.x9k3k5o.x8st7rj.x11hdxyr.x1eunh74.x1wj20lx.x1obq294.x5a5i1n.xde0f50.x15x8krk',
                        # Direct SVG selector with New post aria-label
                        'svg[aria-label="New post"]',
                        # Container with New post SVG
                        'div:has(svg[aria-label="New post"])',
                        # Text-based selectors
                        'span:has-text("Create")',
                        'text="Create"',
                        ':text-is("Create")',
                        # Legacy selectors for fallback
                        'a[aria-label="New post"]',
                        'div[aria-label="New post"]',
                        'svg[aria-label="Create"]',
                        'a[href*="create"]'
                    ]
                    
                    clicked_create = False
                    for i, selector in enumerate(create_selectors):
                        if self.should_stop():
                            self.log(f"[Account {account_number}] ⚠️ Stop flag detected during create button search, terminating script", "WARNING")
                            return
                        try:
                            self.log(f"[Account {account_number}] 🎯 Trying create button selector {i+1}/{len(create_selectors)}: {selector[:50]}...")
                            await page.wait_for_selector(selector, state='visible', timeout=5000)
                            await page.click(selector)
                            self.log(f"[Account {account_number}] ✅ Successfully clicked create button with selector {i+1}")
                            clicked_create = True
                            break
                        except TimeoutError:
                            self.log(f"[Account {account_number}] ⚠️ Create button selector {i+1} timed out (not found)")
                            continue
                        except Exception as e:
                            self.log(f"[Account {account_number}] ❌ Create button selector {i+1} failed with error: {e}", "ERROR")
                            continue
                    
                    if not clicked_create:
                        self.log(f"[Account {account_number}] ❌ Could not find create button after trying all {len(create_selectors)} selectors", "ERROR")
                        self.log(f"[Account {account_number}] 📊 Current page URL: {page.url}")
                        self.log(f"[Account {account_number}] 📊 Page content preview: {(await page.content())[:500]}...")
                        await self.update_visual_status(page, "❌ Create button not found!", 5)
                        return False

                    self.log(f"[Account {account_number}] ✅ Create button clicked successfully!")
                    await self.update_visual_status(page, "✅ Opening create menu...", 6)
                    await self.human_delay(1000, 2000)

                    # Try to click Post option if available
                    self.log(f"[Account {account_number}] 📋 Looking for 'Post' option...")
                    post_selectors = [
                        'text="Post"',
                        'div[role="button"]:has-text("Post")',
                        'span:has-text("Post")',
                        'button:has-text("Post")'
                    ]
                    
                    post_clicked = False
                    for i, selector in enumerate(post_selectors):
                        if self.should_stop():
                            self.log(f"[Account {account_number}] ⚠️ Stop flag detected during post option search, terminating script", "WARNING")
                            return
                        try:
                            self.log(f"[Account {account_number}] 🎯 Trying post option selector {i+1}/{len(post_selectors)}: {selector}")
                            await page.wait_for_selector(selector, state='visible', timeout=3000)
                            await page.click(selector)
                            self.log(f"[Account {account_number}] ✅ Successfully clicked 'Post' option with selector {i+1}")
                            post_clicked = True
                            break
                        except TimeoutError:
                            self.log(f"[Account {account_number}] ⚠️ Post option selector {i+1} timed out (not found)")
                            continue
                        except Exception as e:
                            self.log(f"[Account {account_number}] ❌ Post option selector {i+1} failed with error: {e}", "ERROR")
                            continue

                    if not post_clicked:
                        self.log(f"[Account {account_number}] ℹ️ No separate 'Post' option found - continuing with upload")
                    else:
                        self.log(f"[Account {account_number}] ✅ Post option selected successfully!")

                    await self.human_delay(1000, 2000)

                    if self.should_stop():
                        self.log(f"[Account {account_number}] ⚠️ Stop flag detected before file upload, terminating script", "WARNING")
                        return

                    # Handle file upload
                    self.log(f"[Account {account_number}] 📁 Starting file upload process...")
                    success = await self.handle_file_upload(page, account_number)
                    if not success:
                        self.log(f"[Account {account_number}] ❌ File upload failed - terminating script", "ERROR")
                        return False

                    if self.should_stop():
                        self.log(f"[Account {account_number}] ⚠️ Stop flag detected after file upload, terminating script", "WARNING")
                        return

                    self.log(f"[Account {account_number}] ✅ File upload completed successfully!")

                    # Process the post
                    self.log(f"[Account {account_number}] 🔄 Starting post processing...")
                    success = await self.process_post(page, account_number, caption)
                    if not success:
                        self.log(f"[Account {account_number}] ❌ Post processing failed - terminating script", "ERROR")
                        return False

                    self.log(f"[Account {account_number}] 🎉 Post completed successfully!", "SUCCESS")
                    await self.update_visual_status(page, "✅ COMPLETED!", 5)
                    return True

                except Exception as e:
                    self.log(f"[Account {account_number}] ❌ Critical error during automation: {str(e)}", "ERROR")
                    self.log(f"[Account {account_number}] 📊 Error occurred at URL: {page.url if 'page' in locals() else 'N/A'}")
                    self.log(f"[Account {account_number}] 📊 Error type: {type(e).__name__}")
                    import traceback
                    self.log(f"[Account {account_number}] 📊 Full traceback: {traceback.format_exc()}", "ERROR")
                    await self.update_visual_status(page, f"❌ Error: {str(e)[:30]}...", 2)
                    return False
                finally:
                    self.log(f"[Account {account_number}] 🔄 Closing browser...")
                    try:
                        await browser.close()
                        self.log(f"[Account {account_number}] ✅ Browser closed successfully")
                    except Exception as e:
                        self.log(f"[Account {account_number}] ⚠️ Error closing browser: {e}", "WARNING")
                    
        except Exception as e:
            self.log(f"[Account {account_number}] Critical error: {e}", "ERROR")
            return False

    async def handle_popups(self, page, account_number):
        """Handle pop-ups with enhanced logging"""
        if self.should_stop():
            self.log(f"[Account {account_number}] ⚠️ Stop flag detected during popup handling", "WARNING")
            return
            
        self.log(f"[Account {account_number}] 🔄 Starting popup handling...")
        
        not_now_selectors = [
            'button:has-text("Not now")',
            'div[role="button"]:has-text("Not now")',
            'button:has-text("Not Now")',
            'div[role="button"]:has-text("Not Now")',
            '//button[contains(., "Not Now")]',
            '//button[contains(., "Not now")]'
        ]
        
        popups_dismissed = 0
        for attempt in range(3):  # Try up to 3 times
            if self.should_stop():
                self.log(f"[Account {account_number}] ⚠️ Stop flag detected during popup handling attempt {attempt + 1}", "WARNING")
                return
                
            self.log(f"[Account {account_number}] 🔍 Popup handling attempt {attempt + 1}/3...")
            dismissed_any = False
            
            for i, selector in enumerate(not_now_selectors):
                try:
                    self.log(f"[Account {account_number}] 🎯 Checking for popup with selector {i+1}/{len(not_now_selectors)}: {selector[:50]}...")
                    await page.wait_for_selector(selector, state='visible', timeout=3000)
                    await page.click(selector)
                    popups_dismissed += 1
                    self.log(f"[Account {account_number}] ✅ Dismissed popup #{popups_dismissed} with selector {i+1}")
                    await self.human_delay(1000, 2000)
                    dismissed_any = True
                    break
                except TimeoutError:
                    self.log(f"[Account {account_number}] ℹ️ No popup found with selector {i+1}")
                    continue
                except Exception as e:
                    self.log(f"[Account {account_number}] ⚠️ Error with popup selector {i+1}: {e}")
                    continue
                    
            if not dismissed_any:
                self.log(f"[Account {account_number}] ℹ️ No popups found in attempt {attempt + 1}")
                break
                
        self.log(f"[Account {account_number}] ✅ Popup handling completed! Total popups dismissed: {popups_dismissed}")
        self.log(f"[Account {account_number}] 📊 Current URL after popup handling: {page.url}")

    async def handle_file_upload(self, page, account_number):
        """Handle the media file upload process with enhanced logging."""
        if self.should_stop():
            self.log(f"[Account {account_number}] ⚠️ Stop flag detected during file upload", "WARNING")
            return False
            
        self.log(f"[Account {account_number}] 📁 Starting file upload process...")
        self.log(f"[Account {account_number}] 📊 File to upload: {os.path.basename(self.media_file)}")
        self.log(f"[Account {account_number}] 📊 File path: {self.media_file}")
        self.log(f"[Account {account_number}] 📊 File type: {'Video' if self.is_video else 'Image'}")
        self.log(f"[Account {account_number}] 📊 Current URL: {page.url}")
        await self.update_visual_status(page, "Uploading file...", 7)
        await self.human_delay(2000, 4000)
        
        upload_selectors = [
            'button._aswp._aswr._aswu._asw_._asx2[type="button"]:has-text("Select from computer")',
            'button:has-text("Select from computer")',
            'div[role="button"]:has-text("Select from computer")',
            'input[type="file"]',
            'button:has-text("Select from Computer")',
            '//button[contains(., "Select from computer")]',
            '//input[@type="file"]'
        ]
        
        upload_success = False
        
        for i, selector in enumerate(upload_selectors):
            if self.should_stop():
                self.log(f"[Account {account_number}] ⚠️ Stop flag detected during upload selector {i+1}", "WARNING")
                return False
            try:
                self.log(f"[Account {account_number}] 🎯 Trying upload selector {i+1}/{len(upload_selectors)}: {selector[:50]}...")
                
                if 'input[type="file"]' in selector or '//input[@type="file"]' in selector:
                    self.log(f"[Account {account_number}] 📝 Direct file input approach...")
                    file_input = await page.wait_for_selector(selector, state='attached', timeout=10000)
                    await file_input.set_input_files(self.media_file)
                    self.log(f"[Account {account_number}] ✅ File uploaded directly: {os.path.basename(self.media_file)}")
                    upload_success = True
                    break
                else:
                    self.log(f"[Account {account_number}] 📝 File chooser approach...")
                    await page.wait_for_selector(selector, state='visible', timeout=10000)
                    self.log(f"[Account {account_number}] ✅ Upload button found, waiting for file chooser...")
                    
                    async with page.expect_file_chooser(timeout=15000) as fc_info:
                        await page.click(selector)
                        self.log(f"[Account {account_number}] 🖱️ Clicked upload button")
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(self.media_file)
                        self.log(f"[Account {account_number}] ✅ File selected in chooser: {os.path.basename(self.media_file)}")
                        await self.update_visual_status(page, "✅ File uploaded!", 8)
                        upload_success = True
                        break
                        
            except TimeoutError:
                self.log(f"[Account {account_number}] ⚠️ Upload selector {i+1} timed out")
                continue
            except Exception as e:
                self.log(f"[Account {account_number}] ❌ Upload selector {i+1} failed with error: {e}", "ERROR")
                continue
        
        if not upload_success:
            self.log(f"[Account {account_number}] ❌ All upload methods failed after trying {len(upload_selectors)} selectors", "ERROR")
            self.log(f"[Account {account_number}] 📊 Current URL: {page.url}")
            self.log(f"[Account {account_number}] 📊 Page title: {await page.title()}")
            await self.update_visual_status(page, "❌ Upload failed!", 8)
            return False
            
        self.log(f"[Account {account_number}] ✅ File upload completed successfully!")
        self.log(f"[Account {account_number}] 📊 Current URL after upload: {page.url}")
        return True

    async def process_post(self, page, account_number, caption=""):
        """Navigate through post creation steps."""
        if self.should_stop():
            return False
            
        self.log(f"[Account {account_number}] 🔄 Starting post processing...")
        await self.update_visual_status(page, "Processing post...", 9)
        
        next_selectors = [
            'div.x1i10hfl.xjqpnuy.xc5r6h4.xqeqjp1.x1phubyo.xdl72j9.x2lah0s.xe8uvvx.xdj266r.x14z9mp.xat24cr.x1lziwak.x2lwn1j.xeuugli.x1hl2dhg.xggy1nq.x1ja2u2z.x1t137rt.x1q0g3np.x1a2a7pz.x6s0dn4.xjyslct.x1ejq31n.x18oe1m7.x1sy0etr.xstzfhl.x9f619.x1ypdohk.x1f6kntn.xl56j7k.x17ydfre.x2b8uid.xlyipyv.x87ps6o.x14atkfc.x5c86q.x18br7mf.x1i0vuye.xl0gqc1.xr5sc7.xlal1re.x14jxsvd.xt0b8zv.xjbqb8w.xr9e8f9.x1e4oeot.x1ui04y5.x6en5u8.x972fbf.x10w94by.x1qhh985.x14e42zd.xt0psk2.xt7dq6l.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x1n2onr6.x1n5bzlp[role="button"]:has-text("Next")',
            'button:has-text("Next")',
            'div[role="button"]:has-text("Next")',
            '//button[contains(., "Next")]'
        ]
        
        # First 'Next' button
        self.log(f"[Account {account_number}] 🔍 Looking for first 'Next' button...")
        await self.human_delay(3000, 5000)
        clicked_first_next = False
        for i, selector in enumerate(next_selectors):
            if self.should_stop():
                return False
            try:
                self.log(f"[Account {account_number}] Trying first Next button selector {i+1}: {selector}")
                await page.wait_for_selector(selector, state='visible', timeout=15000)
                await page.click(selector)
                self.log(f"[Account {account_number}] ✅ Clicked first 'Next' button with selector {i+1}")
                clicked_first_next = True
                break
            except TimeoutError:
                self.log(f"[Account {account_number}] First Next button selector {i+1} not found")
                continue
        
        if not clicked_first_next:
            self.log(f"[Account {account_number}] ❌ Could not find or click first 'Next' button", "ERROR")
            await self.update_visual_status(page, "❌ First Next button not found!", 9)
            return False

        # Second 'Next' button
        self.log(f"[Account {account_number}] 🔍 Looking for second 'Next' button...")
        await self.update_visual_status(page, "Moving to caption step...", 10)
        await self.human_delay(2000, 4000)
        
        clicked_second_next = False
        for i, selector in enumerate(next_selectors):
            if self.should_stop():
                return False
            try:
                self.log(f"[Account {account_number}] Trying second Next button selector {i+1}: {selector}")
                await page.wait_for_selector(selector, state='visible', timeout=15000)
                await page.click(selector)
                self.log(f"[Account {account_number}] ✅ Clicked second 'Next' button with selector {i+1}")
                clicked_second_next = True
                break
            except TimeoutError:
                self.log(f"[Account {account_number}] Second Next button selector {i+1} not found")
                continue

        if not clicked_second_next:
            self.log(f"[Account {account_number}] ⚠️ Could not find second 'Next' button, continuing anyway...")

        await self.human_delay(2000, 3000)

        # Add caption
        await self.add_caption(page, account_number, caption)

        # Click 'Share' button
        self.log(f"[Account {account_number}] 🚀 Looking for 'Share' button...")
        await self.update_visual_status(page, "Preparing to share...", 11)
        await self.human_delay(1000, 2000)
        
        share_selectors = [
            'div.x1i10hfl.xjqpnuy.xc5r6h4.xqeqjp1.x1phubyo.xdl72j9.x2lah0s.xe8uvvx.xdj266r.x14z9mp.xat24cr.x1lziwak.x2lwn1j.xeuugli.x1hl2dhg.xggy1nq.x1ja2u2z.x1t137rt.x1q0g3np.x1a2a7pz.x6s0dn4.xjyslct.x1ejq31n.x18oe1m7.x1sy0etr.xstzfhl.x9f619.x1ypdohk.x1f6kntn.xl56j7k.x17ydfre.x2b8uid.xlyipyv.x87ps6o.x14atkfc.x5c86q.x18br7mf.x1i0vuye.xl0gqc1.xr5sc7.xlal1re.x14jxsvd.xt0b8zv.xjbqb8w.xr9e8f9.x1e4oeot.x1ui04y5.x6en5u8.x972fbf.x10w94by.x1qhh985.x14e42zd.xt0psk2.xt7dq6l.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x1n2onr6.x1n5bzlp[role="button"]:has-text("Share")',
            'div.x1i10hfl[role="button"]:has-text("Share")',
            'div[class*="x1i10hfl"][role="button"]:has-text("Share")',
            'div[class*="xjqpnuy"][role="button"]:has-text("Share")',
            'button:has-text("Share")',
            'div[role="button"]:has-text("Share")',
            '[role="button"]:has-text("Share")',
            '//div[@role="button" and contains(text(), "Share")]',
            '//button[contains(text(), "Share")]',
            'text="Share"',
            ':text("Share")',
        ]
        
        clicked_share = False
        for i, selector in enumerate(share_selectors):
            if self.should_stop():
                return False
            try:
                self.log(f"[Account {account_number}] Trying Share button selector {i+1}: {selector}")
                element = await page.wait_for_selector(selector, state='visible', timeout=5000)
                if element:
                    element_text = await element.text_content()
                    if "Share" in element_text:
                        await element.click()
                        self.log(f"[Account {account_number}] ✅ Clicked 'Share' button - Upload in progress...")
                        await self.update_visual_status(page, "🚀 Sharing post...", 12)
                        clicked_share = True
                        break
            except TimeoutError:
                self.log(f"[Account {account_number}] Share button selector {i+1} not found")
                continue
            except Exception as e:
                self.log(f"[Account {account_number}] Share button selector {i+1} failed: {e}")
                continue

        if not clicked_share:
            self.log(f"[Account {account_number}] ❌ Could not find or click 'Share' button", "ERROR")
            await self.update_visual_status(page, "❌ Share button not found!", 12)
            return False

        # Wait for post completion
        self.log(f"[Account {account_number}] ⏳ Waiting for post completion...")
        await self.update_visual_status(page, "⏳ Waiting for completion...", 13)
        await self.human_delay(5000, 8000)
        try:
            await page.wait_for_selector('text="Your post has been shared."', timeout=30000)
            self.log(f"[Account {account_number}] ✅ Post shared successfully - confirmation message found!")
            await self.update_visual_status(page, "✅ Post shared successfully!", 14)
        except TimeoutError:
            try:
                await page.wait_for_url("https://www.instagram.com/", timeout=15000)
                self.log(f"[Account {account_number}] ✅ Post confirmed - redirected to home page")
                await self.update_visual_status(page, "✅ Post confirmed!", 14)
            except TimeoutError:
                self.log(f"[Account {account_number}] ⚠️ Post status unclear, but 'Share' was clicked - likely successful")
                await self.update_visual_status(page, "⚠️ Post likely successful", 14)
        
        return True

    async def add_caption(self, page, account_number, caption=""):
        """Add caption to the post."""
        if self.should_stop():
            return
            
        # Use provided caption or generate default one
        if not caption:
            media_type = "video" if self.is_video else "image"
            caption = f"Automated {media_type} post! 🤖✨ #automation #instagram #bot"
            self.log(f"[Account {account_number}] 📝 No caption provided, using default caption")
        else:
            self.log(f"[Account {account_number}] 📝 Adding custom caption: {caption[:100]}{'...' if len(caption) > 100 else ''}")
            
        await self.update_visual_status(page, "Adding caption...", 10)
        
        try:
            caption_selectors = [
                'div.xw2csxc.x1odjw0f.x1n2onr6.x1hnll1o.xpqswwc.xl565be.x5dp1im.xdj266r.x14z9mp.xat24cr.x1lziwak.x1w2wdq1.xen30ot.xf7dkkf.xv54qhq.xh8yej3.x5n08af.notranslate[aria-label="Write a caption..."][contenteditable="true"]',
                'textarea[aria-label="Write a caption..."]',
                'div[contenteditable="true"][aria-label*="caption"]',
                'textarea[placeholder*="caption"]',
                'div[aria-label="Write a caption..."]',
                'div[contenteditable="true"][aria-label="Write a caption..."]',
                'div[role="textbox"][aria-label="Write a caption..."]',
                'div[data-testid="caption"]',
                'textarea[placeholder="Write a caption..."]',
                'div[aria-label*="caption"]',
                'textarea[aria-label*="caption"]',
                'div[contenteditable="true"]',
                '//textarea[@aria-label="Write a caption..."]',
                '//div[@contenteditable="true" and contains(@aria-label, "caption")]'
            ]
            
            caption_added = False
            for i, selector in enumerate(caption_selectors):
                if self.should_stop():
                    return
                try:
                    self.log(f"[Account {account_number}] Trying caption field selector {i+1}: {selector}")
                    caption_field = await page.wait_for_selector(selector, state='visible', timeout=10000)
                    if caption_field:
                        await self.human_type(page, selector, caption, delay_range=(30, 100))
                        self.log(f"[Account {account_number}] ✅ Caption added successfully with selector {i+1}")
                        caption_added = True
                        break
                except TimeoutError:
                    self.log(f"[Account {account_number}] Caption field selector {i+1} not found")
                    continue
                except Exception as e:
                    self.log(f"[Account {account_number}] Caption field selector {i+1} error: {e}")
                    continue
            
            if not caption_added:
                self.log(f"[Account {account_number}] ⚠️ Could not find caption field, posting without caption")
            
        except Exception as e:
            self.log(f"[Account {account_number}] ❌ Caption addition failed: {e}", "ERROR")

    async def run_automation(self, accounts_file, media_file, concurrent_accounts=5, caption="", auto_generate_caption=True):
        """Run Instagram posting for multiple accounts concurrently."""
        self.log("Starting Multi-Account Instagram Automation.")
        self.log("=" * 50)
        
        # Set media file
        self.set_media_file(media_file)
        
        # Load credentials
        accounts = self.load_accounts_from_file(accounts_file)
        if not accounts:
            self.log("No valid accounts found. Please check your accounts file.", "ERROR")
            return False
        
        # Limit concurrent accounts
        accounts_to_process = accounts[:concurrent_accounts]
        self.log(f"Processing {len(accounts_to_process)} account(s) concurrently.")
        self.log("=" * 50)
        
        # Create semaphore to limit concurrent browsers
        semaphore = asyncio.Semaphore(min(concurrent_accounts, 5))  # Max 5 concurrent browsers
        
        async def process_account_with_semaphore(username, password, account_num):
            async with semaphore:
                if self.should_stop():
                    self.log(f"[Account {account_num}] ⚠️ Stop flag detected before processing - skipping account", "WARNING")
                    return False
                    
                self.log(f"[Account {account_num}] 🚀 Starting processing for {username}...")
                try:
                    result = await self.instagram_post_script(username, password, account_num, caption)
                    if result is None:
                        self.log(f"[Account {account_num}] ⚠️ Script returned None - likely stopped early", "WARNING")
                        return False
                    elif result:
                        self.log(f"[Account {account_num}] ✅ Processing completed successfully!", "SUCCESS")
                        return True
                    else:
                        self.log(f"[Account {account_num}] ❌ Processing failed", "ERROR")
                        return False
                except Exception as e:
                    self.log(f"[Account {account_num}] ❌ Exception during processing: {e}", "ERROR")
                    return False
        
        # Create tasks for each account
        tasks = []
        for i, (username, password) in enumerate(accounts_to_process, 1):
            if self.should_stop():
                break
            self.log(f"Creating task for Account {i}: {username}.")
            task = asyncio.create_task(process_account_with_semaphore(username, password, i))
            tasks.append(task)
        
        if not tasks:
            self.log("No tasks created", "ERROR")
            return False
        
        self.log(f"Created {len(tasks)} tasks. Starting execution...")
        
        # Run all tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Summary
            self.log("\nResults Summary:")
            successful_count = 0
            for i, result in enumerate(results, 1):
                if isinstance(result, Exception):
                    self.log(f"Account {i}: Failed with error: {result}", "ERROR")
                elif result:
                    self.log(f"Account {i}: Completed successfully.", "SUCCESS")
                    successful_count += 1
                else:
                    self.log(f"Account {i}: Failed", "ERROR")
            
            self.log("=" * 50)
            if successful_count == len(results):
                self.log(f"🎉 All accounts completed successfully! {successful_count}/{len(results)} accounts processed.", "SUCCESS")
            elif successful_count > 0:
                self.log(f"⚠️ Partial success: {successful_count}/{len(results)} accounts completed successfully.", "WARNING") 
            else:
                self.log(f"❌ No accounts completed successfully. {len(results)} accounts failed.", "ERROR")
            
            self.log(f"Automation finished! {successful_count}/{len(results)} accounts processed successfully.")
            return successful_count > 0
                    
        except Exception as e:
            self.log(f"Error in concurrent execution: {e}", "ERROR")
            return False

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
