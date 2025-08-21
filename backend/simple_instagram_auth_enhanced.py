"""
Enhanced Simple Instagram Authentication
Streamlined approach with human-like typing and behavior
"""

import asyncio
import random
from typing import Tuple, Dict, Optional
from playwright.async_api import Page, BrowserContext
from datetime import datetime
import json
import os
import pyotp

class HumanLikeTyping:
    """Human-like typing behavior simulation"""
    
    @staticmethod
    async def human_type(page, selector: str, text: str, log_callback=None):
        """Type text with human-like delays and occasional mistakes"""
        try:
            # Clear the field first
            await page.fill(selector, '')
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Type character by character with human-like timing
            for i, char in enumerate(text):
                # Human typing speed varies (50-200ms per character)
                delay = random.uniform(0.05, 0.2)
                
                # Occasionally pause longer (like thinking)
                if random.random() < 0.1:  # 10% chance
                    delay += random.uniform(0.3, 0.8)
                
                # Sometimes make a typo and correct it
                if random.random() < 0.02 and i > 0:  # 2% chance of typo
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    await page.type(selector, wrong_char, delay=delay * 1000)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    # Backspace to correct
                    await page.keyboard.press('Backspace')
                    await asyncio.sleep(random.uniform(0.1, 0.2))
                
                # Type the correct character
                await page.type(selector, char, delay=delay * 1000)
            
            # Final pause after typing
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Human typing failed: {str(e)}")
            # Fallback to normal fill
            await page.fill(selector, text)
    
    @staticmethod
    async def human_click(page, selector: str, log_callback=None):
        """Click with human-like behavior"""
        try:
            # Wait a moment before clicking (human hesitation)
            await asyncio.sleep(random.uniform(0.2, 0.6))
            
            # Sometimes hover before clicking
            if random.random() < 0.3:  # 30% chance
                await page.hover(selector)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            await page.click(selector)
            
            # Pause after clicking
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Human click failed: {str(e)}")
            # Fallback to normal click
            await page.click(selector)
    
    @staticmethod
    async def human_scroll(page, direction='down', distance=None, log_callback=None):
        """Scroll with human-like behavior"""
        try:
            if distance is None:
                distance = random.randint(300, 800)
            
            if direction == 'down':
                await page.mouse.wheel(0, distance)
            else:
                await page.mouse.wheel(0, -distance)
            
            # Human-like pause after scrolling
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Human scroll failed: {str(e)}")

