"""
Instagram Authentication Helper
Provides easy-to-use functions for integrating enhanced authentication into existing scripts
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from enhanced_instagram_auth import enhanced_auth
from instagram_cookie_manager import cookie_manager
from instagram_accounts import get_account_details
from proxy_manager import proxy_manager

logger = logging.getLogger(__name__)

class InstagramAuthHelper:
    def __init__(self):
        self.active_contexts = {}
        self.authentication_cache = {}
    
    async def create_authenticated_context(
        self, 
        username: str, 
        password: str = None,
        headless: bool = True,
        user_data_dir: str = None,
        log_callback: callable = None
    ) -> Tuple[bool, Optional[BrowserContext], Dict]:
        """
        Create a browser context that's authenticated with Instagram
        
        Args:
            username: Instagram username
            password: Instagram password (optional if cookies exist)
            headless: Whether to run browser in headless mode
            user_data_dir: Custom user data directory
            log_callback: Function for logging messages
            
        Returns:
            Tuple[bool, Optional[BrowserContext], Dict]: (success, context, info)
        """
        info = {
            'username': username,
            'browser_created': False,
            'context_created': False,
            'authentication_success': False,
            'proxy_info': None,
            'errors': []
        }
        
        def log(message: str, level: str = "INFO"):
            if log_callback:
                log_callback(message)
            logger.log(getattr(logging, level, logging.INFO), message)
        
        try:
            # Get account details
            account_details = get_account_details(username)
            if not account_details and not password:
                error_msg = f"No account details found for {username} and no password provided"
                info['errors'].append(error_msg)
                log(error_msg, "ERROR")
                return False, None, info
            
            password = password or account_details.get('password', '') if account_details else ''
            
            if not password and not cookie_manager.are_cookies_valid(username):
                error_msg = f"No password available and no valid cookies for {username}"
                info['errors'].append(error_msg)
                log(error_msg, "ERROR")
                return False, None, info
            
            # Setup browser context with proxy
            playwright = await async_playwright().start()
            
            # Get proxy configuration
            proxy_config = None
            proxy_string = proxy_manager.get_account_proxy(username)
            
            if proxy_string:
                parsed_proxy = proxy_manager.parse_proxy(proxy_string)
                if parsed_proxy:
                    proxy_config = {
                        'server': parsed_proxy['server'],
                        'username': parsed_proxy['username'],
                        'password': parsed_proxy['password']
                    }
                    info['proxy_info'] = {
                        'host': parsed_proxy['host'],
                        'port': parsed_proxy['port'],
                        'proxy_string': proxy_string
                    }
                    log(f"🌐 Using proxy: {parsed_proxy['host']}:{parsed_proxy['port']}")
            
            # Launch browser
            browser_args = {
                'headless': headless,
                'args': [
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Speed optimization
                    '--disable-javascript',  # Will enable selectively
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            }
            
            if proxy_config:
                browser_args['proxy'] = proxy_config
            
            if user_data_dir:
                browser_args['user_data_dir'] = user_data_dir
            
            # Use Chrome instead of Chromium with specific executable path
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get('USERNAME', '')),
                r"C:\Users\{}\AppData\Local\Programs\Google Chrome\Application\chrome.exe".format(os.environ.get('USERNAME', ''))
            ]
            
            browser_launched = False
            for chrome_path in chrome_paths:
                try:
                    if os.path.exists(chrome_path):
                        browser_args['executable_path'] = chrome_path
                        browser = await playwright.chromium.launch(**browser_args)
                        log_callback(f"✅ Using Chrome from: {chrome_path}")
                        browser_launched = True
                        break
                except Exception as e:
                    log_callback(f"⚠️ Failed to use Chrome at {chrome_path}: {e}")
                    continue
            
            if not browser_launched:
                try:
                    # Try channel method as backup
                    browser = await playwright.chromium.launch(channel="chrome", **browser_args)
                    log_callback("✅ Using Chrome via channel method")
                except Exception as e:
                    log_callback(f"Chrome not found, falling back to Chromium: {e}")
                    browser = await playwright.chromium.launch(**browser_args)
            info['browser_created'] = True
            
            # Create context
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            info['context_created'] = True
            
            # Enable JavaScript for Instagram
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            log(f"🚀 Starting enhanced authentication for {username}...")
            
            # Perform authentication
            auth_success, auth_info = await enhanced_auth.authenticate_with_cookies_and_proxy(
                context, username, password, log_callback
            )
            
            if auth_success:
                info['authentication_success'] = True
                info.update(auth_info)
                self.active_contexts[username] = context
                log(f"✅ Authentication successful for {username}")
                return True, context, info
            else:
                info['errors'].extend(auth_info.get('errors', []))
                log(f"❌ Authentication failed for {username}")
                await context.close()
                await browser.close()
                return False, None, info
        
        except Exception as e:
            error_msg = f"Error creating authenticated context: {str(e)}"
            info['errors'].append(error_msg)
            log(error_msg, "ERROR")
            
            # Cleanup on error
            try:
                if 'context' in locals():
                    await context.close()
                if 'browser' in locals():
                    await browser.close()
            except:
                pass
            
            return False, None, info
    
    async def quick_login_check(self, username: str, log_callback: callable = None) -> Dict:
        """
        Quick check of login status without creating full browser context
        
        Args:
            username: Instagram username
            log_callback: Function for logging messages
            
        Returns:
            Dict: Status information
        """
        def log(message: str, level: str = "INFO"):
            if log_callback:
                log_callback(message)
            logger.log(getattr(logging, level, logging.INFO), message)
        
        result = {
            'username': username,
            'has_valid_cookies': False,
            'has_account_details': False,
            'has_proxy': False,
            'proxy_info': None,
            'estimated_ready': False,
            'recommendations': []
        }
        
        try:
            # Check cookies
            if cookie_manager.are_cookies_valid(username):
                result['has_valid_cookies'] = True
                log(f"✅ {username} has valid cookies")
            else:
                result['recommendations'].append("Needs fresh login to get new cookies")
                log(f"❌ {username} has no valid cookies")
            
            # Check account details
            account_details = get_account_details(username)
            if account_details:
                result['has_account_details'] = True
                result['has_proxy'] = account_details.get('has_proxy', False)
                
                if result['has_proxy']:
                    result['proxy_info'] = {
                        'host': account_details.get('proxy_host'),
                        'port': account_details.get('proxy_port'),
                        'index': account_details.get('proxy_index')
                    }
                    log(f"✅ {username} has assigned proxy")
                else:
                    result['recommendations'].append("Should assign a proxy for better success rate")
                    log(f"⚠️ {username} has no assigned proxy")
            else:
                result['recommendations'].append("Account not found in database")
                log(f"❌ {username} not found in account database")
            
            # Overall assessment
            if result['has_valid_cookies'] and result['has_account_details']:
                result['estimated_ready'] = True
                log(f"🎉 {username} is ready for automation")
            else:
                log(f"⚠️ {username} needs setup before automation")
            
            return result
            
        except Exception as e:
            log(f"Error checking login status for {username}: {e}", "ERROR")
            result['error'] = str(e)
            return result
    
    async def bulk_authentication_check(self, usernames: List[str], log_callback: callable = None) -> Dict:
        """
        Check authentication status for multiple accounts
        
        Args:
            usernames: List of Instagram usernames
            log_callback: Function for logging messages
            
        Returns:
            Dict: Bulk status information
        """
        def log(message: str, level: str = "INFO"):
            if log_callback:
                log_callback(message)
            logger.log(getattr(logging, level, logging.INFO), message)
        
        log(f"🔍 Checking authentication status for {len(usernames)} accounts...")
        
        results = {}
        summary = {
            'total_accounts': len(usernames),
            'ready_accounts': 0,
            'needs_cookies': 0,
            'needs_proxy': 0,
            'needs_account_setup': 0,
            'estimated_success_rate': 0
        }
        
        for username in usernames:
            try:
                result = await self.quick_login_check(username, log_callback)
                results[username] = result
                
                if result['estimated_ready']:
                    summary['ready_accounts'] += 1
                if not result['has_valid_cookies']:
                    summary['needs_cookies'] += 1
                if not result['has_proxy']:
                    summary['needs_proxy'] += 1
                if not result['has_account_details']:
                    summary['needs_account_setup'] += 1
                    
            except Exception as e:
                log(f"Error checking {username}: {e}", "ERROR")
                results[username] = {'error': str(e)}
        
        # Calculate success rate
        if summary['total_accounts'] > 0:
            summary['estimated_success_rate'] = (summary['ready_accounts'] / summary['total_accounts']) * 100
        
        log(f"📊 Summary: {summary['ready_accounts']}/{summary['total_accounts']} accounts ready ({summary['estimated_success_rate']:.1f}%)")
        
        return {
            'summary': summary,
            'individual_results': results,
            'timestamp': asyncio.get_event_loop().time()
        }
    
    async def cleanup_expired_data(self, log_callback: callable = None) -> Dict:
        """
        Clean up expired cookies and old data
        
        Args:
            log_callback: Function for logging messages
            
        Returns:
            Dict: Cleanup results
        """
        def log(message: str, level: str = "INFO"):
            if log_callback:
                log_callback(message)
            logger.log(getattr(logging, level, logging.INFO), message)
        
        log("🧹 Starting cleanup of expired data...")
        
        try:
            # Cleanup expired cookies
            cleaned_cookies = cookie_manager.cleanup_expired_cookies()
            
            # Close any inactive contexts
            closed_contexts = 0
            for username, context in list(self.active_contexts.items()):
                try:
                    # Try to access context - if it fails, it's already closed
                    await context.pages
                except:
                    # Context is closed, remove from tracking
                    del self.active_contexts[username]
                    closed_contexts += 1
            
            result = {
                'cleaned_cookie_files': cleaned_cookies,
                'closed_inactive_contexts': closed_contexts,
                'active_contexts_remaining': len(self.active_contexts),
                'timestamp': asyncio.get_event_loop().time()
            }
            
            log(f"✅ Cleanup complete: {cleaned_cookies} cookie files, {closed_contexts} contexts")
            return result
            
        except Exception as e:
            log(f"❌ Error during cleanup: {e}", "ERROR")
            return {'error': str(e)}
    
    async def close_context(self, username: str, log_callback: callable = None) -> bool:
        """
        Close browser context for a specific user
        
        Args:
            username: Instagram username
            log_callback: Function for logging messages
            
        Returns:
            bool: True if closed successfully
        """
        def log(message: str, level: str = "INFO"):
            if log_callback:
                log_callback(message)
            logger.log(getattr(logging, level, logging.INFO), message)
        
        try:
            if username in self.active_contexts:
                context = self.active_contexts[username]
                await context.close()
                del self.active_contexts[username]
                log(f"✅ Closed context for {username}")
                return True
            else:
                log(f"ℹ️ No active context found for {username}")
                return True
                
        except Exception as e:
            log(f"❌ Error closing context for {username}: {e}", "ERROR")
            return False
    
    async def close_all_contexts(self, log_callback: callable = None) -> int:
        """
        Close all active browser contexts
        
        Args:
            log_callback: Function for logging messages
            
        Returns:
            int: Number of contexts closed
        """
        def log(message: str, level: str = "INFO"):
            if log_callback:
                log_callback(message)
            logger.log(getattr(logging, level, logging.INFO), message)
        
        closed_count = 0
        
        for username in list(self.active_contexts.keys()):
            if await self.close_context(username, log_callback):
                closed_count += 1
        
        log(f"✅ Closed {closed_count} browser contexts")
        return closed_count
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        stored_accounts = cookie_manager.get_all_stored_accounts()
        
        return {
            'active_contexts': len(self.active_contexts),
            'stored_cookie_accounts': len(stored_accounts),
            'valid_cookie_accounts': len([acc for acc in stored_accounts if acc['is_valid']]),
            'proxy_assignments': len(proxy_manager.get_all_assignments()),
            'authentication_stats': enhanced_auth.get_authentication_stats(),
            'timestamp': asyncio.get_event_loop().time()
        }

# Global instance
auth_helper = InstagramAuthHelper()