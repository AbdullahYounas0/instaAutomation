import asyncio
import pandas as pd
from playwright.async_api import async_playwright, Playwright, BrowserContext
import random
import time
import logging
import os
import pyotp
import re
from instagram_accounts import get_account_details
from proxy_manager import proxy_manager
from enhanced_instagram_auth import enhanced_auth
from instagram_cookie_manager import cookie_manager

# Default Configuration
DEFAULT_WARMUP_DURATION_MINUTES = 300
DEFAULT_SCROLL_PAUSE_SECONDS = 2
DEFAULT_ACTIVITY_DELAY_SECONDS = (3, 7)
DEFAULT_SCROLL_ATTEMPTS = (5, 10)
DEFAULT_MAX_CONCURRENT_BROWSERS = 10

async def human_like_delay(delay_range=DEFAULT_ACTIVITY_DELAY_SECONDS, stop_callback=None):
    """Introduces a human-like delay between actions with stop signal checking."""
    delay_seconds = random.uniform(*delay_range)
    
    # If delay is short, just sleep normally
    if delay_seconds <= 1:
        await asyncio.sleep(delay_seconds)
        return
    
    # For longer delays, check stop signal periodically
    elapsed = 0
    check_interval = 0.5  # Check every 500ms
    
    while elapsed < delay_seconds:
        if stop_callback and stop_callback():
            return  # Exit immediately if stop requested
        
        sleep_time = min(check_interval, delay_seconds - elapsed)
        await asyncio.sleep(sleep_time)
        elapsed += sleep_time

async def generate_totp_code(username, totp_secret):
    """Generate TOTP code for 2FA authentication"""
    try:
        if not totp_secret:
            logging.info(f"[{username}] No TOTP secret provided")
            return None
            
        # Clean the secret (remove spaces and convert to uppercase)
        clean_secret = totp_secret.replace(' ', '').upper()
        
        # Validate secret length (16 or 32 characters for base32)
        if len(clean_secret) not in [16, 32]:
            logging.error(f"[{username}] Invalid TOTP secret length: {len(clean_secret)} (must be 16 or 32 characters)")
            return None
            
        # Validate base32 format
        if not re.match(r'^[A-Z2-7]+$', clean_secret):
            logging.error(f"[{username}] Invalid TOTP secret format (must be base32)")
            return None
        
        # Generate TOTP code
        totp = pyotp.TOTP(clean_secret)
        code = totp.now()
        
        logging.info(f"[{username}] Generated TOTP code: {code} (secret length: {len(clean_secret)})")
        return code
        
    except Exception as e:
        logging.error(f"[{username}] Error generating TOTP code: {e}")
        return None

async def handle_2fa_verification(page, username, totp_secret, log_callback=None):
    """Handle Instagram 2FA verification using TOTP."""
    try:
        if log_callback:
            log_callback(f"[{username}] 🔐 2FA verification required...")
        
        # Generate TOTP code
        totp_code = await generate_totp_code(username, totp_secret)
        if not totp_code:
            if log_callback:
                log_callback(f"[{username}] ❌ Could not generate TOTP code.")
            return False
        
        await human_like_delay((1, 2))

        # Look for 2FA input field
        totp_selectors = [
            'input[name="verificationCode"]',
            'input[name="security_code"]',
            'input[aria-label*="security code"]',
            'input[placeholder*="security code"]',
            'input[placeholder*="verification code"]',
            '[data-testid="2fa-input"]',
            'input[type="text"][maxlength="6"]',
            'input[autocomplete="one-time-code"]'
        ]
        
        totp_input = None
        for selector in totp_selectors:
            try:
                totp_input = await page.wait_for_selector(selector, timeout=5000)
                if totp_input:
                    if log_callback:
                        log_callback(f"[{username}] 📱 Found 2FA input field with selector: {selector}")
                    break
            except:
                continue
        
        if not totp_input:
            if log_callback:
                log_callback(f"[{username}] ❌ Could not find 2FA input field.")
            return False
        
        # Enter TOTP code
        await totp_input.click()
        await page.keyboard.press('Control+a')
        await totp_input.fill(totp_code)
        
        if log_callback:
            log_callback(f"[{username}] ✅ Entered TOTP code: {totp_code}")
        
        await human_like_delay((1.5, 2.5))
        
        # Look for submit button
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Confirm")',
            'button:has-text("Continue")',
            'button:has-text("Submit")',
            'button:has-text("Verify")',
            '[role="button"]:has-text("Confirm")',
            '[role="button"]:has-text("Continue")',
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
            if log_callback:
                log_callback(f"[{username}] 🚀 Clicked submit button for 2FA verification")
        else:
            await page.keyboard.press('Enter')
            if log_callback:
                log_callback(f"[{username}] ⌨️ Pressed Enter for 2FA verification")
        
        await human_like_delay((4, 6)) # Increased delay
        
        # More robust check for verification success
        try:
            # Wait for navigation away from the 2FA page.
            await page.wait_for_url(lambda url: "two_factor" not in url, timeout=15000)
            if log_callback:
                log_callback(f"[{username}] ✅ Navigated away from 2FA page. URL is now: {page.url}")
            
            # Check if we are on a page that indicates successful login
            if "instagram.com" in page.url and not await is_verification_required(page):
                 if log_callback:
                    log_callback(f"[{username}] ✅ 2FA verification successful!")
                 return True
            else:
                if log_callback:
                    log_callback(f"[{username}] ❌ 2FA verification failed after navigation.")
                return False
        except Exception:
             # If navigation times out, check if we are still on a verification page
            if not await is_verification_required(page):
                if log_callback:
                    log_callback(f"[{username}] ✅ 2FA verification successful (no longer on verification page).")
                return True
            else:
                if log_callback:
                    log_callback(f"[{username}] ❌ 2FA verification failed (still on verification page).")
                return False
            
    except Exception as e:
        if log_callback:
            log_callback(f"[{username}] ❌ Error during 2FA verification: {e}")
        return False

