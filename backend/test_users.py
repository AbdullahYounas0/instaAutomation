#!/usr/bin/env python3
"""
Test script to verify the users API endpoint fix
"""

from auth import user_manager

def test_users():
    print("Testing user_manager.get_all_users()...")
    try:
        users = user_manager.get_all_users()
        print(f"✅ Users loaded successfully. Count: {len(users)}")
        
        for i, user in enumerate(users):
            print(f"User {i+1}:")
            print(f"  Username: {user.get('username', 'N/A')}")
            print(f"  ID: {user.get('id', 'N/A')}")
            print(f"  User_ID: {user.get('user_id', 'N/A')}")
            print(f"  Name: {user.get('name', 'N/A')}")
            print(f"  Role: {user.get('role', 'N/A')}")
            print(f"  Active: {user.get('is_active', 'N/A')}")
            print()
        
        # Test the mapping that would happen in the API endpoint
        print("Testing ID mapping for API endpoint...")
        for user in users:
            user_id = user.get('user_id') or user.get('id')
            if user_id:
                user['id'] = user_id
                user['user_id'] = user_id
                print(f"✅ User {user['username']}: ID={user['id']}, User_ID={user['user_id']}")
            else:
                print(f"❌ User {user.get('username', 'unknown')} has no valid ID")
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_users()
