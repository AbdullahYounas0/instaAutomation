import asyncio
import pandas as pd
from playwright.async_api import async_playwright, Playwright, BrowserContext
import random
import time
import logging
import os
import pyotp
import re
import datetime
import traceback
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
        await page.evaluate(f"window.scrollBy(0, {step_amount});")
        await asyncio.sleep(step_delay)

async def is_verification_required(page):
    """Check if the current page requires verification"""
    current_url = page.url
    verification_indicators = [
        "challenge",
        "checkpoint", 
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
    """Handle the 'Save your login info?' dialog by clicking 'Save info' or 'Not now'"""
    try:
        if log_callback:
            log_callback(f"{username}: Checking for 'Save login info' dialog...")
        
        await human_like_delay((2, 3))
        
        # Save Info button (preferred to maintain session)
        save_info_selectors = [
            'button:has-text("Save Info")',
            'button:has-text("Save info")', 
            'button:has-text("Save")',
            'div[role="button"]:has-text("Save Info")',
            'div[role="button"]:has-text("Save info")',
            'div[role="button"]:has-text("Save")'
        ]
        
        for selector in save_info_selectors:
            try:
                save_button = await page.wait_for_selector(selector, timeout=3000)
                if save_button and await save_button.is_visible():
                    await save_button.click()
                    if log_callback:
                        log_callback(f"{username}: Clicked 'Save Info' button")
                    await human_like_delay((2, 3))
                    return True
            except:
                continue
        
        # Fallback to "Not Now" if save info not found
        not_now_selectors = [
            'button:has-text("Not Now")',
            'button:has-text("Not now")',
            'div[role="button"]:has-text("Not Now")',
            'div[role="button"]:has-text("Not now")'
        ]
        
        for selector in not_now_selectors:
            try:
                not_now_button = await page.wait_for_selector(selector, timeout=2000)
                if not_now_button and await not_now_button.is_visible():
                    await not_now_button.click()
                    if log_callback:
                        log_callback(f"{username}: Clicked 'Not Now' button")
                    await human_like_delay((2, 3))
                    return True
            except:
                continue
                
        if log_callback:
            log_callback(f"{username}: No save login info dialog found")
        return True
        
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
            log_callback(f"[{username}] 🔐 Starting enhanced authentication...")
        
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

async def login(context: BrowserContext, username, password, log_callback=None):
    """
    Simple login wrapper for backward compatibility - uses enhanced auth
    """
    account_details = get_account_details(username)
    totp_secret = account_details.get('totp_secret') if account_details else None
    
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
            if log_callback:
                log_callback(f"{username}: No activities enabled, ending warmup")
            break

        activity = random.choice(activity_choices)
        
        try:
            if activity == "feed_scroll":
                await scroll_feed(page, random.randint(*scroll_attempts), log_callback, username, stop_callback)
            elif activity == "watch_reel":
                await watch_reel(page, log_callback, username, stop_callback)
            elif activity == "like_reel":
                await like_reel(page, log_callback, username, stop_callback)
            elif activity == "like_feed_post":
                await like_feed_post(page, log_callback, username, stop_callback)
            elif activity == "explore_scroll":
                await explore_scroll(page, random.randint(*scroll_attempts), log_callback, username, stop_callback)
            elif activity == "random_page_scroll":
                await random_page_scroll(page, random.randint(*scroll_attempts), log_callback, username, stop_callback)
                
        except Exception as e:
            if log_callback:
                log_callback(f"{username}: Error during {activity}: {e}")
        
        # Random delay between activities
        await human_like_delay(activity_delay, stop_callback)

    if log_callback:
        log_callback(f"Activities completed for {username}")

async def scroll_feed(page, scroll_attempts, log_callback=None, username="User", stop_callback=None):
    """Scrolls through the Instagram feed."""
    try:
        # Go to home feed if not already there
        current_url = page.url
        if "instagram.com" in current_url and current_url.count('/') <= 3:
            pass  # Already on home feed
        else:
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            await human_like_delay((2, 4), stop_callback)
        
        if log_callback:
            log_callback(f"{username}: Scrolling feed ({scroll_attempts} scrolls)")
        
        for i in range(scroll_attempts):
            if stop_callback and stop_callback():
                break
            await human_like_scroll(page)
            await human_like_delay((1, 3), stop_callback)
            
    except Exception as e:
        if log_callback:
            log_callback(f"{username}: Error scrolling feed: {e}")

async def watch_reel(page, log_callback=None, username="User", stop_callback=None):
    """Watches a reel for a random duration."""
    try:
        await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
        await human_like_delay((2, 4), stop_callback)
        
        if log_callback:
            log_callback(f"{username}: Watching reel")
        
        # Simulate watching for a random duration
        watch_duration = random.uniform(3, 15)
        await human_like_delay((watch_duration, watch_duration + 2), stop_callback)
        
    except Exception as e:
        if log_callback:
            log_callback(f"{username}: Error watching reel: {e}")

async def like_reel(page, log_callback=None, username="User", stop_callback=None):
    """Likes a reel (if on reels page)."""
    try:
        # Check if we're on a reel
        current_url = page.url
        if "/reels/" not in current_url:
            await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
            await human_like_delay((2, 4), stop_callback)
        
        # Try to find and click like button
        like_selectors = [
            'button[aria-label*="Like"]',
            'svg[aria-label="Like"]',
            'span[class*="heart"]',
            'button:has(svg[aria-label="Like"])'
        ]
        
        for selector in like_selectors:
            try:
                like_button = await page.wait_for_selector(selector, timeout=3000)
                if like_button:
                    await like_button.click()
                    if log_callback:
                        log_callback(f"{username}: Liked a reel")
                    break
            except:
                continue
                
    except Exception as e:
        if log_callback:
            log_callback(f"{username}: Error liking reel: {e}")

async def like_feed_post(page, log_callback=None, username="User", stop_callback=None):
    """Likes a post in the feed."""
    try:
        # Go to home feed
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        await human_like_delay((2, 4), stop_callback)
        
        # Scroll a bit to find posts
        await human_like_scroll(page)
        await human_like_delay((1, 2), stop_callback)
        
        # Try to find and click like button
        like_selectors = [
            'button[aria-label*="Like"]',
            'svg[aria-label="Like"]',
            'span[class*="heart"]',
            'button:has(svg[aria-label="Like"])'
        ]
        
        for selector in like_selectors:
            try:
                like_buttons = await page.query_selector_all(selector)
                if like_buttons:
                    # Click a random like button
                    button = random.choice(like_buttons)
                    await button.click()
                    if log_callback:
                        log_callback(f"{username}: Liked a feed post")
                    break
            except:
                continue
                
    except Exception as e:
        if log_callback:
            log_callback(f"{username}: Error liking feed post: {e}")

async def explore_scroll(page, scroll_attempts, log_callback=None, username="User", stop_callback=None):
    """Scrolls through the explore page."""
    try:
        await page.goto("https://www.instagram.com/explore/", wait_until="domcontentloaded")
        await human_like_delay((2, 4), stop_callback)
        
        if log_callback:
            log_callback(f"{username}: Scrolling explore page ({scroll_attempts} scrolls)")
        
        for i in range(scroll_attempts):
            if stop_callback and stop_callback():
                break
            await human_like_scroll(page)
            await human_like_delay((1, 3), stop_callback)
            
    except Exception as e:
        if log_callback:
            log_callback(f"{username}: Error scrolling explore: {e}")

async def random_page_scroll(page, scroll_attempts, log_callback=None, username="User", stop_callback=None):
    """Visits a random page and scrolls."""
    try:
        # List of popular accounts to visit
        random_pages = [
            "instagram", "nasa", "natgeo", "nike", "cocacola", 
            "disney", "marvel", "netflix", "spotify", "google"
        ]
        
        random_page = random.choice(random_pages)
        await page.goto(f"https://www.instagram.com/{random_page}/", wait_until="domcontentloaded")
        await human_like_delay((2, 4), stop_callback)
        
        if log_callback:
            log_callback(f"{username}: Visiting @{random_page} and scrolling")
        
        for i in range(scroll_attempts):
            if stop_callback and stop_callback():
                break
            await human_like_scroll(page)
            await human_like_delay((1, 3), stop_callback)
            
    except Exception as e:
        if log_callback:
            log_callback(f"{username}: Error with random page visit: {e}")

async def warmup_worker(accounts, config, semaphore, log_callback=None, stop_callback=None):
    """
    Worker function that processes accounts with a semaphore to limit concurrency.
    Each worker handles one account at a time.
    """
    async with semaphore:
        for account in accounts:
            # Check if stop was requested
            if stop_callback and stop_callback():
                if log_callback:
                    log_callback("Worker stopping due to user request.")
                break
            
            username = account['username']
            password = account['password']
            current_username = f"{username[:8]}..." if len(username) > 8 else username
            
            if log_callback:
                log_callback(f"Starting warmup for {current_username}")
            
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
                        log_callback(f"Using proxy for {current_username}: {proxy_info['host']}:{proxy_info['port']}")
            else:
                if log_callback:
                    log_callback(f"No proxy assigned for {current_username}")
            
            playwright = None
            browser = None
            try:
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(
                    headless=True,
                    proxy=proxy_config,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                if log_callback:
                    log_callback(f"Browser launched for {current_username}")
                    
            except Exception as e:
                if log_callback:
                    log_callback(f"Failed to launch browser for {current_username}: {e}")
                
                # Check if it's a browser installation issue
                if "Executable doesn't exist" in str(e) or "playwright install" in str(e).lower():
                    if log_callback:
                        log_callback(f"Browser not installed for {current_username}. Attempting to install browsers...")
                    try:
                        import subprocess
                        result = subprocess.run(['playwright', 'install', 'chromium'], 
                                              capture_output=True, text=True, timeout=300)
                        if result.returncode == 0:
                            if log_callback:
                                log_callback(f"Browser installation completed for {current_username}. Retrying launch...")
                            # Retry browser launch after installation
                            playwright = await async_playwright().start()
                            browser = await playwright.chromium.launch(
                                headless=True,
                                proxy=proxy_config,
                                args=['--no-sandbox', '--disable-setuid-sandbox']
                            )
                            if log_callback:
                                log_callback(f"Browser launched successfully for {current_username} after installation")
                        else:
                            if log_callback:
                                log_callback(f"Browser installation failed for {current_username}: {result.stderr}")
                            # Try system-level installation
                            subprocess.run(['python', '-m', 'playwright', 'install', 'chromium'], timeout=300)
                            playwright = await async_playwright().start()
                            browser = await playwright.chromium.launch(
                                headless=True,
                                proxy=proxy_config,
                                args=['--no-sandbox', '--disable-setuid-sandbox']
                            )
                            if log_callback:
                                log_callback(f"Browser launched for {current_username} after system installation")
                    except Exception as install_error:
                        if log_callback:
                            log_callback(f"Browser installation failed for {current_username}: {install_error}")
                        continue
                else:
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
                    
                    if log_callback:
                        log_callback(f"Warmup completed for {current_username}")
                else:
                    if log_callback:
                        log_callback(f"Login failed for {current_username}")
                        
            except Exception as e:
                if log_callback:
                    log_callback(f"Error during warmup for {current_username}: {e}")
            finally:
                try:
                    await context.close()
                    await browser.close()
                    if playwright:
                        await playwright.stop()
                except Exception as e:
                    if log_callback:
                        log_callback(f"Error closing resources for {current_username}: {e}")

def load_accounts_from_file(file_path):
    """Load accounts from CSV or Excel file."""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        if df.empty:
            return []
        
        # Standardize column names
        df.columns = df.columns.str.strip().str.title()
        
        # Check for required columns
        if 'Username' not in df.columns or 'Password' not in df.columns:
            return []
        
        accounts = []
        for i in range(len(df)):
            username = df.loc[i, "Username"]
            password = df.loc[i, "Password"]
            if pd.notna(username) and pd.notna(password):
                accounts.append({
                    'username': str(username).strip(),
                    'password': str(password).strip()
                })
        
        return accounts
        
    except Exception as e:
        logging.error(f"Error loading accounts: {e}")
        return []

async def run_warmup_automation(script_id, accounts_file, warmup_duration, activities, timing, log_callback=None, stop_callback=None):
    """
    Main function to run Instagram warmup automation - compatible with app.py interface.
    
    Args:
        script_id: Unique identifier for this script run
        accounts_file: Path to accounts CSV/Excel file
        warmup_duration: Duration in minutes for warmup
        activities: Dictionary of enabled activities
        timing: Dictionary of timing settings
        log_callback: Function to call for logging
        stop_callback: Function to check if execution should stop
    """
    try:
        # Create config from parameters to match new interface
        config = {
            'warmup_duration': warmup_duration,
            'activities': activities,
            'timing': timing,
            'max_concurrent_browsers': DEFAULT_MAX_CONCURRENT_BROWSERS
        }
        
        if log_callback:
            log_callback(f"[Script {script_id}] Starting warmup automation...")
        
        # Load accounts
        accounts = load_accounts_from_file(accounts_file)
        if not accounts:
            if log_callback:
                log_callback("No valid accounts found in file")
            return False
        
        if log_callback:
            log_callback(f"Loaded {len(accounts)} accounts for warmup")
        
        # Limit concurrent browsers
        max_concurrent = min(config.get('max_concurrent_browsers', DEFAULT_MAX_CONCURRENT_BROWSERS), len(accounts))
        semaphore = asyncio.Semaphore(max_concurrent)
        
        if log_callback:
            log_callback(f"Starting warmup with max {max_concurrent} concurrent browsers")
        
        # Split accounts into chunks for workers
        chunk_size = max(1, len(accounts) // max_concurrent)
        account_chunks = [accounts[i:i + chunk_size] for i in range(0, len(accounts), chunk_size)]
        
        # Create worker tasks
        tasks = []
        for chunk in account_chunks:
            if chunk:  # Only create task if chunk is not empty
                task = asyncio.create_task(
                    warmup_worker(chunk, config, semaphore, log_callback, stop_callback)
                )
                tasks.append(task)
        
        # Wait for all workers to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        if log_callback:
            log_callback("All warmup workers completed")
        
        return True
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error in warmup execution: {e}")
        return False

async def run_warmup(accounts_file, config, log_callback=None, stop_callback=None):
    """
    Legacy function for backward compatibility.
    
    Args:
        accounts_file: Path to accounts CSV/Excel file
        config: Configuration dictionary with warmup settings
        log_callback: Function to call for logging
        stop_callback: Function to check if execution should stop
    """
    return await run_warmup_automation(
        script_id="legacy",
        accounts_file=accounts_file,
        warmup_duration=config.get('warmup_duration', DEFAULT_WARMUP_DURATION_MINUTES),
        activities=config.get('activities', {}),
        timing=config.get('timing', {}),
        log_callback=log_callback,
        stop_callback=stop_callback
    )