async def human_like_typing(page, selector, text):
    """Types text into a field with a human-like delay between characters."""
    await page.type(selector, text, delay=random.uniform(50, 150))

async def human_like_scroll(page):
    """Performs a human-like scroll action on the page."""
    scroll_amount = random.randint(300, 800)
    scroll_duration = random.uniform(0.5, 1.5)
    steps = random.randint(5, 15)
    step_amount = scroll_amount / steps
    step_delay = scroll_duration / steps

    for _ in range(steps):
        await page.evaluate(f"window.scrollBy(0, {step_amount})")
        await asyncio.sleep(step_delay)
    await asyncio.sleep(random.uniform(0.5, 1.5))

async def is_verification_required(page):
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

async def handle_login_info_save_dialog(page, username, log_callback=None):
    """Handle the 'Save your login info?' dialog by clicking 'Not now'"""
    try:
        if log_callback:
            log_callback(f"{username}: Looking for 'Not now' button on save login info dialog...")
        
        # Multiple selectors to find the "Not now" button
        not_now_selectors = [
            'button:has-text("Not now")',
            'div[role="button"]:has-text("Not now")',
            'button:has-text("Not Now")',
            'div[role="button"]:has-text("Not Now")',
            '//button[contains(text(), "Not now")]',
            '//button[contains(text(), "Not Now")]',
            '[role="button"]:has-text("Not now")',
            '[role="button"]:has-text("Not Now")'
        ]
        
        for selector in not_now_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=3000)
                if element:
                    await element.click()
                    if log_callback:
                        log_callback(f"{username}: ✅ Clicked 'Not now' on save login info dialog")
                    await human_like_delay()
                    return True
            except:
                continue
        
        if log_callback:
            log_callback(f"{username}: ⚠️ Could not find 'Not now' button, continuing...")
        return False
        
    except Exception as e:
        if log_callback:
            log_callback(f"{username}: Error handling save login dialog: {e}")
        return False

