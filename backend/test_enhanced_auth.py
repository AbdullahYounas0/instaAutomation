#!/usr/bin/env python3
"""
Test Script for Enhanced Instagram Authentication System
Tests all components of the new cookie-based authentication with proxy support
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List

from instagram_auth_helper import auth_helper
from instagram_cookie_manager import cookie_manager
from instagram_accounts import get_account_details, instagram_accounts_manager
from proxy_manager import proxy_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_enhanced_auth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedAuthTester:
    def __init__(self):
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        logger.log(getattr(logging, level, logging.INFO), message)
    
    async def test_cookie_manager(self) -> Dict:
        """Test cookie manager functionality"""
        self.log("🍪 Testing Cookie Manager...")
        
        test_result = {
            'component': 'cookie_manager',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # Test 1: Save cookies
            self.log("  📝 Test 1: Save cookies")
            test_cookies = [
                {
                    'name': 'sessionid',
                    'value': 'test_session_12345',
                    'domain': '.instagram.com',
                    'path': '/',
                    'secure': True,
                    'httpOnly': True
                },
                {
                    'name': 'csrftoken',
                    'value': 'test_csrf_67890',
                    'domain': '.instagram.com',
                    'path': '/',
                    'secure': True
                }
            ]
            
            test_proxy_info = {
                'host': '127.0.0.1',
                'port': '8080',
                'proxy_string': '127.0.0.1:8080:user:pass'
            }
            
            save_success = cookie_manager.save_cookies('test_user', test_cookies, test_proxy_info)
            test_result['tests']['save_cookies'] = save_success
            
            if save_success:
                self.log("    ✅ Cookies saved successfully")
            else:
                self.log("    ❌ Failed to save cookies")
                test_result['overall_success'] = False
            
            # Test 2: Load cookies
            self.log("  📖 Test 2: Load cookies")
            loaded_data = cookie_manager.load_cookies('test_user')
            load_success = loaded_data is not None and len(loaded_data.get('cookies', [])) == 2
            test_result['tests']['load_cookies'] = load_success
            
            if load_success:
                self.log("    ✅ Cookies loaded successfully")
                self.log(f"    📊 Loaded {len(loaded_data['cookies'])} cookies")
            else:
                self.log("    ❌ Failed to load cookies")
                test_result['overall_success'] = False
            
            # Test 3: Validate cookies
            self.log("  ✅ Test 3: Validate cookies")
            are_valid = cookie_manager.are_cookies_valid('test_user')
            test_result['tests']['validate_cookies'] = are_valid
            
            if are_valid:
                self.log("    ✅ Cookies are valid")
            else:
                self.log("    ❌ Cookies validation failed")
                test_result['overall_success'] = False
            
            # Test 4: Get stored accounts
            self.log("  📋 Test 4: Get stored accounts")
            stored_accounts = cookie_manager.get_all_stored_accounts()
            get_accounts_success = isinstance(stored_accounts, list)
            test_result['tests']['get_stored_accounts'] = get_accounts_success
            
            if get_accounts_success:
                self.log(f"    ✅ Found {len(stored_accounts)} stored accounts")
            else:
                self.log("    ❌ Failed to get stored accounts")
                test_result['overall_success'] = False
            
            # Test 5: Cleanup
            self.log("  🧹 Test 5: Delete test cookies")
            delete_success = cookie_manager.delete_cookies('test_user')
            test_result['tests']['delete_cookies'] = delete_success
            
            if delete_success:
                self.log("    ✅ Test cookies deleted")
            else:
                self.log("    ❌ Failed to delete test cookies")
        
        except Exception as e:
            error_msg = f"Error testing cookie manager: {str(e)}"
            self.log(error_msg, "ERROR")
            test_result['errors'].append(error_msg)
            test_result['overall_success'] = False
        
        return test_result
    
    async def test_proxy_manager(self) -> Dict:
        """Test proxy manager functionality"""
        self.log("🌐 Testing Proxy Manager...")
        
        test_result = {
            'component': 'proxy_manager',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # Test 1: Get available proxies
            self.log("  📋 Test 1: Get available proxies")
            all_proxies = proxy_manager.get_all_proxies()
            get_proxies_success = isinstance(all_proxies, list) and len(all_proxies) > 0
            test_result['tests']['get_all_proxies'] = get_proxies_success
            
            if get_proxies_success:
                self.log(f"    ✅ Found {len(all_proxies)} available proxies")
            else:
                self.log("    ❌ No proxies available")
                test_result['overall_success'] = False
            
            # Test 2: Parse proxy string
            self.log("  🔍 Test 2: Parse proxy string")
            if all_proxies:
                test_proxy = all_proxies[0]
                parsed = proxy_manager.parse_proxy(test_proxy)
                parse_success = parsed is not None and 'host' in parsed
                test_result['tests']['parse_proxy'] = parse_success
                
                if parse_success:
                    self.log(f"    ✅ Parsed proxy: {parsed['host']}:{parsed['port']}")
                else:
                    self.log("    ❌ Failed to parse proxy")
                    test_result['overall_success'] = False
            
            # Test 3: Get proxy assignments
            self.log("  📊 Test 3: Get proxy assignments")
            assignments = proxy_manager.get_all_assignments()
            get_assignments_success = isinstance(assignments, dict)
            test_result['tests']['get_assignments'] = get_assignments_success
            
            if get_assignments_success:
                self.log(f"    ✅ Found {len(assignments)} proxy assignments")
            else:
                self.log("    ❌ Failed to get proxy assignments")
                test_result['overall_success'] = False
            
            # Test 4: Get usage stats
            self.log("  📈 Test 4: Get usage statistics")
            stats = proxy_manager.get_proxy_usage_stats()
            stats_success = isinstance(stats, dict) and 'total_proxies' in stats
            test_result['tests']['get_stats'] = stats_success
            
            if stats_success:
                self.log(f"    ✅ Stats: {stats['assigned_proxies']}/{stats['total_proxies']} proxies assigned ({stats['usage_percentage']:.1f}%)")
            else:
                self.log("    ❌ Failed to get usage stats")
                test_result['overall_success'] = False
        
        except Exception as e:
            error_msg = f"Error testing proxy manager: {str(e)}"
            self.log(error_msg, "ERROR")
            test_result['errors'].append(error_msg)
            test_result['overall_success'] = False
        
        return test_result
    
    async def test_account_manager(self) -> Dict:
        """Test account manager functionality"""
        self.log("👤 Testing Account Manager...")
        
        test_result = {
            'component': 'account_manager',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # Test 1: Get all accounts
            self.log("  📋 Test 1: Get all accounts")
            accounts = instagram_accounts_manager.get_all_accounts()
            get_accounts_success = isinstance(accounts, list)
            test_result['tests']['get_all_accounts'] = get_accounts_success
            
            if get_accounts_success:
                self.log(f"    ✅ Found {len(accounts)} Instagram accounts")
            else:
                self.log("    ❌ Failed to get accounts")
                test_result['overall_success'] = False
            
            # Test 2: Get active accounts
            self.log("  🎯 Test 2: Get active accounts")
            active_accounts = instagram_accounts_manager.get_active_accounts()
            get_active_success = isinstance(active_accounts, list)
            test_result['tests']['get_active_accounts'] = get_active_success
            
            if get_active_success:
                self.log(f"    ✅ Found {len(active_accounts)} active accounts")
            else:
                self.log("    ❌ Failed to get active accounts")
                test_result['overall_success'] = False
            
            # Test 3: Test get_account_details function
            self.log("  🔍 Test 3: Get account details")
            if active_accounts:
                test_username = active_accounts[0]['username']
                account_details = get_account_details(test_username)
                details_success = account_details is not None
                test_result['tests']['get_account_details'] = details_success
                
                if details_success:
                    self.log(f"    ✅ Retrieved details for {test_username}")
                    self.log(f"    📊 Has proxy: {account_details.get('has_proxy', False)}")
                else:
                    self.log(f"    ❌ Failed to get details for {test_username}")
                    test_result['overall_success'] = False
        
        except Exception as e:
            error_msg = f"Error testing account manager: {str(e)}"
            self.log(error_msg, "ERROR")
            test_result['errors'].append(error_msg)
            test_result['overall_success'] = False
        
        return test_result
    
    async def test_auth_helper(self) -> Dict:
        """Test authentication helper functionality"""
        self.log("🔐 Testing Authentication Helper...")
        
        test_result = {
            'component': 'auth_helper',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # Get a test account
            accounts = instagram_accounts_manager.get_active_accounts()
            
            if not accounts:
                self.log("    ⚠️ No accounts available for testing")
                test_result['tests']['no_accounts_available'] = True
                test_result['overall_success'] = False
                return test_result
            
            test_username = accounts[0]['username']
            self.log(f"    🎯 Using test account: {test_username}")
            
            # Test 1: Quick login check
            self.log("  🔍 Test 1: Quick login check")
            login_status = await auth_helper.quick_login_check(test_username, self.log)
            quick_check_success = isinstance(login_status, dict) and 'username' in login_status
            test_result['tests']['quick_login_check'] = quick_check_success
            
            if quick_check_success:
                self.log(f"    ✅ Login check completed")
                self.log(f"    📊 Has cookies: {login_status['has_valid_cookies']}")
                self.log(f"    📊 Has proxy: {login_status['has_proxy']}")
                self.log(f"    📊 Ready: {login_status['estimated_ready']}")
            else:
                self.log("    ❌ Quick login check failed")
                test_result['overall_success'] = False
            
            # Test 2: System status
            self.log("  📊 Test 2: Get system status")
            system_status = auth_helper.get_system_status()
            status_success = isinstance(system_status, dict) and 'active_contexts' in system_status
            test_result['tests']['get_system_status'] = status_success
            
            if status_success:
                self.log("    ✅ System status retrieved")
                self.log(f"    📊 Active contexts: {system_status['active_contexts']}")
                self.log(f"    📊 Stored cookies: {system_status['stored_cookie_accounts']}")
            else:
                self.log("    ❌ Failed to get system status")
                test_result['overall_success'] = False
            
            # Test 3: Cleanup expired data
            self.log("  🧹 Test 3: Cleanup expired data")
            cleanup_result = await auth_helper.cleanup_expired_data(self.log)
            cleanup_success = isinstance(cleanup_result, dict)
            test_result['tests']['cleanup_expired_data'] = cleanup_success
            
            if cleanup_success:
                self.log("    ✅ Cleanup completed")
                if 'cleaned_cookie_files' in cleanup_result:
                    self.log(f"    📊 Cleaned {cleanup_result['cleaned_cookie_files']} cookie files")
            else:
                self.log("    ❌ Cleanup failed")
                test_result['overall_success'] = False
        
        except Exception as e:
            error_msg = f"Error testing auth helper: {str(e)}"
            self.log(error_msg, "ERROR")
            test_result['errors'].append(error_msg)
            test_result['overall_success'] = False
        
        return test_result
    
    async def test_bulk_authentication_check(self) -> Dict:
        """Test bulk authentication checking"""
        self.log("🔍 Testing Bulk Authentication Check...")
        
        test_result = {
            'component': 'bulk_auth_check',
            'tests': {},
            'overall_success': True,
            'errors': []
        }
        
        try:
            # Get some test usernames
            accounts = instagram_accounts_manager.get_all_accounts()
            test_usernames = [acc['username'] for acc in accounts[:5]]  # Test first 5
            
            if not test_usernames:
                self.log("    ⚠️ No accounts available for bulk testing")
                test_result['tests']['no_accounts_available'] = True
                return test_result
            
            self.log(f"    🎯 Testing {len(test_usernames)} accounts: {', '.join(test_usernames)}")
            
            # Perform bulk check
            bulk_result = await auth_helper.bulk_authentication_check(test_usernames, self.log)
            
            bulk_success = isinstance(bulk_result, dict) and 'summary' in bulk_result
            test_result['tests']['bulk_check'] = bulk_success
            
            if bulk_success:
                summary = bulk_result['summary']
                self.log("    ✅ Bulk authentication check completed")
                self.log(f"    📊 Total accounts: {summary['total_accounts']}")
                self.log(f"    📊 Ready accounts: {summary['ready_accounts']}")
                self.log(f"    📊 Success rate: {summary['estimated_success_rate']:.1f}%")
                
                # Show individual results
                for username, result in bulk_result['individual_results'].items():
                    status = "✅ Ready" if result.get('estimated_ready') else "⚠️ Needs setup"
                    self.log(f"      {username}: {status}")
            else:
                self.log("    ❌ Bulk authentication check failed")
                test_result['overall_success'] = False
        
        except Exception as e:
            error_msg = f"Error testing bulk auth check: {str(e)}"
            self.log(error_msg, "ERROR")
            test_result['errors'].append(error_msg)
            test_result['overall_success'] = False
        
        return test_result
    
    async def run_all_tests(self) -> Dict:
        """Run all test suites"""
        self.log("🚀 Starting Enhanced Authentication System Tests")
        self.log("=" * 60)
        
        start_time = datetime.now()
        
        # Run all test suites
        test_suites = [
            ('Cookie Manager', self.test_cookie_manager),
            ('Proxy Manager', self.test_proxy_manager),
            ('Account Manager', self.test_account_manager),
            ('Auth Helper', self.test_auth_helper),
            ('Bulk Auth Check', self.test_bulk_authentication_check),
        ]
        
        results = {}
        overall_success = True
        
        for suite_name, test_func in test_suites:
            self.log(f"\n🔍 Running {suite_name} tests...")
            try:
                result = await test_func()
                results[suite_name] = result
                
                if result['overall_success']:
                    self.log(f"✅ {suite_name} tests passed")
                else:
                    self.log(f"❌ {suite_name} tests failed")
                    overall_success = False
                    
                    # Show errors
                    for error in result.get('errors', []):
                        self.log(f"    💥 {error}")
                        
            except Exception as e:
                error_msg = f"Fatal error in {suite_name}: {str(e)}"
                self.log(error_msg, "ERROR")
                results[suite_name] = {
                    'component': suite_name.lower().replace(' ', '_'),
                    'tests': {},
                    'overall_success': False,
                    'errors': [error_msg]
                }
                overall_success = False
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Final summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        passed_suites = sum(1 for result in results.values() if result['overall_success'])
        total_suites = len(results)
        
        self.log(f"⏱️  Total test duration: {duration:.2f} seconds")
        self.log(f"📈 Test suites passed: {passed_suites}/{total_suites}")
        self.log(f"🎯 Overall success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        # Component-by-component breakdown
        for suite_name, result in results.items():
            status = "✅ PASS" if result['overall_success'] else "❌ FAIL"
            test_count = len(result['tests'])
            passed_tests = sum(1 for test_result in result['tests'].values() if test_result)
            
            self.log(f"  {suite_name}: {status} ({passed_tests}/{test_count} tests)")
        
        return {
            'overall_success': overall_success,
            'suite_results': results,
            'summary': {
                'total_suites': total_suites,
                'passed_suites': passed_suites,
                'duration_seconds': duration,
                'timestamp': start_time.isoformat()
            }
        }
    
    def save_test_results(self, results: Dict, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.log(f"📁 Test results saved to {filename}")
        except Exception as e:
            self.log(f"❌ Failed to save test results: {e}", "ERROR")

async def main():
    """Main test execution"""
    tester = EnhancedAuthTester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Save results
        tester.save_test_results(results)
        
        # Exit with appropriate code
        exit_code = 0 if results['overall_success'] else 1
        
        if results['overall_success']:
            tester.log("\n🎉 All tests passed! Enhanced authentication system is ready to use.")
        else:
            tester.log("\n💥 Some tests failed. Please review the errors above.")
        
        return exit_code
        
    except KeyboardInterrupt:
        tester.log("\n⛔ Tests interrupted by user")
        return 130
    except Exception as e:
        tester.log(f"\n💥 Fatal error during testing: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)