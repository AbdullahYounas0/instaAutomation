#!/usr/bin/env python3
"""
Cleanup orphaned proxy assignments
Removes proxy assignments for accounts that no longer exist
"""

import json
import os

def cleanup_orphaned_proxy_assignments():
    """Remove proxy assignments for deleted Instagram accounts"""
    
    # Read Instagram accounts
    try:
        with open('backend/instagram_accounts.json', 'r') as f:
            accounts = json.load(f)
        existing_usernames = {acc['username'] for acc in accounts}
        print(f"Found {len(existing_usernames)} existing Instagram accounts")
    except FileNotFoundError:
        existing_usernames = set()
        print("No Instagram accounts file found")
    
    # Read proxy assignments
    try:
        with open('backend/proxy_assignments.json', 'r') as f:
            proxy_assignments = json.load(f)
        print(f"Found {len(proxy_assignments)} proxy assignments")
    except FileNotFoundError:
        print("No proxy assignments file found")
        return
    
    # Find orphaned assignments
    orphaned_accounts = []
    for username in proxy_assignments.keys():
        if username not in existing_usernames:
            orphaned_accounts.append(username)
    
    if not orphaned_accounts:
        print("✅ No orphaned proxy assignments found")
        return
    
    print(f"🧹 Found {len(orphaned_accounts)} orphaned proxy assignments:")
    for username in orphaned_accounts:
        proxy = proxy_assignments[username]
        print(f"  - {username} -> {proxy}")
    
    # Remove orphaned assignments
    cleaned_assignments = {
        username: proxy for username, proxy in proxy_assignments.items()
        if username in existing_usernames
    }
    
    # Save cleaned assignments
    with open('backend/proxy_assignments.json', 'w') as f:
        json.dump(cleaned_assignments, f, indent=2)
    
    print(f"✅ Cleaned up {len(orphaned_accounts)} orphaned proxy assignments")
    print(f"📊 Remaining assignments: {len(cleaned_assignments)}")
    
    if cleaned_assignments:
        print("Remaining valid assignments:")
        for username, proxy in cleaned_assignments.items():
            host_port = proxy.split(':')[:2]
            print(f"  - {username} -> {':'.join(host_port)}")

if __name__ == "__main__":
    print("Proxy Assignment Cleanup Script")
    print("=" * 40)
    cleanup_orphaned_proxy_assignments()