async def login_instagram_with_cookies_and_2fa(context: BrowserContext, username, password, totp_secret=None, log_callback=None):
    """
    Enhanced login function with cookie management and automatic 2FA handling
    """
    try:
        if log_callback:
            log_callback(f"[{username}] � Starting enhanced authentication...")
        
        # Create a log callback for the authentication system
        def auth_log_callback(message):
            if log_callback:
                log_callback(f"[{username}] {message}")
        
        # Use enhanced authentication with cookies and proxy
        success, auth_info = await enhanced_auth.authenticate_with_cookies_and_proxy(
            context=context,
            username=username,
            password=password,
            log_callback=auth_log_callback
        )
        
        if success:
            if log_callback:
                log_callback(f"[{username}] ✅ Authentication successful!")
                log_callback(f"[{username}] 📊 Method: {auth_info.get('authentication_method', 'unknown')}")
                log_callback(f"[{username}] 🍪 Cookies loaded: {auth_info.get('cookies_loaded', False)}")
                log_callback(f"[{username}] 💾 Cookies saved: {auth_info.get('cookies_saved', False)}")
            return True
        else:
            if log_callback:
                log_callback(f"[{username}] ❌ Authentication failed")
                if auth_info.get('errors'):
                    for error in auth_info['errors']:
                        log_callback(f"[{username}] ❌ Error: {error}")
            return False
            
    except Exception as e:
        if log_callback:
            log_callback(f"[{username}] ❌ Login error: {e}")
        return False
                
                if log_callback:
                    log_callback(f"[{username}] 🔍 Current URL: {current_url}")
                
                # Success: Direct redirect to home page
                if current_url == "https://www.instagram.com/" or current_url.startswith("https://www.instagram.com/?"):
                    if log_callback:
                        log_callback(f"[{username}] ✅ Login successful! Redirected to home page")
                    return page
                
                # Handle "Save your login info?" dialog
                if "accounts/onetap" in current_url:
                    if log_callback:
                        log_callback(f"[{username}] 💾 Handling 'Save login info' dialog...")
                    
                    if await handle_login_info_save_dialog(page, username, log_callback):
                        # Wait for redirect after dismissing dialog
                        try:
                            await page.wait_for_url("https://www.instagram.com/", timeout=15000)
                            if log_callback:
                                log_callback(f"[{username}] ✅ Login successful after dismissing save dialog!")
                            return page
                        except:
                            # Sometimes we don't get redirected immediately, check if we can find home page elements
                            try:
                                await page.wait_for_selector('a[href="/"]', timeout=10000)
                                if log_callback:
                                    log_callback(f"[{username}] ✅ Login successful!")
                                return page
                            except:
                                continue
                
                # Handle 2FA verification
                if await is_verification_required(page):
                    if log_callback:
                        log_callback(f"[{username}] 🔐 2FA verification required")
                    
                    if totp_secret:
                        if log_callback:
                            log_callback(f"[{username}] 🤖 Attempting automatic 2FA with TOTP secret...")
                        
                        if await handle_2fa_verification(page, username, totp_secret, log_callback):
                            # Wait for redirect after successful 2FA
                            await human_like_delay((3, 5))
                            
                            # Check if we're now on home page
                            current_url = page.url
                            if current_url == "https://www.instagram.com/" or "accounts/onetap" in current_url:
                                if "accounts/onetap" in current_url:
                                    await handle_login_info_save_dialog(page, username, log_callback)
                                    await page.wait_for_url("https://www.instagram.com/", timeout=10000)
                                
                                if log_callback:
                                    log_callback(f"[{username}] ✅ Login successful with automatic 2FA!")
                                return page
                            else:
                                if log_callback:
                                    log_callback(f"[{username}] 🔄 2FA completed, checking page status...")
                                continue
                        else:
                            if log_callback:
                                log_callback(f"[{username}] ❌ Automatic 2FA failed")
                            return None
                    else:
                        if log_callback:
                            log_callback(f"[{username}] ❌ 2FA required but no TOTP secret provided", "ERROR")
                            log_callback(f"[{username}] Cannot proceed without TOTP secret - account login failed", "ERROR")
                        return None
                
                # Check for login errors
                error_selectors = [
                    'p:has-text("Sorry, your password was incorrect")',
                    'p:has-text("The username you entered")',
                    'div:has-text("There was a problem logging you into Instagram")',
                    '[data-testid="login-error-message"]'
                ]
                
                for error_selector in error_selectors:
                    if await page.query_selector(error_selector):
                        if log_callback:
                            log_callback(f"[{username}] ❌ Login error detected - invalid credentials", "ERROR")
                        return None
                
                # If we're still on login page, there might be an issue
                if "/accounts/login/" in current_url:
                    if log_callback:
                        log_callback(f"[{username}] ⚠️ Still on login page, attempt {attempt + 1}/{max_attempts}")
                    if attempt < max_attempts - 1:
                        await human_like_delay((2, 4))
                        continue
                    else:
                        if log_callback:
                            log_callback(f"[{username}] ❌ Login failed after {max_attempts} attempts", "ERROR")
                        return None
                
                # Unknown page - wait and retry
                if log_callback:
                    log_callback(f"[{username}] 🤔 Unexpected page state, retrying...")
                await human_like_delay((3, 5))
                
            except Exception as e:
                if log_callback:
                    log_callback(f"[{username}] ⚠️ Exception during login attempt {attempt + 1}: {e}")
                if attempt == max_attempts - 1:
                    raise
                await human_like_delay((2, 4))
        
        if log_callback:
            log_callback(f"[{username}] ❌ Login failed after all attempts", "ERROR")
        return None

    except Exception as e:
        if log_callback:
            log_callback(f"[{username}] ❌ Login error: {e}", "ERROR")
        return None

async def login(context: BrowserContext, username, password, log_callback=None):
    """
    Legacy login function - now uses enhanced 2FA version with account lookup
    """
    # Try to get account details including TOTP secret
    account_details = get_account_details(username)
    totp_secret = account_details.get('totp_secret') if account_details else None
    
    if log_callback and totp_secret:
        log_callback(f"[{username}] 🔐 TOTP secret found - automatic 2FA enabled")
    elif log_callback:
        log_callback(f"[{username}] ℹ️ No TOTP secret found - manual 2FA may be required")
    
    return await login_instagram_with_cookies_and_2fa(context, username, password, totp_secret, log_callback)

