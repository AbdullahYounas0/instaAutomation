#!/usr/bin/env python3
"""
Debug Login Script
Simple script to debug the login process step by step
"""

import asyncio
import sys
from datetime import datetime
from instagram_auth_helper import auth_helper
from instagram_accounts import get_account_details

async def debug_login():
    """Debug the login process step by step"""
    
    username = "paulpmoorenoco09f"
    
    def log(message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}", flush=True)
    
    print("=" * 60)
    print("🔍 DEBUG LOGIN PROCESS")
    print("=" * 60)
    
    try:
        # Get account details first
        account_details = get_account_details(username)
        if not account_details:
            log("❌ No account details found")
            return
        
        log(f"✅ Account details loaded for {username}")
        log(f"   Password: {'***' if account_details.get('password') else 'MISSING'}")
        log(f"   TOTP Secret: {'***' if account_details.get('totp_secret') else 'MISSING'}")
        
        # Test enhanced authentication with detailed logging
        log("🚀 Starting enhanced authentication with debug mode...")
        
        success, context, info = await auth_helper.create_authenticated_context(
            username=username,
            headless=False,  # Keep visible for debugging
            log_callback=log
        )
        
        if success:
            log("🎉 SUCCESS! Authentication completed")
            log(f"📊 Method used: {info.get('authentication_method')}")
            log(f"💾 Cookies saved: {info.get('cookies_saved', False)}")
            
            # Keep browser open longer for debugging
            log("👀 Keeping browser open for 15 seconds for inspection...")
            page = await context.new_page()
            await page.goto("https://www.instagram.com/")
            await asyncio.sleep(15)
            
            # Close context
            await context.close()
            log("🧹 Browser closed")
            
        else:
            log("❌ FAILED! Authentication failed")
            log("📊 Debug Info:")
            for key, value in info.items():
                if key == 'errors':
                    for i, error in enumerate(value, 1):
                        log(f"   Error {i}: {error}")
                else:
                    log(f"   {key}: {value}")
        
    except KeyboardInterrupt:
        log("⛔ Debug interrupted by user")
    except Exception as e:
        log(f"💥 Error during debug: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup any remaining contexts
        await auth_helper.close_all_contexts()
        log("🧹 All contexts cleaned up")

if __name__ == "__main__":
    asyncio.run(debug_login())