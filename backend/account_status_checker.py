"""
Account Status Checker
Checks authentication status and provides troubleshooting guidance for failed accounts
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from instagram_accounts import get_all_accounts
from proxy_manager import proxy_manager
from enhanced_instagram_auth import enhanced_auth
from stealth_browser_manager import StealthBrowserManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class AccountStatusChecker:
    def __init__(self):
        self.results = {}
    
    async def check_all_accounts(self, log_callback=None) -> Dict:
        """Check status of all accounts"""
        accounts = get_all_accounts()
        results = {
            'total_accounts': len(accounts),
            'successful_logins': 0,
            'failed_logins': 0,
            'proxy_issues': 0,
            'credential_issues': 0,
            'suspension_issues': 0,
            'network_issues': 0,
            'details': {}
        }
        
        if log_callback:
            log_callback(f"Starting status check for {len(accounts)} accounts...")
        
        for account in accounts:
            username = account['username']
            display_name = username[:8] + "..." if len(username) > 8 else username
            
            if log_callback:
                log_callback(f"Checking {display_name}...")
            
            account_result = await self.check_single_account(username, account['password'], log_callback)
            results['details'][username] = account_result
            
            # Update counters
            if account_result['status'] == 'success':
                results['successful_logins'] += 1
            else:
                results['failed_logins'] += 1
                
                # Categorize failure types
                if 'proxy' in account_result.get('issue_type', '').lower():
                    results['proxy_issues'] += 1
                elif 'credential' in account_result.get('issue_type', '').lower():
                    results['credential_issues'] += 1
                elif 'suspend' in account_result.get('issue_type', '').lower():
                    results['suspension_issues'] += 1
                elif 'network' in account_result.get('issue_type', '').lower():
                    results['network_issues'] += 1
        
        # Generate summary report
        if log_callback:
            log_callback(f"\n📊 ACCOUNT STATUS SUMMARY:")
            log_callback(f"✅ Successful logins: {results['successful_logins']}/{results['total_accounts']}")
            log_callback(f"❌ Failed logins: {results['failed_logins']}/{results['total_accounts']}")
            if results['failed_logins'] > 0:
                log_callback(f"   🌐 Proxy issues: {results['proxy_issues']}")
                log_callback(f"   🔑 Credential issues: {results['credential_issues']}")
                log_callback(f"   🚫 Suspension issues: {results['suspension_issues']}")
                log_callback(f"   📡 Network issues: {results['network_issues']}")
        
        return results
    
    async def check_single_account(self, username: str, password: str, log_callback=None) -> Dict:
        """Check a single account's authentication status"""
        result = {
            'username': username,
            'status': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'proxy_assigned': False,
            'proxy_working': False,
            'authentication_method': None,
            'issue_type': None,
            'recommendations': [],
            'errors': []
        }
        
        browser = None
        context = None
        
        try:
            # Check proxy assignment
            proxy_string = proxy_manager.get_account_proxy(username)
            if proxy_string:
                result['proxy_assigned'] = True
                parsed_proxy = proxy_manager.parse_proxy(proxy_string)
                if parsed_proxy:
                    result['proxy_working'] = True
            else:
                result['recommendations'].append("Assign a proxy to this account")
            
            # Create stealth browser
            try:
                stealth_manager = StealthBrowserManager(username)
                browser, context = await stealth_manager.create_stealth_browser()
            except Exception as e:
                result['status'] = 'failed'
                result['issue_type'] = 'browser_setup'
                result['errors'].append(f"Browser setup failed: {str(e)}")
                result['recommendations'].append("Check proxy configuration and network connectivity")
                return result
            
            # Attempt authentication
            def auth_log_callback(message):
                if log_callback:
                    # Only log important messages to avoid spam
                    if any(keyword in message.lower() for keyword in ['failed', 'success', 'error', 'timeout', 'suspend']):
                        log_callback(f"  {message}")
            
            success, auth_info = await enhanced_auth.authenticate_with_cookies_and_proxy(
                context=context,
                username=username,
                password=password,
                log_callback=auth_log_callback
            )
            
            if success:
                result['status'] = 'success'
                result['authentication_method'] = auth_info.get('authentication_method')
                
                # Check for account suspension
                page = context.pages[0] if context.pages else None
                if page:
                    current_url = page.url.lower()
                    if "suspended" in current_url or "accounts/suspended" in current_url:
                        result['status'] = 'failed'
                        result['issue_type'] = 'account_suspended'
                        result['recommendations'].append("Account is suspended - contact Instagram support")
            else:
                result['status'] = 'failed'
                result['errors'] = auth_info.get('errors', [])
                
                # Analyze error types and provide recommendations
                error_text = ' '.join(result['errors']).lower()
                
                if 'timeout' in error_text or 'navigation' in error_text:
                    result['issue_type'] = 'network_timeout'
                    result['recommendations'].extend([
                        "Check internet connection stability",
                        "Consider changing proxy server",
                        "Verify proxy server is responsive"
                    ])
                elif 'credential' in error_text or 'invalid' in error_text or 'incorrect' in error_text:
                    result['issue_type'] = 'credential_issue'
                    result['recommendations'].extend([
                        "Verify username and password are correct",
                        "Check if account password was changed",
                        "Ensure account is not locked"
                    ])
                elif 'proxy' in error_text:
                    result['issue_type'] = 'proxy_issue'
                    result['recommendations'].extend([
                        "Check proxy server status",
                        "Try assigning a different proxy",
                        "Verify proxy credentials"
                    ])
                elif 'suspend' in error_text:
                    result['issue_type'] = 'account_suspended'
                    result['recommendations'].append("Account appears to be suspended")
                else:
                    result['issue_type'] = 'unknown_error'
                    result['recommendations'].append("Manual investigation required")
        
        except Exception as e:
            result['status'] = 'failed'
            result['issue_type'] = 'system_error'
            result['errors'].append(f"System error: {str(e)}")
            result['recommendations'].append("Check system logs and configuration")
        
        finally:
            try:
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except:
                pass
        
        return result
    
    def generate_troubleshooting_report(self, results: Dict) -> str:
        """Generate a detailed troubleshooting report"""
        report = []
        report.append("="*60)
        report.append("INSTAGRAM ACCOUNT STATUS REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"Total accounts checked: {results['total_accounts']}")
        report.append(f"Successful logins: {results['successful_logins']}")
        report.append(f"Failed logins: {results['failed_logins']}")
        report.append("")
        
        if results['failed_logins'] > 0:
            report.append("FAILURE BREAKDOWN:")
            report.append(f"Proxy issues: {results['proxy_issues']}")
            report.append(f"Credential issues: {results['credential_issues']}")
            report.append(f"Suspension issues: {results['suspension_issues']}")
            report.append(f"Network issues: {results['network_issues']}")
            report.append("")
        
        # Detailed account information
        report.append("DETAILED RESULTS:")
        report.append("-" * 40)
        
        for username, details in results['details'].items():
            display_name = username[:12] + "..." if len(username) > 12 else username
            status_emoji = "✅" if details['status'] == 'success' else "❌"
            
            report.append(f"{status_emoji} {display_name}")
            report.append(f"   Status: {details['status']}")
            
            if details['status'] == 'success':
                report.append(f"   Auth method: {details.get('authentication_method', 'Unknown')}")
            else:
                if details.get('issue_type'):
                    report.append(f"   Issue type: {details['issue_type']}")
                if details.get('errors'):
                    report.append(f"   Errors: {'; '.join(details['errors'][:2])}")  # Show first 2 errors
                if details.get('recommendations'):
                    report.append(f"   Recommendations:")
                    for rec in details['recommendations'][:3]:  # Show first 3 recommendations
                        report.append(f"     • {rec}")
            
            report.append("")
        
        return "\n".join(report)

async def main():
    """Main function to run account status check"""
    checker = AccountStatusChecker()
    
    def log_callback(message):
        print(message)
    
    print("Starting Instagram account status check...")
    results = await checker.check_all_accounts(log_callback)
    
    # Generate and save report
    report = checker.generate_troubleshooting_report(results)
    
    # Save to file
    report_filename = f"account_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nDetailed report saved to: {report_filename}")
    print("\nQuick summary:")
    print(report.split("DETAILED RESULTS:")[0])

if __name__ == "__main__":
    asyncio.run(main())
