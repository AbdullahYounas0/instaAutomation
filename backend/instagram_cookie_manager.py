"""
Instagram Cookie Management System
Handles secure cookie storage, loading, and validation for Instagram accounts
"""

import json
import os
import time
import pickle
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib
import logging

logger = logging.getLogger(__name__)

class InstagramCookieManager:
    def __init__(self):
        self.cookies_dir = Path("instagram_cookies")
        self.cookies_dir.mkdir(exist_ok=True)
        
        # Cookie expiration settings
        self.cookie_expiry_days = 30
        self.session_timeout_hours = 24
    
    def _get_cookie_file_path(self, username: str) -> Path:
        """Get the cookie file path for a username"""
        # Hash username to avoid filesystem issues with special characters
        username_hash = hashlib.md5(username.lower().encode()).hexdigest()
        return self.cookies_dir / f"{username_hash}_{username.lower()}.json"
    
    def _encrypt_cookie_data(self, data: Dict) -> str:
        """Simple base64 encoding for cookie data (can be enhanced with proper encryption)"""
        try:
            json_str = json.dumps(data)
            encoded = base64.b64encode(json_str.encode()).decode()
            return encoded
        except Exception as e:
            logger.error(f"Error encrypting cookie data: {e}")
            return ""
    
    def _decrypt_cookie_data(self, encoded_data: str) -> Dict:
        """Simple base64 decoding for cookie data"""
        try:
            json_str = base64.b64decode(encoded_data.encode()).decode()
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error decrypting cookie data: {e}")
            return {}
    
    def save_cookies(self, username: str, cookies: List[Dict], proxy_info: Optional[Dict] = None) -> bool:
        """
        Save Instagram cookies for a username
        
        Args:
            username: Instagram username
            cookies: List of cookie dictionaries from Playwright
            proxy_info: Proxy information used for this session
            
        Returns:
            bool: True if cookies saved successfully
        """
        try:
            cookie_file = self._get_cookie_file_path(username)
            
            # Prepare cookie data
            cookie_data = {
                'username': username.lower(),
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=self.cookie_expiry_days)).isoformat(),
                'session_expires_at': (datetime.now() + timedelta(hours=self.session_timeout_hours)).isoformat(),
                'proxy_info': proxy_info,
                'last_used': datetime.now().isoformat(),
                'login_count': self._get_login_count(username) + 1
            }
            
            # Encrypt and save
            encrypted_data = self._encrypt_cookie_data(cookie_data)
            if not encrypted_data:
                return False
            
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'encrypted_data': encrypted_data,
                    'metadata': {
                        'username': username.lower(),
                        'created_at': datetime.now().isoformat(),
                        'version': '1.0'
                    }
                }, f, indent=2)
            
            logger.info(f"Cookies saved for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cookies for {username}: {e}")
            return False
    
    def load_cookies(self, username: str) -> Optional[Dict]:
        """
        Load Instagram cookies for a username
        
        Args:
            username: Instagram username
            
        Returns:
            Dict with cookies and metadata, or None if not found/expired
        """
        try:
            cookie_file = self._get_cookie_file_path(username)
            
            if not cookie_file.exists():
                logger.info(f"No cookie file found for {username}")
                return None
            
            # Load encrypted data
            with open(cookie_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            encrypted_data = file_data.get('encrypted_data')
            if not encrypted_data:
                logger.warning(f"No encrypted data in cookie file for {username}")
                return None
            
            # Decrypt cookie data
            cookie_data = self._decrypt_cookie_data(encrypted_data)
            if not cookie_data:
                logger.warning(f"Failed to decrypt cookie data for {username}")
                return None
            
            # Check expiration
            expires_at = datetime.fromisoformat(cookie_data.get('expires_at', ''))
            if datetime.now() > expires_at:
                logger.info(f"Cookies expired for {username}")
                self.delete_cookies(username)
                return None
            
            # Update last used timestamp
            cookie_data['last_used'] = datetime.now().isoformat()
            self.save_cookies(username, cookie_data['cookies'], cookie_data.get('proxy_info'))
            
            logger.info(f"Cookies loaded for {username}")
            return cookie_data
            
        except Exception as e:
            logger.error(f"Error loading cookies for {username}: {e}")
            return None
    
    def are_cookies_valid(self, username: str) -> bool:
        """
        Check if cookies exist and are valid for a username
        
        Args:
            username: Instagram username
            
        Returns:
            bool: True if cookies are valid
        """
        cookie_data = self.load_cookies(username)
        if not cookie_data:
            return False
        
        # Check session expiration
        session_expires_at = datetime.fromisoformat(cookie_data.get('session_expires_at', ''))
        if datetime.now() > session_expires_at:
            logger.info(f"Session expired for {username}")
            return False
        
        # Check if cookies list is not empty and has essential cookies
        cookies = cookie_data.get('cookies', [])
        if not cookies:
            return False
        
        # Look for essential Instagram cookies
        essential_cookies = ['sessionid', 'csrftoken']
        cookie_names = [cookie.get('name', '') for cookie in cookies]
        
        for essential in essential_cookies:
            if essential not in cookie_names:
                logger.info(f"Missing essential cookie '{essential}' for {username}")
                return False
        
        return True
    
    def delete_cookies(self, username: str) -> bool:
        """
        Delete cookies for a username
        
        Args:
            username: Instagram username
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            cookie_file = self._get_cookie_file_path(username)
            
            if cookie_file.exists():
                cookie_file.unlink()
                logger.info(f"Cookies deleted for {username}")
                return True
            else:
                logger.info(f"No cookies to delete for {username}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting cookies for {username}: {e}")
            return False
    
    def get_all_stored_accounts(self) -> List[Dict]:
        """
        Get list of all accounts with stored cookies
        
        Returns:
            List of account info dictionaries
        """
        accounts = []
        
        try:
            for cookie_file in self.cookies_dir.glob("*.json"):
                try:
                    with open(cookie_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    metadata = file_data.get('metadata', {})
                    username = metadata.get('username', 'unknown')
                    
                    # Get basic info
                    cookie_data = self.load_cookies(username)
                    if cookie_data:
                        accounts.append({
                            'username': username,
                            'saved_at': cookie_data.get('saved_at'),
                            'expires_at': cookie_data.get('expires_at'),
                            'last_used': cookie_data.get('last_used'),
                            'login_count': cookie_data.get('login_count', 0),
                            'has_proxy': cookie_data.get('proxy_info') is not None,
                            'proxy_info': cookie_data.get('proxy_info'),
                            'is_valid': self.are_cookies_valid(username)
                        })
                
                except Exception as e:
                    logger.error(f"Error reading cookie file {cookie_file}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error getting stored accounts: {e}")
        
        return accounts
    
    def _get_login_count(self, username: str) -> int:
        """Get the current login count for a username"""
        cookie_data = self.load_cookies(username)
        return cookie_data.get('login_count', 0) if cookie_data else 0
    
    def cleanup_expired_cookies(self) -> int:
        """
        Clean up expired cookie files
        
        Returns:
            int: Number of files cleaned up
        """
        cleaned_count = 0
        
        try:
            for cookie_file in self.cookies_dir.glob("*.json"):
                try:
                    with open(cookie_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    encrypted_data = file_data.get('encrypted_data')
                    if not encrypted_data:
                        cookie_file.unlink()
                        cleaned_count += 1
                        continue
                    
                    cookie_data = self._decrypt_cookie_data(encrypted_data)
                    if not cookie_data:
                        cookie_file.unlink()
                        cleaned_count += 1
                        continue
                    
                    expires_at = datetime.fromisoformat(cookie_data.get('expires_at', ''))
                    if datetime.now() > expires_at:
                        cookie_file.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up expired cookies: {cookie_file.name}")
                
                except Exception as e:
                    logger.error(f"Error checking cookie file {cookie_file}: {e}")
                    # Remove corrupted files
                    try:
                        cookie_file.unlink()
                        cleaned_count += 1
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"Error during cookie cleanup: {e}")
        
        logger.info(f"Cookie cleanup completed: {cleaned_count} files removed")
        return cleaned_count

# Global instance
cookie_manager = InstagramCookieManager()