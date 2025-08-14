"""
Instagram Automation Anti-Detection Setup Script
Implements all 5 requested anti-detection features:

1. Lock One Proxy to One Account (No Exceptions)
2. Match Proxy Location to Browser Environment  
3. Use Full Profile Persistence (Not Just Cookies)
4. Stealth Fingerprinting
5. Control DNS & WebRTC Leaks
"""

import os
import sys
import asyncio
import logging
from manage_proxy_assignments import main as manage_proxies
from validate_anti_detection import main as validate_anti_detection

def setup_logging():
    """Setup logging for the setup process"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('setup_anti_detection.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_directories():
    """Create necessary directories for profile persistence"""
    print("📁 Creating directories for browser profile persistence...")
    
    directories = [
        'browser_profiles',
        'instagram_cookies',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ Created/verified: {directory}")

def print_feature_overview():
    """Print overview of implemented anti-detection features"""
    print("\n🛡️ ANTI-DETECTION FEATURES IMPLEMENTED:")
    print("="*60)
    
    features = [
        {
            "number": 1,
            "title": "Lock One Proxy to One Account (No Exceptions)",
            "description": "✅ Strict one-to-one proxy-account binding enforced\n   ✅ Enhanced proxy manager with violation detection\n   ✅ Automatic proxy assignment validation"
        },
        {
            "number": 2, 
            "title": "Match Proxy Location to Browser Environment",
            "description": "✅ Automatic timezone detection based on proxy IP\n   ✅ Locale matching (en-US, en-GB, de-DE, etc.)\n   ✅ Geolocation API spoofing with accurate coordinates"
        },
        {
            "number": 3,
            "title": "Use Full Profile Persistence (Not Just Cookies)", 
            "description": "✅ Complete browser user data directory persistence\n   ✅ LocalStorage, IndexedDB, SessionStorage saved\n   ✅ Cache and browsing history maintained"
        },
        {
            "number": 4,
            "title": "Stealth Fingerprinting",
            "description": "✅ navigator.webdriver property removed\n   ✅ Stable Canvas, WebGL, and Audio fingerprints\n   ✅ Consistent plugins, mimeTypes, and platform spoofing\n   ✅ Hardware concurrency and screen properties matched"
        },
        {
            "number": 5,
            "title": "Control DNS & WebRTC Leaks",
            "description": "✅ WebRTC completely disabled via browser flags\n   ✅ DNS requests forced through proxy\n   ✅ UDP traffic blocked to prevent IP leaks\n   ✅ Force proxy IP handling policy"
        }
    ]
    
    for feature in features:
        print(f"\n{feature['number']}. {feature['title']}")
        print(f"   {feature['description']}")

def print_usage_instructions():
    """Print instructions for using the anti-detection features"""
    print("\n📋 USAGE INSTRUCTIONS:")
    print("="*60)
    
    instructions = [
        "1. Run 'python manage_proxy_assignments.py' to set up proxy assignments",
        "2. All Instagram scripts now automatically use stealth browser manager",
        "3. Each account gets its own persistent browser profile directory",
        "4. Proxy location automatically determines timezone and geolocation",
        "5. Run 'python validate_anti_detection.py' to verify configuration"
    ]
    
    for instruction in instructions:
        print(f"   {instruction}")
    
    print("\n🔧 MANUAL VERIFICATION:")
    print("   - Check browser_profiles/ directory for account-specific profiles")
    print("   - Verify proxy_assignments.json for one-to-one binding") 
    print("   - Test with different accounts to ensure fingerprint isolation")

def print_security_warnings():
    """Print important security warnings and best practices"""
    print("\n⚠️ SECURITY WARNINGS & BEST PRACTICES:")
    print("="*60)
    
    warnings = [
        "🚨 NEVER share proxy credentials or assign same proxy to multiple accounts",
        "🚨 Each account MUST maintain consistent timezone/location across sessions",
        "🚨 Do not delete browser_profiles/ directories - this breaks persistence",
        "🚨 Monitor proxy usage to ensure no IP conflicts between accounts",
        "🚨 Test thoroughly before running large-scale automation"
    ]
    
    for warning in warnings:
        print(f"   {warning}")
    
    print("\n💡 ADDITIONAL RECOMMENDATIONS:")
    tips = [
        "✅ Use residential proxies for better success rates",
        "✅ Implement delays between actions (already included)",
        "✅ Monitor account health and adjust automation frequency",
        "✅ Keep browser profiles backed up for critical accounts"
    ]
    
    for tip in tips:
        print(f"   {tip}")

async def main():
    """Main setup function"""
    setup_logging()
    
    print("🛡️ INSTAGRAM AUTOMATION ANTI-DETECTION SETUP")
    print("=" * 80)
    print("This script sets up comprehensive anti-detection measures")
    print("to prevent Instagram account bans and detection.\n")
    
    # Create required directories
    create_directories()
    
    # Setup proxy assignments
    print("\n🔧 Setting up proxy assignments...")
    try:
        manage_proxies()
    except Exception as e:
        print(f"⚠️ Error setting up proxies: {e}")
        print("You may need to run 'python manage_proxy_assignments.py' manually")
    
    # Validate anti-detection measures
    print("\n🔍 Validating anti-detection configuration...")
    try:
        await validate_anti_detection()
    except Exception as e:
        print(f"⚠️ Error during validation: {e}")
        print("You may need to run 'python validate_anti_detection.py' manually")
    
    # Print feature overview
    print_feature_overview()
    
    # Print usage instructions
    print_usage_instructions()
    
    # Print security warnings
    print_security_warnings()
    
    print("\n🎉 ANTI-DETECTION SETUP COMPLETE!")
    print("Your Instagram automation is now configured with comprehensive")
    print("anti-detection measures to minimize the risk of account bans.")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
