"""
Instagram Accounts Management Module
Handles CRUD operations for Instagram accounts storage and retrieval
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from proxy_manager import proxy_manager

ACCOUNTS_FILE = 'instagram_accounts.json'

class InstagramAccountsManager:
    def __init__(self):
        self.accounts_file = ACCOUNTS_FILE
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Ensure instagram_accounts.json exists"""
        if not os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'w') as f:
                json.dump([], f)
    
    def load_accounts(self) -> List[Dict]:
        """Load all Instagram accounts"""
        try:
            with open(self.accounts_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_accounts(self, accounts: List[Dict]) -> bool:
        """Save accounts to file"""
        try:
            with open(self.accounts_file, 'w') as f:
                json.dump(accounts, f, indent=2)
            return True
        except Exception:
            return False
    
    def get_all_accounts(self) -> List[Dict]:
        """Get all Instagram accounts with proxy information"""
        accounts = self.load_accounts()
        
        # Add proxy information to each account
        for account in accounts:
            proxy_info = self.get_account_proxy_info(account['username'])
            account.update(proxy_info)
        
        return accounts
    
    def get_active_accounts(self) -> List[Dict]:
        """Get only active Instagram accounts with proxy information"""
        accounts = self.load_accounts()
        active_accounts = [acc for acc in accounts if acc.get('is_active', True)]
        
        # Add proxy information to each account
        for account in active_accounts:
            proxy_info = self.get_account_proxy_info(account['username'])
            account.update(proxy_info)
        
        return active_accounts
    
    def add_account(self, username: str, password: str, email: str = '', 
                   phone: str = '', notes: str = '', totp_secret: str = '') -> Dict:
        """Add a new Instagram account"""
        accounts = self.load_accounts()
        
        # Check if username already exists
        if any(acc['username'].lower() == username.lower() for acc in accounts):
            raise ValueError(f"Account with username '{username}' already exists")
        
        new_account = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': password,
            'email': email,
            'phone': phone,
            'notes': notes,
            'totp_secret': totp_secret,  # Added TOTP secret field
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_used': None
        }
        
        accounts.append(new_account)
        
        if self.save_accounts(accounts):
            return new_account
        else:
            raise Exception("Failed to save account")
    
    def update_account(self, account_id: str, updates: Dict) -> bool:
        """Update an existing Instagram account"""
        accounts = self.load_accounts()
        
        for i, account in enumerate(accounts):
            if account['id'] == account_id:
                # Update fields
                if 'username' in updates:
                    # Check if new username already exists in other accounts
                    if any(acc['username'].lower() == updates['username'].lower() 
                          and acc['id'] != account_id for acc in accounts):
                        raise ValueError(f"Account with username '{updates['username']}' already exists")
                    account['username'] = updates['username']
                
                if 'password' in updates:
                    account['password'] = updates['password']
                if 'email' in updates:
                    account['email'] = updates['email']
                if 'phone' in updates:
                    account['phone'] = updates['phone']
                if 'notes' in updates:
                    account['notes'] = updates['notes']
                if 'totp_secret' in updates:
                    account['totp_secret'] = updates['totp_secret']
                if 'is_active' in updates:
                    account['is_active'] = updates['is_active']
                
                account['updated_at'] = datetime.now().isoformat()
                accounts[i] = account
                
                return self.save_accounts(accounts)
        
        return False
    
    def delete_account(self, account_id: str) -> bool:
        """Delete an Instagram account"""
        accounts = self.load_accounts()
        accounts = [acc for acc in accounts if acc['id'] != account_id]
        return self.save_accounts(accounts)
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get account by ID with proxy information"""
        accounts = self.load_accounts()
        account = next((acc for acc in accounts if acc['id'] == account_id), None)
        
        if account:
            proxy_info = self.get_account_proxy_info(account['username'])
            account.update(proxy_info)
        
        return account
    
    def get_accounts_by_ids(self, account_ids: List[str]) -> List[Dict]:
        """Get multiple accounts by their IDs with proxy information"""
        accounts = self.load_accounts()
        selected_accounts = [acc for acc in accounts if acc['id'] in account_ids and acc.get('is_active', True)]
        
        # Add proxy information to each account
        for account in selected_accounts:
            proxy_info = self.get_account_proxy_info(account['username'])
            account.update(proxy_info)
        
        return selected_accounts
    
    def update_last_used(self, account_id: str) -> bool:
        """Update the last_used timestamp for an account"""
        return self.update_account(account_id, {'last_used': datetime.now().isoformat()})
    
    def import_accounts_from_file(self, file_path: str) -> Dict:
        """Import accounts from Excel/CSV file"""
        try:
            import pandas as pd
            
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Expected columns: username, password, email (optional), phone (optional), notes (optional)
            required_columns = ['username', 'password']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Clean and validate data
            df = df.dropna(subset=required_columns)
            
            accounts = self.load_accounts()
            existing_usernames = {acc['username'].lower() for acc in accounts}
            
            added_accounts = []
            skipped_accounts = []
            
            for _, row in df.iterrows():
                username = str(row['username']).strip()
                password = str(row['password']).strip()
                
                if not username or not password:
                    skipped_accounts.append({'username': username, 'reason': 'Empty username or password'})
                    continue
                
                if username.lower() in existing_usernames:
                    skipped_accounts.append({'username': username, 'reason': 'Username already exists'})
                    continue
                
                try:
                    new_account = {
                        'id': str(uuid.uuid4()),
                        'username': username,
                        'password': password,
                        'email': str(row.get('email', '')).strip(),
                        'phone': str(row.get('phone', '')).strip(),
                        'notes': str(row.get('notes', '')).strip(),
                        'totp_secret': str(row.get('totp_secret', '')).strip(),  # Added TOTP secret support
                        'is_active': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat(),
                        'last_used': None
                    }
                    
                    accounts.append(new_account)
                    added_accounts.append(new_account)
                    existing_usernames.add(username.lower())
                    
                except Exception as e:
                    skipped_accounts.append({'username': username, 'reason': str(e)})
            
            if self.save_accounts(accounts):
                return {
                    'success': True,
                    'added_count': len(added_accounts),
                    'skipped_count': len(skipped_accounts),
                    'added_accounts': added_accounts,
                    'skipped_accounts': skipped_accounts
                }
            else:
                raise Exception("Failed to save accounts")
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_proxy_info(self, username: str) -> Dict:
        """Get proxy information for an account"""
        try:
            proxy = proxy_manager.get_account_proxy(username)
            if proxy:
                proxy_info = proxy_manager.parse_proxy(proxy)
                proxy_index = proxy_manager.get_all_proxies().index(proxy) if proxy in proxy_manager.get_all_proxies() else -1
                
                return {
                    'assigned_proxy': proxy,
                    'proxy_index': proxy_index + 1 if proxy_index >= 0 else None,
                    'proxy_host': proxy_info['host'] if proxy_info else None,
                    'proxy_port': proxy_info['port'] if proxy_info else None,
                    'has_proxy': True
                }
            else:
                return {
                    'assigned_proxy': None,
                    'proxy_index': None,
                    'proxy_host': None,
                    'proxy_port': None,
                    'has_proxy': False
                }
        except Exception:
            return {
                'assigned_proxy': None,
                'proxy_index': None,
                'proxy_host': None,
                'proxy_port': None,
                'has_proxy': False
            }
    
    def assign_proxy_to_account(self, username: str, proxy_index: Optional[int] = None) -> Dict:
        """Assign a proxy to an account"""
        try:
            proxy = proxy_manager.assign_proxy_to_account(username, proxy_index)
            return {
                'success': True,
                'proxy': proxy,
                'proxy_index': proxy_index,
                'message': f'Proxy {proxy_index + 1 if proxy_index is not None else "auto"} assigned to {username}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_proxy_assignment(self, username: str) -> Dict:
        """Remove proxy assignment from account"""
        try:
            success = proxy_manager.remove_proxy_assignment(username)
            return {
                'success': success,
                'message': f'Proxy assignment removed from {username}' if success else 'Failed to remove proxy assignment'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def reassign_proxy(self, username: str, new_proxy_index: int) -> Dict:
        """Reassign a different proxy to an account"""
        try:
            proxy = proxy_manager.reassign_proxy(username, new_proxy_index)
            return {
                'success': True,
                'proxy': proxy,
                'proxy_index': new_proxy_index + 1,
                'message': f'Proxy {new_proxy_index + 1} reassigned to {username}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
instagram_accounts_manager = InstagramAccountsManager()

def get_account_details(username: str) -> Optional[Dict]:
    """
    Get account details by username (legacy function for backward compatibility)
    Returns the account dictionary if found, None otherwise
    """
    accounts = instagram_accounts_manager.load_accounts()
    for account in accounts:
        if account.get('username', '').lower() == username.lower():
            # Add proxy information
            proxy_info = instagram_accounts_manager.get_account_proxy_info(username)
            account.update(proxy_info)
            return account
    return None

def get_all_account_usernames() -> List[str]:
    """Get all account usernames"""
    accounts = instagram_accounts_manager.load_accounts()
    return [account.get('username', '') for account in accounts if account.get('username')]
