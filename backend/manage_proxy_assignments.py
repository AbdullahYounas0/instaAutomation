"""
Proxy Assignment Management Utility
Validates and manages strict one-to-one proxy-account bindings
"""

import json
import os
from proxy_manager import proxy_manager
from instagram_accounts import get_all_account_usernames

def validate_all_proxy_assignments():
    """Validate all proxy assignments and report any issues"""
    print("🔍 Validating all proxy assignments...")
    
    # Check for strict binding violations
    violations = proxy_manager.validate_strict_binding()
    
    if any(violations.values()):
        print("❌ STRICT BINDING VIOLATIONS FOUND:")
        
        if violations['duplicate_proxies']:
            print("\n🚨 DUPLICATE PROXY ASSIGNMENTS:")
            for violation in violations['duplicate_proxies']:
                print(f"   - {violation}")
        
        if violations['invalid_proxies']:
            print("\n🚨 INVALID PROXY ASSIGNMENTS:")
            for violation in violations['invalid_proxies']:
                print(f"   - {violation}")
        
        if violations['orphaned_accounts']:
            print("\n🚨 ORPHANED ACCOUNTS:")
            for violation in violations['orphaned_accounts']:
                print(f"   - {violation}")
        
        return False
    else:
        print("✅ All proxy assignments are valid and follow strict one-to-one binding")
        return True

def auto_assign_missing_proxies():
    """Auto-assign proxies to accounts that don't have one"""
    print("🔄 Auto-assigning proxies to accounts without assignments...")
    
    try:
        all_accounts = get_all_account_usernames()
        assigned_count = 0
        
        for username in all_accounts:
            try:
                existing_proxy = proxy_manager.get_account_proxy(username)
                if not existing_proxy:
                    proxy = proxy_manager.assign_proxy_to_account(username)
                    if proxy:
                        proxy_info = proxy_manager.parse_proxy(proxy)
                        print(f"✅ Assigned proxy {proxy_info['host']}:{proxy_info['port']} to {username}")
                        assigned_count += 1
                    else:
                        print(f"❌ Failed to assign proxy to {username}")
                else:
                    proxy_info = proxy_manager.parse_proxy(existing_proxy)
                    print(f"✓ {username} already has proxy {proxy_info['host']}:{proxy_info['port']}")
            except Exception as e:
                print(f"❌ Error processing {username}: {e}")
        
        print(f"\n📊 Auto-assigned {assigned_count} new proxies")
        return assigned_count > 0
        
    except Exception as e:
        print(f"❌ Error during auto-assignment: {e}")
        return False

def show_proxy_usage_stats():
    """Display proxy usage statistics"""
    print("📊 Proxy Usage Statistics:")
    
    stats = proxy_manager.get_proxy_usage_stats()
    print(f"   Total Proxies: {stats['total_proxies']}")
    print(f"   Assigned Proxies: {stats['assigned_proxies']}")
    print(f"   Available Proxies: {stats['available_proxies']}")
    print(f"   Usage Percentage: {stats['usage_percentage']:.1f}%")
    
    assignments = proxy_manager.get_all_assignments()
    print(f"   Total Account Assignments: {len(assignments)}")

def show_all_assignments():
    """Show all current proxy assignments"""
    print("📋 Current Proxy Assignments:")
    
    assignments = proxy_manager.get_all_assignments()
    
    if not assignments:
        print("   No proxy assignments found")
        return
    
    for account, info in assignments.items():
        proxy_host = info.get('proxy_host', 'Unknown')
        proxy_port = info.get('proxy_port', 'Unknown')
        proxy_index = info.get('proxy_index', 'Unknown')
        is_valid = info.get('is_valid', False)
        
        status = "✅" if is_valid else "❌"
        print(f"   {status} {account} → {proxy_host}:{proxy_port} (Index: {proxy_index})")

def enforce_strict_binding():
    """Enforce strict proxy binding by fixing violations"""
    print("🔧 Enforcing strict proxy binding...")
    
    fixed = proxy_manager.enforce_strict_binding()
    
    if fixed:
        print("✅ Fixed proxy binding violations")
    else:
        print("✓ No violations found to fix")
    
    return fixed

def main():
    """Main function to run proxy management utilities"""
    print("🛡️ Instagram Automation - Proxy Assignment Management")
    print("=" * 60)
    
    # Show current stats
    show_proxy_usage_stats()
    print()
    
    # Validate current assignments
    is_valid = validate_all_proxy_assignments()
    print()
    
    # Fix any violations
    if not is_valid:
        enforce_strict_binding()
        print()
    
    # Auto-assign missing proxies
    auto_assign_missing_proxies()
    print()
    
    # Show final assignments
    show_all_assignments()
    print()
    
    # Final validation
    print("🔍 Final Validation:")
    final_valid = validate_all_proxy_assignments()
    
    if final_valid:
        print("\n🎉 All proxy assignments are now properly configured!")
        print("✅ Strict one-to-one proxy-account binding is enforced")
    else:
        print("\n⚠️ Some issues remain - manual intervention may be required")

if __name__ == "__main__":
    main()