async def perform_activities(page, username, duration_minutes, activities, timing, log_callback=None, stop_callback=None):
    """
    Performs a series of human-like activities on Instagram for a given duration.
    Activities include scrolling feed, watching/liking reels, liking feed posts,
    and visiting random pages.
    """
    if log_callback:
        log_callback(f"Starting activities for {username}...")
    start_time = time.time()
    end_time = start_time + duration_minutes * 60

    activity_delay = timing.get('activity_delay', DEFAULT_ACTIVITY_DELAY_SECONDS)
    scroll_attempts = timing.get('scroll_attempts', DEFAULT_SCROLL_ATTEMPTS)

    while time.time() < end_time:
        # Check if stop was requested
        if stop_callback and stop_callback():
            if log_callback:
                log_callback(f"{username}: Stopping activities due to user request.")
            break
            
        # Build activity choices based on enabled activities
        activity_choices = []
        if activities.get('feed_scroll', True):
            activity_choices.append("feed_scroll")
        if activities.get('watch_reels', True):
            activity_choices.append("watch_reel")
        if activities.get('like_reels', True):
            activity_choices.append("like_reel")
        if activities.get('like_posts', True):
            activity_choices.append("like_feed_post")
        if activities.get('explore_page', True):
            activity_choices.append("explore_scroll")
        if activities.get('random_visits', True):
            activity_choices.append("random_page_scroll")
        
        if not activity_choices:
            activity_choices = ["feed_scroll"]  # Default fallback
            
        activity_type = random.choice(activity_choices)
        if log_callback:
            log_callback(f"[{username}] 🎯 Selected activity: {activity_type}")

        try:
            if activity_type == "feed_scroll":
                if log_callback:
                    log_callback(f"[{username}] 📱 Navigating to home feed...")
                await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay, stop_callback)
                scroll_count = random.randint(*scroll_attempts)
                if log_callback:
                    log_callback(f"[{username}] 📜 Performing {scroll_count} scroll actions on feed...")
                
                for i in range(scroll_count):
                    # Check for stop signal before each scroll
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"[{username}] ⏹️ Stopping feed scroll due to user request.")
                        return
                    await human_like_scroll(page)
                    if log_callback and (i + 1) % 3 == 0:  # Log every 3rd scroll
                        log_callback(f"[{username}] 📜 Scrolled {i + 1}/{scroll_count} times on feed")

            elif activity_type == "watch_reel":
                if log_callback:
                    log_callback(f"[{username}] 🎬 Navigating to reels page...")
                await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                try:
                    scroll_count = random.randint(*scroll_attempts)
                    if log_callback:
                        log_callback(f"[{username}] 🎬 Scrolling through {scroll_count} reels...")
                    
                    for i in range(scroll_count):
                        # Check for stop signal before each scroll
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback(f"[{username}] ⏹️ Stopping reel watching due to user request.")
                            return
                        await human_like_scroll(page)

                    reels = await page.query_selector_all('div:has(video[playsinline])')
                    if reels:
                        chosen_reel = random.choice(reels)
                        await chosen_reel.scroll_into_view_if_needed()
                        watch_duration = random.uniform(5, 15)
                        if log_callback:
                            log_callback(f"[{username}] 👀 Watching a reel for {watch_duration:.1f} seconds...")
                        
                        # Check for stop signal during reel watching
                        for second in range(int(watch_duration)):
                            if stop_callback and stop_callback():
                                if log_callback:
                                    log_callback(f"[{username}] ⏹️ Stopping reel watching due to user request.")
                                return
                            await asyncio.sleep(1)
                        
                        if log_callback:
                            log_callback(f"[{username}] ✅ Finished watching reel")
                    else:
                        if log_callback:
                            log_callback(f"[{username}] ⚠️ No reels found to watch", "WARNING")
                except Exception as e:
                    if log_callback:
                        log_callback(f"[{username}] ❌ Error while trying to watch reel: {e}", "ERROR")
                await human_like_delay(activity_delay)

            elif activity_type == "like_reel":
                if log_callback:
                    log_callback(f"[{username}] ❤️ Attempting to like a reel...")
                await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                try:
                    scroll_count = random.randint(*scroll_attempts)
                    if log_callback:
                        log_callback(f"[{username}] 📜 Scrolling through {scroll_count} reels to find one to like...")
                    
                    for i in range(scroll_count):
                        # Check for stop signal before each scroll
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback(f"[{username}] ⏹️ Stopping reel liking due to user request.")
                            return
                        await human_like_scroll(page)

                    like_selectors = [
                        'svg[aria-label="Like"]',
                        'button[aria-label="Like"]',
                        'div[role="button"] svg[aria-label="Like"]',
                        'span[role="button"] svg[aria-label="Like"]'
                    ]
                    
                    if log_callback:
                        log_callback(f"[{username}] 🔍 Looking for like button...")
                    
                    like_button = None
                    for selector in like_selectors:
                        try:
                            like_button = await page.wait_for_selector(selector, timeout=3000)
                            if like_button:
                                is_visible = await like_button.is_visible()
                                if is_visible:
                                    if log_callback:
                                        log_callback(f"[{username}] 🎯 Found like button with selector: {selector}")
                                    break
                        except:
                            continue
                    
                    if like_button:
                        try:
                            await like_button.click()
                            if log_callback:
                                log_callback(f"[{username}] ❤️ Liked a reel.")
                        except:
                            try:
                                parent_button = await like_button.evaluate_handle('element => element.closest("button") || element.closest("div[role="button"]") || element.closest("span[role="button"]")')
                                if parent_button:
                                    await parent_button.click()
                                    if log_callback:
                                        log_callback(f"[{username}] ❤️ Liked a reel.")
                                else:
                                    if log_callback:
                                        log_callback(f"[{username}] ⚠️ Found like button but couldn't click it.", "WARNING")
                            except Exception as e:
                                if log_callback:
                                    log_callback(f"[{username}] ❌ Error clicking like button: {e}", "WARNING")
                    else:
                        if log_callback:
                            log_callback(f"[{username}] ⚠️ No like buttons found for reels.", "WARNING")
                except Exception as e:
                    if log_callback:
                        log_callback(f"[{username}] ❌ Error while trying to like reel: {e}", "ERROR")
                await human_like_delay(activity_delay)

            elif activity_type == "like_feed_post":
                if log_callback:
                    log_callback(f"[{username}] ❤️ Attempting to like a feed post...")
                await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                try:
                    scroll_count = random.randint(*scroll_attempts)
                    for i in range(scroll_count):
                        # Check for stop signal before each scroll
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback(f"[{username}] ⏹️ Stopping feed post liking due to user request.")
                            return
                        await human_like_scroll(page)

                    like_selectors = [
                        'svg[aria-label="Like"]',
                        'button[aria-label="Like"]',
                        'div[role="button"] svg[aria-label="Like"]',
                        'span[role="button"] svg[aria-label="Like"]'
                    ]
                    
                    like_button = None
                    for selector in like_selectors:
                        try:
                            like_buttons = await page.query_selector_all(selector)
                            if like_buttons:
                                visible_buttons = [btn for btn in like_buttons if await btn.is_visible()]
                                if visible_buttons:
                                    like_button = random.choice(visible_buttons)
                                    break
                        except:
                            continue
                    
                    if like_button:
                        try:
                            await like_button.click()
                            if log_callback:
                                log_callback(f"[{username}] ❤️ Liked a feed post.")
                        except:
                            try:
                                parent_button = await like_button.evaluate_handle('element => element.closest("button") || element.closest("div[role="button"]") || element.closest("span[role="button"]")')
                                if parent_button:
                                    await parent_button.click()
                                    if log_callback:
                                        log_callback(f"[{username}] ❤️ Liked a feed post.")
                                else:
                                    if log_callback:
                                        log_callback(f"[{username}] ⚠️ Found like button but couldn't click it.", "WARNING")
                            except Exception as e:
                                if log_callback:
                                    log_callback(f"[{username}] ❌ Error clicking like button: {e}", "WARNING")
                    else:
                        if log_callback:
                            log_callback(f"[{username}] ⚠️ No like buttons found for feed posts.", "WARNING")
                except Exception as e:
                    if log_callback:
                        log_callback(f"[{username}] ❌ Error while trying to like a feed post: {e}", "ERROR")
                await human_like_delay(activity_delay)

            elif activity_type == "explore_scroll":
                if log_callback:
                    log_callback(f"[{username}] 🗺️ Navigating to Explore page and scrolling...")
                await page.goto("https://www.instagram.com/explore/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                scroll_count = random.randint(*scroll_attempts)
                for i in range(scroll_count):
                    # Check for stop signal before each scroll
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"[{username}] ⏹️ Stopping explore scrolling due to user request.")
                        return
                    await human_like_scroll(page)
                if log_callback:
                    log_callback(f"[{username}] ✅ Finished scrolling on Explore page.")
                await human_like_delay(activity_delay)

            elif activity_type == "random_page_scroll":
                pages_to_visit = {
                    "Search": "https://www.instagram.com/explore/search/",
                    "Messages": "https://www.instagram.com/direct/inbox/",
                    "Notifications": "https://www.instagram.com/accounts/activity/",
                    "Profile": "https://www.instagram.com/accounts/edit/"
                }
                page_name, page_url = random.choice(list(pages_to_visit.items()))
                if log_callback:
                    log_callback(f"[{username}] 📄 Navigating to {page_name} page and scrolling...")
                await page.goto(page_url, wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                scroll_count = random.randint(*scroll_attempts)
                for i in range(scroll_count):
                    # Check for stop signal before each scroll
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"[{username}] ⏹️ Stopping {page_name} scrolling due to user request.")
                        return
                    await human_like_scroll(page)
                if log_callback:
                    log_callback(f"[{username}] ✅ Finished scrolling on {page_name} page.")

            elif activity_type == "like_reel":
                if log_callback:
                    log_callback(f"[{username}] ❤️ Attempting to like a reel...")
                await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                try:
                    scroll_count = random.randint(*scroll_attempts)
                    if log_callback:
                        log_callback(f"[{username}] 📜 Scrolling through {scroll_count} reels to find one to like...")
                    
                    for i in range(scroll_count):
                        # Check for stop signal before each scroll
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback(f"[{username}] ⏹️ Stopping reel liking due to user request.")
                            return
                        await human_like_scroll(page)

                    like_selectors = [
                        'svg[aria-label="Like"]',
                        'button[aria-label="Like"]',
                        'div[role="button"] svg[aria-label="Like"]',
                        'span[role="button"] svg[aria-label="Like"]'
                    ]
                    
                    if log_callback:
                        log_callback(f"[{username}] 🔍 Looking for like button...")
                    
                    like_button = None
                    for selector in like_selectors:
                        try:
                            like_button = await page.wait_for_selector(selector, timeout=3000)
                            if like_button:
                                is_visible = await like_button.is_visible()
                                if is_visible:
                                    if log_callback:
                                        log_callback(f"[{username}] 🎯 Found like button with selector: {selector}")
                                    break
                        except:
                            continue
                    
                    if like_button:
                        try:
                            await like_button.click()
                            if log_callback:
                                log_callback(f"{username}: Liked a reel.")
                        except:
                            try:
                                parent_button = await like_button.evaluate_handle('element => element.closest("button") || element.closest("div[role=\\"button\\"]") || element.closest("span[role=\\"button\\"]")')
                                if parent_button:
                                    await parent_button.click()
                                    if log_callback:
                                        log_callback(f"{username}: Liked a reel.")
                                else:
                                    if log_callback:
                                        log_callback(f"{username}: Found like button but couldn't click it.", "WARNING")
                            except Exception as e:
                                if log_callback:
                                    log_callback(f"{username}: Error clicking like button: {e}", "WARNING")
                    else:
                        if log_callback:
                            log_callback(f"{username}: No like buttons found for reels.", "WARNING")
                except Exception as e:
                    if log_callback:
                        log_callback(f"{username}: Error while trying to like reel: {e}", "ERROR")
                await human_like_delay(activity_delay)

            elif activity_type == "like_feed_post":
                if log_callback:
                    log_callback(f"{username}: Attempting to like a feed post...")
                await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                try:
                    scroll_count = random.randint(*scroll_attempts)
                    for i in range(scroll_count):
                        # Check for stop signal before each scroll
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback(f"{username}: Stopping feed post liking due to user request.")
                            return
                        await human_like_scroll(page)

                    like_selectors = [
                        'svg[aria-label="Like"]',
                        'button[aria-label="Like"]',
                        'div[role="button"] svg[aria-label="Like"]',
                        'span[role="button"] svg[aria-label="Like"]'
                    ]
                    
                    like_button = None
                    for selector in like_selectors:
                        try:
                            like_buttons = await page.query_selector_all(selector)
                            if like_buttons:
                                visible_buttons = [btn for btn in like_buttons if await btn.is_visible()]
                                if visible_buttons:
                                    like_button = random.choice(visible_buttons)
                                    break
                        except:
                            continue
                    
                    if like_button:
                        try:
                            await like_button.click()
                            if log_callback:
                                log_callback(f"{username}: Liked a feed post.")
                        except:
                            try:
                                parent_button = await like_button.evaluate_handle('element => element.closest("button") || element.closest("div[role=\\"button\\"]") || element.closest("span[role=\\"button\\"]")')
                                if parent_button:
                                    await parent_button.click()
                                    if log_callback:
                                        log_callback(f"{username}: Liked a feed post.")
                                else:
                                    if log_callback:
                                        log_callback(f"{username}: Found like button but couldn't click it.", "WARNING")
                            except Exception as e:
                                if log_callback:
                                    log_callback(f"{username}: Error clicking like button: {e}", "WARNING")
                    else:
                        if log_callback:
                            log_callback(f"{username}: No like buttons found for feed posts.", "WARNING")
                except Exception as e:
                    if log_callback:
                        log_callback(f"{username}: Error while trying to like a feed post: {e}", "ERROR")
                await human_like_delay(activity_delay)

            elif activity_type == "explore_scroll":
                if log_callback:
                    log_callback(f"{username}: Navigating to Explore page and scrolling...")
                await page.goto("https://www.instagram.com/explore/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                scroll_count = random.randint(*scroll_attempts)
                for i in range(scroll_count):
                    # Check for stop signal before each scroll
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"{username}: Stopping explore scrolling due to user request.")
                        return
                    await human_like_scroll(page)
                if log_callback:
                    log_callback(f"{username}: Finished scrolling on Explore page.")
                await human_like_delay(activity_delay)

            elif activity_type == "random_page_scroll":
                pages_to_visit = {
                    "Search": "https://www.instagram.com/explore/search/",
                    "Messages": "https://www.instagram.com/direct/inbox/",
                    "Notifications": "https://www.instagram.com/accounts/activity/",
                    "Profile": "https://www.instagram.com/accounts/edit/"
                }
                page_name, page_url = random.choice(list(pages_to_visit.items()))
                if log_callback:
                    log_callback(f"{username}: Navigating to {page_name} page and scrolling...")
                await page.goto(page_url, wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                scroll_count = random.randint(*scroll_attempts)
                for i in range(scroll_count):
                    # Check for stop signal before each scroll
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"{username}: Stopping {page_name} scrolling due to user request.")
                        return
                    await human_like_scroll(page)
                if log_callback:
                    log_callback(f"{username}: Finished scrolling on {page_name} page.")
                await human_like_delay(activity_delay)

        except Exception as e:
            if log_callback:
                log_callback(f"{username}: Unhandled error during activity '{activity_type}': {e}", "ERROR")
            
        remaining_time = int(end_time - time.time())
        if remaining_time > 0 and log_callback:
            log_callback(f"{username}: Remaining time for activities: {remaining_time // 60} minutes and {remaining_time % 60} seconds.")
        else:
            if log_callback:
                log_callback(f"{username}: Warmup duration completed.")
            break

    if log_callback:
        log_callback(f"Activities finished for {username}.")

