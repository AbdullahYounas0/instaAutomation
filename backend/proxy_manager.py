"""
Proxy Management Module
Handles proxy assignment and management for Instagram accounts
"""

import json
import os
import threading
from typing import List, Dict, Optional
from datetime import datetime

# Proxy list - centralized proxy configuration
PROXIES = [
    "207.228.28.217:7866:silwfmmt:9mnui1h717nw",
    "156.237.42.124:8023:silwfmmt:9mnui1h717nw",
    "46.203.104.5:7502:silwfmmt:9mnui1h717nw",
    "154.194.25.13:5031:silwfmmt:9mnui1h717nw",
    "207.228.32.142:6759:silwfmmt:9mnui1h717nw",
    "46.203.54.224:8222:silwfmmt:9mnui1h717nw",
    "207.228.14.23:5315:silwfmmt:9mnui1h717nw",
    "69.30.79.150:5203:silwfmmt:9mnui1h717nw",
    "69.30.79.15:5068:silwfmmt:9mnui1h717nw",
    "69.30.79.149:5202:silwfmmt:9mnui1h717nw",
    "46.203.54.223:8221:silwfmmt:9mnui1h717nw",
    "69.30.79.83:5136:silwfmmt:9mnui1h717nw",
    "46.203.54.10:8008:silwfmmt:9mnui1h717nw",
    "46.203.104.207:7704:silwfmmt:9mnui1h717nw",
    "69.30.79.107:5160:silwfmmt:9mnui1h717nw",
    "69.30.79.54:5107:silwfmmt:9mnui1h717nw",
    "69.30.79.227:5280:silwfmmt:9mnui1h717nw",
    "69.30.79.201:5254:silwfmmt:9mnui1h717nw",
    "69.30.79.191:5244:silwfmmt:9mnui1h717nw",
    "69.30.79.79:5132:silwfmmt:9mnui1h717nw"
]

PROXY_ASSIGNMENTS_FILE = 'proxy_assignments.json'

