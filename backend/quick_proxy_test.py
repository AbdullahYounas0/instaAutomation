#!/usr/bin/env python3
"""
Quick Proxy Test Script
Fast test for proxy connectivity - tests only with requests library for speed
"""

import requests
import time
from proxy_manager import proxy_manager
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class QuickProxyTester:
    def __init__(self):
        self.timeout = 10
        self.test_url = 'http://httpbin.org/ip'
        
    def test_single_proxy_quick(self, proxy_data):
        """Quick test for a single proxy"""
        index, proxy_string = proxy_data
        
        try:
            # Parse the proxy string first
            parsed = proxy_manager.parse_proxy(proxy_string)
            if not parsed:
                return {
                    'index': index,
                    'proxy_url': proxy_string,
                    'success': False,
                    'ip': None,
                    'response_time': 0,
                    'error': f'Failed to parse: {proxy_string[:50]}...'
                }
            
            # Construct proper proxy URL for requests library
            proxy_url = f"http://{parsed['username']}:{parsed['password']}@{parsed['host']}:{parsed['port']}"
            proxies = {'http': proxy_url, 'https': proxy_url}
            
            start_time = time.time()
            
            # Use HTTP endpoint to avoid SSL issues
            test_urls = [
                'http://httpbin.org/ip',
                'http://icanhazip.com',
                'http://api.ipify.org?format=json'
            ]
            
            success = False
            last_error = None
            
            for test_url in test_urls:
                try:
                    response = requests.get(
                        test_url,
                        proxies=proxies,
                        timeout=self.timeout,
                        verify=False,  # Disable SSL verification
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        try:
                            if 'json' in test_url:
                                data = response.json()
                                ip = data.get('ip', data.get('origin', 'Unknown'))
                            else:
                                ip = response.text.strip()
                            
                            return {
                                'index': index,
                                'proxy_url': proxy_string,
                                'success': True,
                                'ip': ip,
                                'response_time': response_time,
                                'error': None,
                                'test_url': test_url
                            }
                        except:
                            return {
                                'index': index,
                                'proxy_url': proxy_string,
                                'success': True,
                                'ip': f'Connected - {response.text[:20]}...' if response.text else 'Connected',
                                'response_time': response_time,
                                'error': None,
                                'test_url': test_url
                            }
                    else:
                        last_error = f'HTTP {response.status_code}'
                        
                except requests.exceptions.ProxyError as e:
                    last_error = 'Proxy Connection Error'
                except requests.exceptions.Timeout:
                    last_error = f'Timeout ({self.timeout}s)'
                except requests.exceptions.SSLError:
                    last_error = 'SSL Error'
                except Exception as e:
                    last_error = str(e)[:50] + '...' if len(str(e)) > 50 else str(e)
            
            # If we reach here, all test URLs failed
            return {
                'index': index,
                'proxy_url': proxy_string,
                'success': False,
                'ip': None,
                'response_time': time.time() - start_time,
                'error': last_error or 'All test URLs failed'
            }
                
        except Exception as e:
            return {
                'index': index,
                'proxy_url': proxy_string,
                'success': False,
                'ip': None,
                'response_time': 0,
                'error': str(e)[:50] + '...' if len(str(e)) > 50 else str(e)
            }

    def test_all_proxies_concurrent(self, max_proxies=None, max_workers=5):
        """Test all proxies concurrently for speed"""
        all_proxies = proxy_manager.get_all_proxies()
        
        if max_proxies:
            proxies_to_test = all_proxies[:max_proxies]
        else:
            proxies_to_test = all_proxies
        
        print(f"🚀 QUICK PROXY TEST - Testing {len(proxies_to_test)} proxies")
        print(f"⏰ Timeout: {self.timeout}s per proxy")
        print(f"🔀 Concurrent workers: {max_workers}")
        print(f"📡 Test URL: {self.test_url}")
        print("-" * 80)
        
        # Prepare data for concurrent testing
        proxy_data = [(i, proxy_string) for i, proxy_string in enumerate(proxies_to_test)]
        
        results = []
        
        # Use ThreadPoolExecutor for concurrent testing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_proxy = {
                executor.submit(self.test_single_proxy_quick, data): data 
                for data in proxy_data
            }
            
            # Process completed tasks
            for future in as_completed(future_to_proxy):
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Print result immediately
                    self.print_single_result(result)
                    
                except Exception as e:
                    proxy_data = future_to_proxy[future]
                    print(f"❌ Proxy {proxy_data[0] + 1}: Exception during test - {str(e)[:50]}...")
        
        # Sort results by index
        results.sort(key=lambda x: x['index'])
        
        self.print_summary(results)
        return results

    def print_single_result(self, result):
        """Print result for a single proxy"""
        index = result['index'] + 1
        parsed = proxy_manager.parse_proxy(result['proxy_url'])
        host = parsed['host'] if parsed else 'Unknown'
        port = parsed['port'] if parsed else 'Unknown'
        
        if result['success']:
            print(f"✅ Proxy {index:2d}: {host}:{port} - {result['ip']} ({result['response_time']:.2f}s)")
        else:
            print(f"❌ Proxy {index:2d}: {host}:{port} - {result['error']} ({result['response_time']:.2f}s)")

    def print_summary(self, results):
        """Print summary of all tests"""
        print("\n" + "="*80)
        print("📊 QUICK TEST SUMMARY")
        print("="*80)
        
        working = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"\n✅ WORKING PROXIES: {len(working)}/{len(results)} ({len(working)/len(results)*100:.1f}%)")
        if working:
            avg_time = sum(r['response_time'] for r in working) / len(working)
            fastest = min(working, key=lambda x: x['response_time'])
            print(f"   Average Response Time: {avg_time:.2f}s")
            print(f"   Fastest Proxy: #{fastest['index'] + 1} ({fastest['response_time']:.2f}s)")
        
        print(f"\n❌ FAILED PROXIES: {len(failed)}/{len(results)} ({len(failed)/len(results)*100:.1f}%)")
        
        # Error breakdown
        if failed:
            error_counts = {}
            for r in failed:
                error = r['error'] or 'Unknown Error'
                error_counts[error] = error_counts.get(error, 0) + 1
            
            print(f"\n🔍 ERROR BREAKDOWN:")
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {error}: {count} proxies")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if len(working) >= 2:
            print("   ✅ You have working proxies! Instagram automation should work.")
        elif len(working) == 1:
            print("   ⚠️  Only 1 working proxy. Consider getting more for better reliability.")
        else:
            print("   ❌ No working proxies found. Check your proxy credentials or provider.")
            print("   🔧 Consider:")
            print("      - Verifying proxy credentials with your provider")
            print("      - Checking if your IP is whitelisted")
            print("      - Testing with different proxy servers")

def main():
    print("⚡ QUICK PROXY CONNECTIVITY TEST")
    print("=" * 50)
    
    tester = QuickProxyTester()
    
    if len(sys.argv) > 1:
        try:
            max_proxies = int(sys.argv[1])
            results = tester.test_all_proxies_concurrent(max_proxies=max_proxies)
        except ValueError:
            print("Invalid number. Testing all proxies...")
            results = tester.test_all_proxies_concurrent()
    else:
        print("Usage: python quick_proxy_test.py [max_proxies]")
        print("Example: python quick_proxy_test.py 5")
        print("\nTesting first 5 proxies by default...\n")
        results = tester.test_all_proxies_concurrent(max_proxies=5)

    # Show working proxy indices for easy assignment
    working_proxies = [r for r in results if r['success']]
    if working_proxies:
        print(f"\n🎯 WORKING PROXY INDICES (for proxy assignment):")
        for r in working_proxies:
            parsed = proxy_manager.parse_proxy(r['proxy_url'])
            host = parsed['host'] if parsed else 'Unknown'
            print(f"   Index {r['index']}: {host} ({r['response_time']:.2f}s)")

if __name__ == "__main__":
    main()