async def worker(playwright: Playwright, account_queue: asyncio.Queue, config, log_callback=None, stop_callback=None):
    """
    Worker task to process accounts. Each worker launches a browser and processes
    accounts from the queue until it's empty.
    """
    browser = None
    context = None
    page = None
    current_username = "unknown_user"

    try:
        while True:
            # Check if stop was requested
            if stop_callback and stop_callback():
                if log_callback:
                    log_callback("Worker stopping due to user request.")
                break
            
            try:
                username, password = account_queue.get_nowait()
                current_username = username
            except asyncio.QueueEmpty:
                if log_callback:
                    log_callback("Account queue is empty. Worker exiting.")
                break

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
                    if log_callback:
                        log_callback(f"[{username}] Using assigned proxy: {proxy_info['host']}:{proxy_info['port']}")
            else:
                if log_callback:
                    log_callback(f"[{username}] No proxy assigned to this account")

            # Launch browser with proxy for this specific account
            try:
                if browser:
                    await browser.close()
                    
                browser = await playwright.chromium.launch(
                    headless=False,  # Show browser for localhost debugging
                    channel="chrome",
                    proxy=proxy_config,
                    slow_mo=1000,  # Slow down actions for visibility
                    args=[
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
                
                # Check if browser is still connected (closed detection)
                try:
                    if browser and not browser.is_connected():
                        if log_callback:
                            log_callback(f"Browser was closed manually for {current_username} - stopping worker")
                        break
                except:
                    # If we can't check browser status, assume it's closed
                    if log_callback:
                        log_callback(f"Browser connection lost for {current_username} - stopping worker") 
                    break
                    
            except Exception as e:
                if log_callback:
                    log_callback(f"Failed to launch browser for {current_username}: {e}")
                continue

            context = await browser.new_context()
            try:
                # Use enhanced authentication with cookies and proxy
                login_success = await login_instagram_with_cookies_and_2fa(context, username, password, None, log_callback)
                if login_success:
                    # Create a page for activities after successful login
                    page = await context.new_page()
                    await page.goto("https://www.instagram.com/", wait_until='domcontentloaded')
                    
                    # Check for stop signal before starting activities
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"Worker stopping for {current_username} due to user request before activities.")
                        break
                    
                    await perform_activities(
                        page, username, 
                        config['warmup_duration'], 
                        config['activities'], 
                        config['timing'],
                        log_callback, 
                        stop_callback
                    )
                else:
                    if log_callback:
                        log_callback(f"Login failed for {current_username}, skipping activities.")
            except Exception as e:
                if log_callback:
                    log_callback(f"Unhandled error in worker for {current_username}: {e}", "ERROR")
                # Continue to next account even if current one fails
            finally:
                if context:
                    try:
                        await context.close()
                        if log_callback:
                            log_callback(f"Closed browser context for {current_username}.")
                    except Exception as e:
                        if log_callback:
                            log_callback(f"Error closing context for {current_username}: {e}", "ERROR")
                account_queue.task_done()
    except Exception as e:
        if log_callback:
            log_callback(f"Worker encountered a critical error: {e}", "ERROR")
    finally:
        if browser:
            await browser.close()
            if log_callback:
                log_callback("Browser closed by worker.")

async def run_warmup_automation(
    script_id,
    accounts_file,
    warmup_duration=DEFAULT_WARMUP_DURATION_MINUTES,
    activities=None,
    timing=None,
    log_callback=None,
    stop_callback=None
):
    """
    Main function to run the Instagram warmup automation.
    """
    try:
        # Load accounts from file
        if accounts_file.endswith('.csv'):
            df = pd.read_csv(accounts_file)
        else:
            df = pd.read_excel(accounts_file)
        
        # Standardize column names
        df.columns = df.columns.str.strip().str.title()
        
        # Validate required columns
        if 'Username' not in df.columns or 'Password' not in df.columns:
            raise ValueError("Accounts file must contain 'Username' and 'Password' columns")
        
        # Filter out empty rows
        accounts = []
        for _, row in df.iterrows():
            if pd.notna(row['Username']) and pd.notna(row['Password']):
                accounts.append((str(row['Username']).strip(), str(row['Password']).strip()))
        
        if not accounts:
            raise ValueError("No valid accounts found in the file")
        
        if log_callback:
            log_callback(f"Loaded {len(accounts)} accounts from {accounts_file}")
        
        # Set default activities and timing if not provided
        if activities is None:
            activities = {
                'feed_scroll': True,
                'watch_reels': True,
                'like_reels': True,
                'like_posts': True,
                'explore_page': True,
                'random_visits': True
            }
        
        if timing is None:
            timing = {
                'activity_delay': DEFAULT_ACTIVITY_DELAY_SECONDS,
                'scroll_attempts': DEFAULT_SCROLL_ATTEMPTS
            }
        
        config = {
            'warmup_duration': warmup_duration,
            'activities': activities,
            'timing': timing
        }
        
        # Use all accounts dynamically (no concurrent limit)
        concurrent_browsers_to_use = len(accounts)
        if log_callback:
            log_callback(f"Using {concurrent_browsers_to_use} concurrent browsers (all accounts from file)")
        
        async with async_playwright() as playwright:
            total_accounts_processed = 0
            while total_accounts_processed < len(accounts):
                # Check if stop was requested
                if stop_callback and stop_callback():
                    if log_callback:
                        log_callback("Warmup automation stopped by user request.")
                    return True
                    
                current_batch = accounts[total_accounts_processed:total_accounts_processed + concurrent_browsers_to_use]
                if not current_batch:
                    if log_callback:
                        log_callback("No more accounts to process.")
                    break

                account_queue = asyncio.Queue()
                for acc in current_batch:
                    await account_queue.put(acc)

                if log_callback:
                    log_callback(f"Starting a new batch of {len(current_batch)} accounts.")
                workers = [asyncio.create_task(worker(playwright, account_queue, config, log_callback, stop_callback)) for _ in range(concurrent_browsers_to_use)]
                
                # Wait for either queue to be empty or stop signal
                while not account_queue.empty():
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback("Stop requested - cancelling all workers immediately.")
                        # Cancel all workers immediately
                        for worker_task in workers:
                            worker_task.cancel()
                        # Wait briefly for tasks to cancel
                        await asyncio.gather(*workers, return_exceptions=True)
                        return True
                    await asyncio.sleep(0.5)  # Check every 500ms
                
                # All accounts in queue are picked up, now wait for workers to complete
                await account_queue.join()
                
                if log_callback:
                    log_callback("All accounts in the current batch processed. Cleaning up workers...")
                
                # Cancel any remaining workers
                for worker_task in workers:
                    if not worker_task.done():
                        worker_task.cancel()
                
                # Wait for all workers to finish with timeout
                try:
                    await asyncio.wait_for(asyncio.gather(*workers, return_exceptions=True), timeout=5.0)
                except asyncio.TimeoutError:
                    if log_callback:
                        log_callback("Some workers took too long to stop, forcing shutdown.")
                
                total_accounts_processed += len(current_batch)
                if log_callback:
                    log_callback(f"Finished batch. Total accounts processed so far: {total_accounts_processed}/{len(accounts)}")
                
                if total_accounts_processed < len(accounts):
                    if log_callback:
                        log_callback("Pausing before starting the next batch...")
                    # Check for stop signal during the pause
                    for i in range(10):  # 10 seconds total, checking every second
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback("Warmup automation stopped by user request during batch pause.")
                            return True
                        await asyncio.sleep(1)

        if log_callback:
            log_callback("All accounts processed. Warmup automation completed successfully!", "SUCCESS")
        return True
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error in warmup automation: {e}", "ERROR")
        return False