class EnhancedSimpleAuth:
    """Enhanced simple Instagram authentication with human-like behavior"""
    
    def __init__(self):
        self.session_dir = 'instagram_sessions_simple'
        os.makedirs(self.session_dir, exist_ok=True)
        self.typing = HumanLikeTyping()
    
    def default_log(self, message: str):
        """Default logging function"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [INFO] {message}")
    
    async def authenticate_with_human_behavior(
        self, 
        context: BrowserContext, 
        username: str, 
        password: str, 
        totp_secret: Optional[str] = None,
        proxy_info: Optional[Dict] = None,
        log_callback: callable = None
    ) -> Tuple[bool, Dict]:
        """
        Authenticate with human-like behavior - typing, clicking, scrolling
        """
        log = log_callback or self.default_log
        log(f"🔐 Starting enhanced authentication for {username}")
        
        try:
            # Get or create page
            page = context.pages[0] if context.pages else await context.new_page()
            log(f"📄 Using browser page")
            
            if proxy_info:
                log(f"📡 Using proxy: {proxy_info.get('host', 'Unknown')}:{proxy_info.get('port', 'Unknown')}")
            
            # Human-like navigation to Instagram
            log(f"🌐 Navigating to Instagram login page...")
            
            # Sometimes go to homepage first (like a human)
            if random.random() < 0.3:  # 30% chance
                await page.goto("https://www.instagram.com/", wait_until="networkidle", timeout=30000)
                await asyncio.sleep(random.uniform(1, 3))
                # Then navigate to login
                await page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle", timeout=30000)
            else:
                # Go directly to login
                await page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle", timeout=30000)
            
            log(f"✅ Successfully loaded Instagram login page")
            
            # Human-like pause to "read" the page
            await asyncio.sleep(random.uniform(2, 4))
            
            # Check current URL
            current_url = page.url
            log(f"📍 Current page URL: {current_url}")
            
            if "instagram.com" not in current_url:
                log(f"❌ Not on Instagram page. Current URL: {current_url}")
                return False, {"error": f"Wrong page: {current_url}"}
            
            # Human-like form interaction
            log(f"🔍 Looking for login form...")
            
            try:
                # Wait for username field with human-like patience
                await page.wait_for_selector('input[name="username"]', timeout=15000)
                log(f"✅ Found username field")
                
                # Human-like typing for username
                log(f"✏️ Typing username with human-like behavior...")
                await self.typing.human_type(page, 'input[name="username"]', username, log)
                log(f"✅ Username entered")
                
                # Human pause before password
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Human-like typing for password
                log(f"✏️ Typing password with human-like behavior...")
                await self.typing.human_type(page, 'input[name="password"]', password, log)
                log(f"✅ Password entered")
                
                # Human hesitation before clicking login
                await asyncio.sleep(random.uniform(1, 2))
                
                # Human-like login button click
                log(f"🖱️ Clicking login button with human-like behavior...")
                await self.typing.human_click(page, 'button[type="submit"]', log)
                log(f"✅ Login button clicked")
                
                # Wait for response with human-like patience
                log(f"⏳ Waiting for login response...")
                await asyncio.sleep(random.uniform(3, 6))
                
                # Check result
                final_url = page.url
                log(f"📍 Final URL after login: {final_url}")
                
                # Handle different scenarios
                if "two_factor" in final_url:
                    log(f"🔐 Two-factor authentication required")
                    
                    if totp_secret:
                        log(f"🔑 Handling 2FA with human-like behavior...")
                        success = await self._handle_2fa_human_like(page, totp_secret, log)
                        
                        if success:
                            final_url_after_2fa = page.url
                            log(f"✅ 2FA successful! Final URL: {final_url_after_2fa}")
                            
                            # Save session
                            await self._save_session(page, username, log)
                            
                            return True, {
                                'method': 'enhanced_simple_with_2fa',
                                'proxy': proxy_info,
                                'username': username,
                                'final_url': final_url_after_2fa,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            return False, {"error": "2FA verification failed"}
                    else:
                        return False, {"error": "2FA required but no TOTP secret provided"}
                
                elif "/accounts/login" not in final_url and "instagram.com" in final_url:
                    log(f"✅ Login successful without 2FA! Redirected to: {final_url}")
                    
                    # Save session
                    await self._save_session(page, username, log)
                    
                    return True, {
                        'method': 'enhanced_simple_login',
                        'proxy': proxy_info,
                        'username': username,
                        'final_url': final_url,
                        'timestamp': datetime.now().isoformat()
                    }
                
                elif "suspended" in final_url:
                    log(f"⚠️ Account appears to be suspended: {final_url}")
                    return True, {
                        'method': 'enhanced_simple_login',
                        'proxy': proxy_info,
                        'username': username,
                        'final_url': final_url,
                        'status': 'suspended',
                        'timestamp': datetime.now().isoformat()
                    }
                
                else:
                    # Check for error messages
                    try:
                        error_element = await page.query_selector('[role="alert"], .error, #slfErrorAlert')
                        if error_element:
                            error_text = await error_element.text_content()
                            log(f"❌ Login error: {error_text}")
                            return False, {"error": f"Login error: {error_text}"}
                    except:
                        pass
                    
                    log(f"❌ Login failed - unexpected result")
                    return False, {"error": f"Login failed - unexpected URL: {final_url}"}
                    
            except Exception as e:
                log(f"❌ Login form interaction failed: {str(e)}")
                return False, {"error": f"Form interaction failed: {str(e)}"}
                
        except Exception as e:
            log(f"❌ Authentication failed: {str(e)}")
            return False, {"error": f"Authentication failed: {str(e)}"}
    
    async def _handle_2fa_human_like(self, page: Page, totp_secret: str, log: callable) -> bool:
        """Handle 2FA with human-like behavior and improved button detection"""
        try:
            # Clean and generate TOTP code
            clean_secret = totp_secret.replace(' ', '').upper()
            totp = pyotp.TOTP(clean_secret)
            code = totp.now()
            log(f"🔢 Generated 2FA code: {code}")
            
            # Human-like pause to "think"
            await asyncio.sleep(random.uniform(1, 3))
            
            # Find 2FA input with multiple selectors
            selectors = [
                'input[name="verificationCode"]',
                'input[aria-label="Security code"]',
                'input[placeholder*="code"]',
                'input[type="text"]',
                'input[maxlength="6"]'
            ]
            
            input_found = False
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    log(f"✅ Found 2FA input field")
                    
                    # Human-like typing of 2FA code
                    log(f"✏️ Typing 2FA code with human-like behavior...")
                    await self.typing.human_type(page, selector, code, log)
                    log(f"✅ 2FA code entered")
                    
                    input_found = True
                    break
                except:
                    continue
            
            if not input_found:
                log(f"❌ Could not find 2FA input field")
                return False
            
            # Human hesitation before submitting
            await asyncio.sleep(random.uniform(1, 2))
            
            # Find and click submit button with improved detection
            button_selectors = [
                'button[type="submit"]',
                'button:has-text("Confirm")',
                'button:has-text("Submit")', 
                'button:has-text("Continue")',
                'div[role="button"]:has-text("Confirm")',
                'div[role="button"]:has-text("Submit")',
                '[data-testid="confirmButton"]',
                'button._acan._acap._acas._aj1-._ap30',
                'div._acan._acap._acas._aj1-._ap30[role="button"]'
            ]
            
            button_clicked = False
            for selector in button_selectors:
                try:
                    # Check if button exists and is clickable
                    button = await page.query_selector(selector)
                    if button:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        
                        if is_visible and is_enabled:
                            await page.click(selector, timeout=10000)
                            log(f"🖱️ Clicked 2FA submit button with selector: {selector}")
                            button_clicked = True
                            break
                except Exception as e:
                    log(f"⚠️ Button selector {selector} failed: {str(e)}")
                    continue
            
            # If no button found, try pressing Enter as fallback
            if not button_clicked:
                log(f"📝 No submit button found, trying Enter key...")
                await page.keyboard.press("Enter")
                log(f"⌨️ Pressed Enter key for 2FA submission")
            
            # Wait for verification with human-like patience
            log(f"⏳ Waiting for 2FA verification...")
            await asyncio.sleep(random.uniform(5, 8))
            
            # Check result
            final_url = page.url
            log(f"📍 Final URL after 2FA: {final_url}")
            
            if "two_factor" not in final_url and "instagram.com" in final_url:
                log(f"✅ 2FA verification successful!")
                return True
            else:
                log(f"❌ 2FA verification failed")
                return False
                
        except Exception as e:
            log(f"❌ 2FA handling failed: {str(e)}")
            return False
    
    async def _save_session(self, page: Page, username: str, log: callable):
        """Save session cookies"""
        try:
            cookies = await page.context.cookies()
            session_file = os.path.join(self.session_dir, f"{username}_enhanced_session.json")
            
            session_data = {
                'cookies': cookies,
                'timestamp': datetime.now().isoformat(),
                'url': page.url,
                'user_agent': await page.evaluate('navigator.userAgent')
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            log(f"💾 Saved enhanced session data for {username}")
            
        except Exception as e:
            log(f"⚠️ Could not save session: {str(e)}")

# Global instance
enhanced_simple_auth = EnhancedSimpleAuth()
