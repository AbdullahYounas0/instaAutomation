#!/usr/bin/env python3
"""
Assign Proxy Script
Assign proxies to Instagram accounts
"""

from proxy_manager import proxy_manager

def assign_proxy():
    """Assign proxy to account"""
    account_username = "paulpmoorenoco09f"
    
    try:
        # Assign first available proxy (index 0)
        proxy = proxy_manager.assign_proxy_to_account(account_username, proxy_index=0)
        print(f"[SUCCESS] Assigned proxy to {account_username}")
        print(f"   Proxy: {proxy}")
        
        # Show proxy details
        proxy_info = proxy_manager.parse_proxy(proxy)
        if proxy_info:
            print(f"   Host: {proxy_info['host']}")
            print(f"   Port: {proxy_info['port']}")
            print(f"   Username: {proxy_info['username']}")
        
        # Show all assignments
        assignments = proxy_manager.get_all_assignments()
        print(f"\n[ASSIGNMENTS] All Assignments:")
        for account, details in assignments.items():
            print(f"   {account}: Proxy #{details['proxy_index']} ({details['proxy_host']}:{details['proxy_port']})")
        
        # Show usage stats
        stats = proxy_manager.get_proxy_usage_stats()
        print(f"\n[STATS] Proxy Usage Stats:")
        print(f"   Total proxies: {stats['total_proxies']}")
        print(f"   Assigned: {stats['assigned_proxies']}")
        print(f"   Available: {stats['available_proxies']}")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    assign_proxy()