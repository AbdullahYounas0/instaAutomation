"""
Proxy Health Checker
Tests proxy connectivity and assigns better proxies to failed accounts
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from proxy_manager import proxy_manager, PROXIES
from instagram_accounts import get_all_accounts

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class ProxyHealthChecker:
    def __init__(self):
        self.test_results = {}
        self.healthy_proxies = []
        self.failed_proxies = []
    
    async def test_proxy_connectivity(self, proxy_string: str, timeout: int = 10) -> Dict:
        """Test a single proxy's connectivity and response time"""
        result = {
            'proxy': proxy_string,
            'status': 'unknown',
            'response_time': None,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            parsed = proxy_manager.parse_proxy(proxy_string)
            if not parsed:
                result['status'] = 'failed'
                result['error'] = 'Invalid proxy format'
                return result
            
            # Create proxy URL for aiohttp
            proxy_url = f"http://{parsed['username']}:{parsed['password']}@{parsed['host']}:{parsed['port']}"
            
            # Test with Instagram (safe endpoint)
            test_url = "https://httpbin.org/ip"  # Use httpbin instead of Instagram to avoid rate limits
            
            start_time = time.time()
            
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(test_url, proxy=proxy_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        end_time = time.time()
                        
                        result['status'] = 'healthy'
                        result['response_time'] = round(end_time - start_time, 2)
                        result['ip'] = data.get('origin', 'Unknown')
                    else:
                        result['status'] = 'failed'
                        result['error'] = f'HTTP {response.status}'
        
        except asyncio.TimeoutError:
            result['status'] = 'failed'
            result['error'] = 'Connection timeout'
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
        
        return result
    
    async def test_all_proxies(self, log_callback=None) -> Dict:
        """Test all available proxies"""
        if log_callback:
            log_callback(f"Testing {len(PROXIES)} proxies for connectivity...")
        
        tasks = []
        for proxy in PROXIES:
            task = self.test_proxy_connectivity(proxy)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = 0
        failed_count = 0
        
        for result in results:
            if isinstance(result, dict):
                self.test_results[result['proxy']] = result
                
                if result['status'] == 'healthy':
                    self.healthy_proxies.append(result['proxy'])
                    healthy_count += 1
                else:
                    self.failed_proxies.append(result['proxy'])
                    failed_count += 1
        
        # Sort healthy proxies by response time
        self.healthy_proxies.sort(key=lambda p: self.test_results[p].get('response_time', float('inf')))
        
        summary = {
            'total_proxies': len(PROXIES),
            'healthy_proxies': healthy_count,
            'failed_proxies': failed_count,
            'fastest_proxy': self.healthy_proxies[0] if self.healthy_proxies else None,
            'slowest_healthy_proxy': self.healthy_proxies[-1] if self.healthy_proxies else None
        }
        
        if log_callback:
            log_callback(f"✅ Healthy proxies: {healthy_count}/{len(PROXIES)}")
            log_callback(f"❌ Failed proxies: {failed_count}/{len(PROXIES)}")
            if self.healthy_proxies:
                fastest = self.test_results[summary['fastest_proxy']]
                log_callback(f"⚡ Fastest proxy: {fastest['response_time']}s")
        
        return summary
    
    async def reassign_failed_account_proxies(self, log_callback=None) -> Dict:
        """Reassign proxies for accounts that had authentication failures"""
        if not self.healthy_proxies:
            if log_callback:
                log_callback("No healthy proxies available for reassignment")
            return {'reassigned': 0, 'errors': ['No healthy proxies available']}
        
        accounts = get_all_accounts()
        current_assignments = proxy_manager.load_assignments()
        
        reassigned_count = 0
        errors = []
        
        if log_callback:
            log_callback("Checking account proxy assignments...")
        
        for account in accounts:
            username = account['username']
            current_proxy = current_assignments.get(username)
            
            if current_proxy and current_proxy in self.failed_proxies:
                # This account has a failed proxy, reassign to a healthy one
                try:
                    # Find the best available healthy proxy
                    best_proxy = None
                    for proxy in self.healthy_proxies:
                        # Check if proxy is already assigned to another account
                        if proxy not in current_assignments.values():
                            best_proxy = proxy
                            break
                    
                    if best_proxy:
                        # Reassign the proxy
                        proxy_manager.reassign_proxy_to_account(username, best_proxy)
                        reassigned_count += 1
                        
                        response_time = self.test_results[best_proxy].get('response_time', 'Unknown')
                        display_name = username[:8] + "..." if len(username) > 8 else username
                        
                        if log_callback:
                            log_callback(f"🔄 Reassigned {display_name}: {best_proxy} (RT: {response_time}s)")
                    else:
                        errors.append(f"No available healthy proxy for {username}")
                        
                except Exception as e:
                    errors.append(f"Failed to reassign proxy for {username}: {str(e)}")
        
        if log_callback:
            log_callback(f"✅ Reassigned {reassigned_count} accounts to healthy proxies")
            if errors:
                log_callback(f"⚠️ {len(errors)} errors occurred during reassignment")
        
        return {
            'reassigned': reassigned_count,
            'errors': errors
        }
    
    def generate_proxy_report(self) -> str:
        """Generate a detailed proxy health report"""
        report = []
        report.append("="*60)
        report.append("PROXY HEALTH REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"Total proxies tested: {len(self.test_results)}")
        report.append(f"Healthy proxies: {len(self.healthy_proxies)}")
        report.append(f"Failed proxies: {len(self.failed_proxies)}")
        report.append("")
        
        # Healthy proxies (sorted by response time)
        if self.healthy_proxies:
            report.append("HEALTHY PROXIES (sorted by speed):")
            report.append("-" * 40)
            
            for i, proxy in enumerate(self.healthy_proxies[:10], 1):  # Show top 10
                result = self.test_results[proxy]
                parsed = proxy_manager.parse_proxy(proxy)
                host_port = f"{parsed['host']}:{parsed['port']}" if parsed else proxy
                
                report.append(f"{i:2d}. {host_port}")
                report.append(f"    Response time: {result['response_time']}s")
                report.append(f"    IP: {result.get('ip', 'Unknown')}")
                report.append("")
        
        # Failed proxies
        if self.failed_proxies:
            report.append("FAILED PROXIES:")
            report.append("-" * 40)
            
            for proxy in self.failed_proxies:
                result = self.test_results[proxy]
                parsed = proxy_manager.parse_proxy(proxy)
                host_port = f"{parsed['host']}:{parsed['port']}" if parsed else proxy
                
                report.append(f"❌ {host_port}")
                report.append(f"   Error: {result.get('error', 'Unknown error')}")
                report.append("")
        
        return "\n".join(report)

async def main():
    """Main function to run proxy health check"""
    checker = ProxyHealthChecker()
    
    def log_callback(message):
        print(message)
    
    print("Starting proxy health check...")
    
    # Test all proxies
    summary = await checker.test_all_proxies(log_callback)
    
    print("\nReassigning failed account proxies...")
    # Reassign proxies for failed accounts
    reassignment_result = await checker.reassign_failed_account_proxies(log_callback)
    
    # Generate and save report
    report = checker.generate_proxy_report()
    
    # Save to file
    report_filename = f"proxy_health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nDetailed report saved to: {report_filename}")
    print(f"\nSummary:")
    print(f"✅ Healthy proxies: {summary['healthy_proxies']}/{summary['total_proxies']}")
    print(f"🔄 Accounts reassigned: {reassignment_result['reassigned']}")
    
    if summary['fastest_proxy']:
        fastest_time = checker.test_results[summary['fastest_proxy']]['response_time']
        print(f"⚡ Fastest proxy response: {fastest_time}s")

if __name__ == "__main__":
    asyncio.run(main())
