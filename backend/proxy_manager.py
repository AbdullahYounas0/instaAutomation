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
    "156.237.58.177:8075:silwfmmt:9mnui1h717nw",
    "72.1.138.220:6111:silwfmmt:9mnui1h717nw",
    "136.143.251.205:7404:silwfmmt:9mnui1h717nw",
    "163.123.200.142:6427:silwfmmt:9mnui1h717nw",
    "208.66.73.58:5069:silwfmmt:9mnui1h717nw",
    "46.203.3.115:8114:silwfmmt:9mnui1h717nw",
    "66.43.6.242:8113:silwfmmt:9mnui1h717nw",
    "69.30.75.24:6081:silwfmmt:9mnui1h717nw",
    "72.1.156.235:8125:silwfmmt:9mnui1h717nw",
    "156.237.54.82:7977:silwfmmt:9mnui1h717nw",
    "45.56.157.181:6404:silwfmmt:9mnui1h717nw",
    "192.53.68.50:5108:silwfmmt:9mnui1h717nw",
    "208.72.211.251:7036:silwfmmt:9mnui1h717nw",
    "207.228.28.217:7866:silwfmmt:9mnui1h717nw",
    "156.237.42.124:8023:silwfmmt:9mnui1h717nw",
    "46.203.104.5:7502:silwfmmt:9mnui1h717nw",
    "154.194.25.13:5031:silwfmmt:9mnui1h717nw",
    "207.228.32.142:6759:silwfmmt:9mnui1h717nw",
    "46.203.54.224:8222:silwfmmt:9mnui1h717nw",
    "207.228.14.23:5315:silwfmmt:9mnui1h717nw"
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
        """Parse proxy string into components"""
        try:
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
        Assign a proxy to an Instagram account
        If proxy_index is provided, assign that specific proxy
        If proxy_index is None, assign the next available proxy
        """
        with self.lock:
            assignments = self.load_assignments()
            
            # Check if account already has a proxy assigned
            if account_username in assignments:
                current_proxy = assignments[account_username]
                raise ValueError(f"Account {account_username} already has a proxy assigned. Use reassign instead.")
            
            # If specific proxy index requested
            if proxy_index is not None:
                if 0 <= proxy_index < len(PROXIES):
                    proxy = PROXIES[proxy_index]
                    
                    # Check if this proxy is already assigned
                    assigned_proxies = set(assignments.values())
                    if proxy in assigned_proxies:
                        # Find which account has this proxy
                        assigned_account = next(
                            (acc for acc, prx in assignments.items() if prx == proxy), 
                            None
                        )
                        raise ValueError(f"Proxy {proxy_index + 1} is already assigned to account: {assigned_account}")
                    
                    # Assign the proxy
                    assignments[account_username] = proxy
                    
                    if self.save_assignments(assignments):
                        return proxy
                    else:
                        raise Exception("Failed to save proxy assignment")
                else:
                    raise ValueError(f"Invalid proxy index: {proxy_index} (available: 0-{len(PROXIES)-1})")
            
            # Auto-assign next available proxy
            assigned_proxies = set(assignments.values())
            available_proxies = [p for p in PROXIES if p not in assigned_proxies]
            
            if not available_proxies:
                raise Exception("No available proxies left")
            
            # Assign the first available proxy
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
    
    def reassign_proxy(self, account_username: str, new_proxy_index: int) -> str:
        """Reassign a different proxy to an account"""
        with self.lock:
            if not (0 <= new_proxy_index < len(PROXIES)):
                raise ValueError(f"Invalid proxy index: {new_proxy_index} (available: 0-{len(PROXIES)-1})")
            
            assignments = self.load_assignments()
            new_proxy = PROXIES[new_proxy_index]
            
            # Check if the new proxy is already assigned to someone else
            assigned_proxies = {acc: prx for acc, prx in assignments.items() if acc != account_username}
            if new_proxy in assigned_proxies.values():
                assigned_account = next(
                    (acc for acc, prx in assigned_proxies.items() if prx == new_proxy), 
                    None
                )
                raise ValueError(f"Proxy {new_proxy_index + 1} is already assigned to account: {assigned_account}")
            
            # Assign the new proxy
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
