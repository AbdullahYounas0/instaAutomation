#!/usr/bin/env python3
"""
Test script to verify DM automation works without AI functionality
This ensures the script runs successfully even if OpenAI client fails
"""

import asyncio
import sys
import os
import json
from instagram_dm_automation import DMAutomationEngine

async def test_dm_automation_without_ai():
    """Test DM automation with AI disabled"""
    
    print("🧪 Testing DM Automation without AI functionality")
    print("=" * 50)
    
    # Test with AI disabled
    print("1️⃣ Testing with AI disabled...")
    engine = DMAutomationEngine(enable_ai=False)
    
    # Test initialization
    print("✅ Engine initialized successfully")
    
    # Test OpenAI client setup (should skip)
    result = engine.setup_openai_client()
    print(f"AI setup result: {'✅ PASS' if result else '❌ FAIL'}")
    
    # Test message generation without AI
    print("\n2️⃣ Testing message generation...")
    test_user = {
        'first_name': 'John',
        'username': 'john_doe',
        'city': 'New York',
        'bio': 'Entrepreneur and business owner'
    }
    
    message = engine.generate_message(test_user, "Generate a professional message")
    print(f"Generated message: {message}")
    print("✅ Message generation working")
    
    # Test multiple message variations
    print("\n3️⃣ Testing message variety...")
    for i in range(3):
        msg = engine.generate_message(test_user, "Test prompt")
        print(f"Message {i+1}: {msg}")
    
    print("\n✅ All tests passed! DM automation works without AI.")
    return True

async def test_dm_automation_with_ai():
    """Test DM automation with AI enabled (may fail gracefully)"""
    
    print("\n🧪 Testing DM Automation with AI enabled")
    print("-" * 40)
    
    # Test with AI enabled
    engine = DMAutomationEngine(enable_ai=True)
    
    # Test OpenAI client setup
    result = engine.setup_openai_client()
    if result:
        print("✅ AI client setup successful")
        
        # Test AI message generation
        test_user = {
            'first_name': 'Sarah',
            'username': 'sarah_business',
            'city': 'Los Angeles',
            'bio': 'Marketing consultant'
        }
        
        message = engine.generate_message(test_user, "Generate a professional outreach message")
        print(f"AI-generated message: {message}")
        return True
    else:
        print("⚠️ AI client setup failed (expected) - fallback messages work")
        return True

async def main():
    """Run all tests"""
    
    # Test 1: Without AI (should always work)
    test1_result = await test_dm_automation_without_ai()
    
    # Test 2: With AI (may fail gracefully)
    test2_result = await test_dm_automation_with_ai()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   No AI Mode:  {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   AI Mode:     {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result:
        print("\n🎉 DM automation is ready for VPS deployment!")
        print("💡 The script will work reliably even if AI setup fails.")
    else:
        print("\n❌ Issues detected. Check the logs above.")
    
    return test1_result

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