class ProxyManager:
    def __init__(self):
        self.assignments_file = PROXY_ASSIGNMENTS_FILE
        self.lock = threading.Lock()
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Ensure proxy_assignments.json exists"""
        if not os.path.exists(self.assignments_file):
            with open(self.assignments_file, 'w') as f:
                json.dump({}, f)
    
    def load_assignments(self) -> Dict:
        """Load proxy assignments from file"""
        try:
            with open(self.assignments_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_assignments(self, assignments: Dict) -> bool:
        """Save proxy assignments to file"""
        try:
            with open(self.assignments_file, 'w') as f:
                json.dump(assignments, f, indent=2)
            return True
        except Exception:
            return False
    
    def get_all_proxies(self) -> List[str]:
        """Get all available proxies"""
        return PROXIES.copy()
    
    def parse_proxy(self, proxy_string: str) -> Optional[Dict]:
        """Parse proxy string into components - handles both URL and colon-separated formats"""
        try:
            # Handle URL format without protocol: username:password@host:port
            if '@' in proxy_string and not proxy_string.startswith('http'):
                credentials, host_port = proxy_string.split('@', 1)
                username, password = credentials.split(':', 1)
                host, port = host_port.split(':', 1)
                
                return {
                    'server': f'http://{host}:{port}',  # Add http:// for server URL
                    'host': host,
                    'port': port,
                    'username': username,
                    'password': password
                }
            
            # Handle new URL format: https://username:password@host:port
            if proxy_string.startswith('https://') or proxy_string.startswith('http://'):
                # Remove protocol
                if proxy_string.startswith('https://'):
                    url_part = proxy_string[8:]  # Remove 'https://'
                else:
                    url_part = proxy_string[7:]   # Remove 'http://'
                
                # Split at @ to separate credentials from host:port
                if '@' in url_part:
                    credentials, host_port = url_part.split('@', 1)
                    username, password = credentials.split(':', 1)
                    host, port = host_port.split(':', 1)
                    
                    return {
                        'server': f'http://{host}:{port}',  # Use http:// for server
                        'host': host,
                        'port': port,
                        'username': username,
                        'password': password
                    }
            
            # Handle old colon-separated format: host:port:username:password
            parts = proxy_string.split(':')
            if len(parts) == 4:
                return {
                    'server': f'http://{parts[0]}:{parts[1]}',
                    'host': parts[0],
                    'port': parts[1],
                    'username': parts[2],
                    'password': parts[3]
                }
            return None
        except Exception:
            return None
    
    def assign_proxy_to_account(self, account_username: str, proxy_index: Optional[int] = None) -> Optional[str]:
        """
        Assign a proxy to an Instagram account with strict one-to-one binding
        If proxy_index is provided, assign that specific proxy
        If proxy_index is None, assign the next available proxy
        
        STRICT RULE: One proxy per account, one account per proxy (NO EXCEPTIONS)
        """
        with self.lock:
            assignments = self.load_assignments()
            
            # Check if account already has a proxy assigned
            if account_username in assignments:
                current_proxy = assignments[account_username]
                raise ValueError(f"Account {account_username} already has a proxy assigned: {current_proxy}. Use reassign_proxy() to change it.")
            
            # If specific proxy index requested
            if proxy_index is not None:
                if 0 <= proxy_index < len(PROXIES):
                    proxy = PROXIES[proxy_index]
                    
                    # STRICT CHECK: Ensure this proxy is not assigned to ANY other account
                    assigned_proxies = set(assignments.values())
                    if proxy in assigned_proxies:
                        # Find which account has this proxy
                        assigned_account = next(
                            (acc for acc, prx in assignments.items() if prx == proxy), 
                            None
                        )
                        raise ValueError(f"STRICT BINDING VIOLATION: Proxy {proxy_index + 1} is already assigned to account: {assigned_account}")
                    
                    # Assign the proxy with strict binding
                    assignments[account_username] = proxy
                    
                    if self.save_assignments(assignments):
                        return proxy
                    else:
                        raise Exception("Failed to save proxy assignment")
                else:
                    raise ValueError(f"Invalid proxy index: {proxy_index} (available: 0-{len(PROXIES)-1})")
            
            # Auto-assign next available proxy with strict one-to-one binding
            assigned_proxies = set(assignments.values())
            available_proxies = [p for p in PROXIES if p not in assigned_proxies]
            
            if not available_proxies:
                raise Exception("No available proxies left for assignment. All proxies are bound to accounts.")
            
            # Assign the first available proxy with strict binding
            proxy = available_proxies[0]
            assignments[account_username] = proxy
            
            if self.save_assignments(assignments):
                return proxy
            else:
                raise Exception("Failed to save proxy assignment")
    
    def get_account_proxy(self, account_username: str) -> Optional[str]:
        """Get the proxy assigned to an account"""
        assignments = self.load_assignments()
        return assignments.get(account_username)
    
    def remove_proxy_assignment(self, account_username: str) -> bool:
        """Remove proxy assignment from an account"""
        with self.lock:
            assignments = self.load_assignments()
            if account_username in assignments:
                del assignments[account_username]
                return self.save_assignments(assignments)
            else:
                # Account doesn't have a proxy assignment
                raise ValueError(f"Account {account_username} does not have a proxy assigned")
    
    def get_all_assignments(self) -> Dict[str, Dict]:
        """Get all proxy assignments with detailed info"""
        assignments = self.load_assignments()
        detailed_assignments = {}
        
        for account, proxy in assignments.items():
            proxy_info = self.parse_proxy(proxy)
            proxy_index = PROXIES.index(proxy) if proxy in PROXIES else -1
            
            detailed_assignments[account] = {
                'proxy': proxy,
                'proxy_index': proxy_index + 1 if proxy_index >= 0 else None,
                'proxy_host': proxy_info['host'] if proxy_info else None,
                'proxy_port': proxy_info['port'] if proxy_info else None,
                'is_valid': proxy in PROXIES
            }
        
        return detailed_assignments
    
    def get_proxy_usage_stats(self) -> Dict:
        """Get statistics about proxy usage"""
        assignments = self.load_assignments()
        assigned_proxies = set(assignments.values())
        
        return {
            'total_proxies': len(PROXIES),
            'assigned_proxies': len(assigned_proxies),
            'available_proxies': len(PROXIES) - len(assigned_proxies),
            'assignments_count': len(assignments),
            'usage_percentage': (len(assigned_proxies) / len(PROXIES)) * 100
        }
    
    def reassign_proxy_to_account(self, account_username: str, new_proxy_string: str) -> str:
        """
        Reassign a specific proxy (by string) to an account with strict binding enforcement
        STRICT RULE: Maintains one-to-one proxy-account binding
        """
        with self.lock:
            if new_proxy_string not in PROXIES:
                raise ValueError(f"Invalid proxy string: {new_proxy_string}")
            
            assignments = self.load_assignments()
            
            # STRICT CHECK: Ensure the new proxy is not assigned to someone else
            assigned_proxies = {acc: prx for acc, prx in assignments.items() if acc != account_username}
            if new_proxy_string in assigned_proxies.values():
                assigned_account = next(
                    (acc for acc, prx in assigned_proxies.items() if prx == new_proxy_string), 
                    None
                )
                raise ValueError(f"STRICT BINDING VIOLATION: Proxy {new_proxy_string} is already assigned to account: {assigned_account}")
            
            # Store old proxy for logging
            old_proxy = assignments.get(account_username, "None")
            
            # Assign the new proxy (this frees up the old proxy automatically)
            assignments[account_username] = new_proxy_string
            
            if self.save_assignments(assignments):
                return new_proxy_string
            else:
                raise Exception("Failed to save proxy reassignment")

    def reassign_proxy(self, account_username: str, new_proxy_index: int) -> str:
        """
        Reassign a different proxy to an account with strict binding enforcement
        STRICT RULE: Maintains one-to-one proxy-account binding
        """
        with self.lock:
            if not (0 <= new_proxy_index < len(PROXIES)):
                raise ValueError(f"Invalid proxy index: {new_proxy_index} (available: 0-{len(PROXIES)-1})")
            
            assignments = self.load_assignments()
            new_proxy = PROXIES[new_proxy_index]
            
            # STRICT CHECK: Ensure the new proxy is not assigned to someone else
            assigned_proxies = {acc: prx for acc, prx in assignments.items() if acc != account_username}
            if new_proxy in assigned_proxies.values():
                assigned_account = next(
                    (acc for acc, prx in assigned_proxies.items() if prx == new_proxy), 
                    None
                )
                raise ValueError(f"STRICT BINDING VIOLATION: Proxy {new_proxy_index + 1} is already assigned to account: {assigned_account}")
            
            # Store old proxy for logging
            old_proxy = assignments.get(account_username, "None")
            
            # Assign the new proxy (this frees up the old proxy automatically)
            assignments[account_username] = new_proxy
            
            if self.save_assignments(assignments):
                return new_proxy
            else:
                raise Exception("Failed to save proxy reassignment")
    
    def get_available_proxy_indices(self) -> List[int]:
        """Get list of available proxy indices"""
        assignments = self.load_assignments()
        assigned_proxies = set(assignments.values())
        available_indices = []
        
        for i, proxy in enumerate(PROXIES):
            if proxy not in assigned_proxies:
                available_indices.append(i)
        
        return available_indices
    
    def validate_strict_binding(self) -> Dict[str, List[str]]:
        """
        Validate that proxy-account binding is strictly one-to-one
        Returns any violations found
        """
        assignments = self.load_assignments()
        violations = {
            'duplicate_proxies': [],
            'invalid_proxies': [],
            'orphaned_accounts': []
        }
        
        # Check for duplicate proxy assignments
        proxy_count = {}
        for account, proxy in assignments.items():
            proxy_count[proxy] = proxy_count.get(proxy, []) + [account]
        
        for proxy, accounts in proxy_count.items():
            if len(accounts) > 1:
                violations['duplicate_proxies'].append(f"Proxy {proxy} assigned to multiple accounts: {accounts}")
        
        # Check for invalid proxies
        for account, proxy in assignments.items():
            if proxy not in PROXIES:
                violations['invalid_proxies'].append(f"Account {account} has invalid proxy: {proxy}")
        
        return violations
    
    def enforce_strict_binding(self) -> bool:
        """
        Enforce strict one-to-one binding by fixing any violations
        Returns True if fixes were applied
        """
        violations = self.validate_strict_binding()
        fixed = False
        
        if violations['duplicate_proxies'] or violations['invalid_proxies']:
            assignments = self.load_assignments()
            
            # Remove all duplicate and invalid assignments
            for account in list(assignments.keys()):
                proxy = assignments[account]
                if proxy not in PROXIES:
                    del assignments[account]
                    fixed = True
            
            # Handle duplicate assignments - keep first, remove others
            assigned_proxies = set()
            for account in list(assignments.keys()):
                proxy = assignments[account]
                if proxy in assigned_proxies:
                    del assignments[account]
                    fixed = True
                else:
                    assigned_proxies.add(proxy)
            
            if fixed:
                self.save_assignments(assignments)
        
        return fixed

# Global instance
proxy_manager = ProxyManager()

# Convenience functions for backward compatibility
def get_account_proxy(username: str) -> Optional[str]:
    """Get proxy assigned to account"""
    return proxy_manager.get_account_proxy(username)

def assign_proxy_to_account(username: str, proxy_index: Optional[int] = None) -> Optional[str]:
    """Assign proxy to account"""
    return proxy_manager.assign_proxy_to_account(username, proxy_index)

def parse_proxy(proxy_string: str) -> Optional[Dict]:
    """Parse proxy string"""
    return proxy_manager.parse_proxy(proxy_string)
