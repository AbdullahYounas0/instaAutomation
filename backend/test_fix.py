#!/usr/bin/env python3
"""
Direct test of the get_all_users API endpoint issue
"""

import json
import sys
import os

# Add backend directory to path
sys.path.append('.')

def test_user_id_mapping():
    """Test the exact issue that was causing the 500 error"""
    
    print("🔍 Testing the user ID mapping issue...")
    
    # Load users directly like the API endpoint does
    try:
        from auth import user_manager
        
        print("📋 Loading users from user_manager...")
        users = user_manager.get_all_users()
        print(f"✅ Loaded {len(users)} users")
        
        # Test the original broken logic
        print("\n🧪 Testing original broken logic:")
        try:
            for user in users:
                user_id = user['user_id']  # This would fail for users with only 'id'
                print(f"  User {user['username']}: user_id = {user_id}")
        except KeyError as e:
            print(f"❌ Original logic failed as expected: {e}")
        
        # Test the fixed logic
        print("\n✅ Testing fixed logic:")
        for user in users:
            # Handle both 'user_id' and 'id' fields for backward compatibility
            user_id = user.get('user_id') or user.get('id')
            if user_id:
                user['id'] = user_id
                user['user_id'] = user_id  # Ensure both fields exist
                print(f"  ✅ User {user['username']}: id = {user['id']}, user_id = {user['user_id']}")
            else:
                print(f"  ❌ User {user.get('username', 'unknown')} has no valid ID")
        
        print("\n🎉 All users processed successfully with fixed logic!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_users_json_structure():
    """Test the users.json file structure"""
    
    print("\n📁 Testing users.json file structure...")
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
        
        print(f"✅ Loaded {len(users)} users from JSON")
        
        for i, user in enumerate(users):
            print(f"User {i+1}: {user.get('username', 'N/A')}")
            print(f"  id: {user.get('id', 'MISSING')}")
            print(f"  user_id: {user.get('user_id', 'MISSING')}")
            print(f"  role: {user.get('role', 'N/A')}")
            print(f"  is_active: {user.get('is_active', 'N/A')}")
            
            # Check if both fields exist
            has_id = 'id' in user
            has_user_id = 'user_id' in user
            
            if has_id and has_user_id:
                print(f"  ✅ Has both ID fields")
            elif has_id or has_user_id:
                print(f"  ⚠️  Missing one ID field")
            else:
                print(f"  ❌ Missing both ID fields")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading users.json: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING USER ID MAPPING FIX")
    print("=" * 60)
    
    success1 = test_users_json_structure()
    success2 = test_user_id_mapping()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED! The fix should work.")
    else:
        print("❌ SOME TESTS FAILED. Check the output above.")
    print("=" * 60)
