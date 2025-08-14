"""
Advanced Stealth Browser Manager for Instagram Automation
Implements comprehensive anti-detection measures to avoid banning
"""

import os
import json
import asyncio
import random
import socket
import requests
from typing import Dict, Optional, List, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from proxy_manager import proxy_manager, parse_proxy
import logging

# US-focused timezone mapping for American proxy locations
US_TIMEZONE_MAP = {
    # Eastern Time Zone
    'New York': 'America/New_York',
    'Philadelphia': 'America/New_York',
    'Atlanta': 'America/New_York',
    'Miami': 'America/New_York',
    'Boston': 'America/New_York',
    'Washington': 'America/New_York',
    'Detroit': 'America/New_York',
    'Charlotte': 'America/New_York',
    'Jacksonville': 'America/New_York',
    'Baltimore': 'America/New_York',
    
    # Central Time Zone
    'Chicago': 'America/Chicago',
    'Houston': 'America/Chicago',
    'San Antonio': 'America/Chicago',
    'Dallas': 'America/Chicago',
    'Austin': 'America/Chicago',
    'Fort Worth': 'America/Chicago',
    'Oklahoma City': 'America/Chicago',
    'Memphis': 'America/Chicago',
    'Milwaukee': 'America/Chicago',
    'Kansas City': 'America/Chicago',
    'Nashville': 'America/Chicago',
    'New Orleans': 'America/Chicago',
    
    # Mountain Time Zone
    'Phoenix': 'America/Phoenix',
    'Denver': 'America/Denver',
    'Salt Lake City': 'America/Denver',
    'Las Vegas': 'America/Los_Angeles',  # Nevada follows Pacific time
    'Albuquerque': 'America/Denver',
    'Colorado Springs': 'America/Denver',
    'Mesa': 'America/Phoenix',
    'Tucson': 'America/Phoenix',
    
    # Pacific Time Zone
    'Los Angeles': 'America/Los_Angeles',
    'San Diego': 'America/Los_Angeles',
    'San Jose': 'America/Los_Angeles',
    'San Francisco': 'America/Los_Angeles',
    'Seattle': 'America/Los_Angeles',
    'Portland': 'America/Los_Angeles',
    'Sacramento': 'America/Los_Angeles',
    'Long Beach': 'America/Los_Angeles',
    'Oakland': 'America/Los_Angeles',
    'Fresno': 'America/Los_Angeles'
}

# Coordinates for major US cities (lat, lon)
US_CITY_COORDINATES = {
    # Eastern Time Zone
    'New York': (40.7128, -74.0060),
    'Philadelphia': (39.9526, -75.1652),
    'Atlanta': (33.7490, -84.3880),
    'Miami': (25.7617, -80.1918),
    'Boston': (42.3601, -71.0589),
    'Washington': (38.9072, -77.0369),
    'Detroit': (42.3314, -83.0458),
    'Charlotte': (35.2271, -80.8431),
    'Jacksonville': (30.3322, -81.6557),
    'Baltimore': (39.2904, -76.6122),
    
    # Central Time Zone
    'Chicago': (41.8781, -87.6298),
    'Houston': (29.7604, -95.3698),
    'San Antonio': (29.4241, -98.4936),
    'Dallas': (32.7767, -96.7970),
    'Austin': (30.2672, -97.7431),
    'Fort Worth': (32.7555, -97.3308),
    'Oklahoma City': (35.4676, -97.5164),
    'Memphis': (35.1495, -90.0490),
    'Milwaukee': (43.0389, -87.9065),
    'Kansas City': (39.0997, -94.5786),
    'Nashville': (36.1627, -86.7816),
    'New Orleans': (29.9511, -90.0715),
    
    # Mountain Time Zone
    'Phoenix': (33.4484, -112.0740),
    'Denver': (39.7392, -104.9903),
    'Salt Lake City': (40.7608, -111.8910),
    'Las Vegas': (36.1699, -115.1398),
    'Albuquerque': (35.0844, -106.6504),
    'Colorado Springs': (38.8339, -104.8214),
    'Mesa': (33.4152, -111.8315),
    'Tucson': (32.2226, -110.9747),
    
    # Pacific Time Zone
    'Los Angeles': (34.0522, -118.2437),
    'San Diego': (32.7157, -117.1611),
    'San Jose': (37.3382, -121.8863),
    'San Francisco': (37.7749, -122.4194),
    'Seattle': (47.6062, -122.3321),
    'Portland': (45.5152, -122.6784),
    'Sacramento': (38.5816, -121.4944),
    'Long Beach': (33.7701, -118.1937),
    'Oakland': (37.8044, -122.2712),
    'Fresno': (36.7378, -119.7871)
}

class StealthBrowserManager:
    def __init__(self, account_username: str):
        self.account_username = account_username
        self.user_data_dir = os.path.join("browser_profiles", account_username)
        self.proxy_config = None
        self.proxy_location = None
        
        # US-focused defaults (since all proxies are American)
        self.timezone = 'America/New_York'  # Eastern Time default
        self.coordinates = (40.7128, -74.0060)  # NYC coordinates default
        self.locale = 'en-US'  # US English
        
        # Ensure user data directory exists
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        # Load or generate stable fingerprints
        self.fingerprints = self._load_or_generate_fingerprints()
        
    def _get_us_state_from_city(self, city: str) -> str:
        """Get US state abbreviation from city name"""
        us_state_map = {
            # Eastern Time Zone
            'New York': 'NY', 'Philadelphia': 'PA', 'Atlanta': 'GA', 'Miami': 'FL',
            'Boston': 'MA', 'Washington': 'DC', 'Detroit': 'MI', 'Charlotte': 'NC',
            'Jacksonville': 'FL', 'Baltimore': 'MD',
            
            # Central Time Zone  
            'Chicago': 'IL', 'Houston': 'TX', 'San Antonio': 'TX', 'Dallas': 'TX',
            'Austin': 'TX', 'Fort Worth': 'TX', 'Oklahoma City': 'OK', 'Memphis': 'TN',
            'Milwaukee': 'WI', 'Kansas City': 'MO', 'Nashville': 'TN', 'New Orleans': 'LA',
            
            # Mountain Time Zone
            'Phoenix': 'AZ', 'Denver': 'CO', 'Salt Lake City': 'UT', 'Las Vegas': 'NV',
            'Albuquerque': 'NM', 'Colorado Springs': 'CO', 'Mesa': 'AZ', 'Tucson': 'AZ',
            
            # Pacific Time Zone
            'Los Angeles': 'CA', 'San Diego': 'CA', 'San Jose': 'CA', 'San Francisco': 'CA',
            'Seattle': 'WA', 'Portland': 'OR', 'Sacramento': 'CA', 'Long Beach': 'CA',
            'Oakland': 'CA', 'Fresno': 'CA'
        }
        return us_state_map.get(city, 'NY')  # Default to NY
        
    def _load_or_generate_fingerprints(self) -> Dict:
        """Load existing fingerprints or generate new stable ones"""
        fingerprint_file = os.path.join(self.user_data_dir, "fingerprints.json")
        
        if os.path.exists(fingerprint_file):
            try:
                with open(fingerprint_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Generate new stable fingerprints optimized for US users
        fingerprints = {
            'screen': {
                # Common US screen resolutions
                'width': random.choice([1920, 1366, 1536, 1440, 1600, 2560]),
                'height': random.choice([1080, 768, 864, 900, 1200, 1440]),
                'colorDepth': 24,
                'pixelDepth': 24
            },
            'canvas_fp': self._generate_canvas_fingerprint(),
            'webgl_fp': self._generate_webgl_fingerprint(),
            'audio_fp': self._generate_audio_fingerprint(),
            'user_agent': self._generate_user_agent(),
            'plugins': self._generate_plugins(),
            'languages': ['en-US', 'en'],  # US English priority
            'platform': 'Win32',  # Windows is most common in US
            'hardware_concurrency': random.choice([4, 8, 12, 16, 20, 24])  # Modern US systems
        }
        
        # Save fingerprints
        try:
            with open(fingerprint_file, 'w') as f:
                json.dump(fingerprints, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save fingerprints: {e}")
        
        return fingerprints
    
    def _generate_canvas_fingerprint(self) -> str:
        """Generate a stable canvas fingerprint"""
        # Generate a consistent hash based on account username
        import hashlib
        hash_obj = hashlib.md5(self.account_username.encode())
        return hash_obj.hexdigest()[:16]
    
    def _generate_webgl_fingerprint(self) -> Dict:
        """Generate stable WebGL fingerprint"""
        return {
            'vendor': 'Google Inc. (Intel)',
            'renderer': 'ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'extensions': [
                'ANGLE_instanced_arrays', 'EXT_blend_minmax', 'EXT_color_buffer_half_float',
                'EXT_disjoint_timer_query', 'EXT_float_blend', 'EXT_frag_depth'
            ]
        }
    
    def _generate_audio_fingerprint(self) -> str:
        """Generate stable audio fingerprint"""
        import hashlib
        hash_obj = hashlib.md5(f"audio_{self.account_username}".encode())
        return hash_obj.hexdigest()[:12]
    
    def _generate_user_agent(self) -> str:
        """Generate realistic user agent for US users"""
        # Latest Chrome versions popular in the US
        chrome_versions = [
            '122.0.0.0', '123.0.0.0', '124.0.0.0', '125.0.0.0', 
            '126.0.0.0', '127.0.0.0', '128.0.0.0'
        ]
        webkit_version = '537.36'
        
        chrome_version = random.choice(chrome_versions)
        
        # US-focused Windows versions (most common in US)
        windows_versions = [
            'Windows NT 10.0; Win64; x64',  # Windows 10/11 64-bit (most common)
            'Windows NT 10.0; WOW64',       # Windows 10 32-bit on 64-bit
        ]
        
        windows_version = random.choice(windows_versions)
        
        return f"Mozilla/5.0 ({windows_version}) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}"
    
    def _generate_plugins(self) -> List[Dict]:
        """Generate realistic plugin list"""
        return [
            {'name': 'Chrome PDF Plugin', 'filename': 'internal-pdf-viewer'},
            {'name': 'Chrome PDF Viewer', 'filename': 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
            {'name': 'Native Client', 'filename': 'internal-nacl-plugin'}
        ]
    
    def _detect_proxy_location(self) -> str:
        """Detect proxy location and return US city (simplified for US-only proxies)"""
        if not self.proxy_config:
            return 'New York'  # Default to NYC
        
        try:
            # Extract IP from proxy config
            proxy_ip = self.proxy_config.get('server', '').replace('http://', '').split(':')[0]
            
            # Use a geolocation service to detect city within US
            response = requests.get(f'http://ip-api.com/json/{proxy_ip}', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    country = data.get('countryCode', 'US')
                    city = data.get('city', 'New York')
                    
                    # If it's not US (unlikely), default to New York
                    if country != 'US':
                        logging.warning(f"Non-US proxy detected ({country}), defaulting to New York")
                        return 'New York'
                    
                    # Return the detected US city
                    return city
        except Exception as e:
            logging.warning(f"Failed to detect proxy location: {e}")
        
        return 'New York'  # Default fallback
    
    def _setup_proxy_environment(self):
        """Setup environment based on US proxy location"""
        city = self._detect_proxy_location()
        
        # Set timezone based on US city
        if city in US_TIMEZONE_MAP:
            self.timezone = US_TIMEZONE_MAP[city]
        else:
            # Default to Eastern Time for unknown US cities
            self.timezone = 'America/New_York'
            logging.info(f"Unknown US city '{city}', defaulting to Eastern Time")
        
        # Set coordinates for the US city
        if city in US_CITY_COORDINATES:
            self.coordinates = US_CITY_COORDINATES[city]
        else:
            # Default to NYC coordinates for unknown cities
            self.coordinates = (40.7128, -74.0060)
            logging.info(f"Unknown US city '{city}', defaulting to NYC coordinates")
        
        # Always use US English locale since all proxies are US-based
        self.locale = 'en-US'
        
        # Get state information for more detailed logging
        state = self._get_us_state_from_city(city)
        
        logging.info(f"US proxy environment: {city}, {state}, timezone: {self.timezone}, locale: {self.locale}")
        logging.info(f"Coordinates: {self.coordinates}")
        
        # Log timezone info for debugging
        from datetime import datetime
        try:
            import pytz
            tz = pytz.timezone(self.timezone)
            current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
            logging.info(f"Current time in {city}, {state}: {current_time}")
        except ImportError:
            logging.info(f"pytz not available, skipping timezone validation")
        except Exception as e:
            logging.warning(f"Could not get timezone info: {e}")
    
    async def create_stealth_browser(self) -> Tuple[Browser, BrowserContext]:
        """Create a stealth browser with full anti-detection measures"""
        
        # Get proxy for this account
        proxy_string = proxy_manager.get_account_proxy(self.account_username)
        if proxy_string:
            proxy_info = parse_proxy(proxy_string)
            if proxy_info:
                self.proxy_config = {
                    'server': proxy_info['server'],
                    'username': proxy_info['username'],
                    'password': proxy_info['password']
                }
                logging.info(f"Using proxy for {self.account_username}: {proxy_info['host']}:{proxy_info['port']}")
        
        # Setup environment based on proxy location
        self._setup_proxy_environment()
        
        playwright = await async_playwright().start()
        
        # Advanced stealth browser arguments
        browser_args = [
            # Basic stealth
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            
            # WebRTC & DNS security
            '--disable-webrtc',
            '--disable-webrtc-multiple-routes',
            '--disable-webrtc-hw-decoding',
            '--disable-webrtc-hw-encoding',
            '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
            
            # Additional stealth
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-gpu',
            '--disable-gpu-compositing',
            '--disable-accelerated-2d-canvas',
            '--disable-accelerated-video-decode',
            
            # Performance and detection avoidance
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--mute-audio',
            '--disable-logging',
            '--disable-permissions-api',
            '--ignore-certificate-errors',
            '--allow-running-insecure-content',
            '--disable-component-extensions-with-background-pages',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-default-browser-check',
            '--disable-background-networking'
        ]
        
        try:
            # Use launch_persistent_context for user data directory support
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                proxy=self.proxy_config,
                args=browser_args,
                slow_mo=random.randint(100, 300),  # Random delay for human-like behavior
                user_agent=self.fingerprints['user_agent'],
                viewport={
                    'width': self.fingerprints['screen']['width'],
                    'height': self.fingerprints['screen']['height']
                },
                java_script_enabled=True,
                locale=self.locale,
                timezone_id=self.timezone,
                geolocation={'latitude': self.coordinates[0], 'longitude': self.coordinates[1]},
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept-Language': f"{self.locale},en;q=0.9",
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            # Get the browser instance from the context
            browser = context.browser
            
            # Inject comprehensive stealth scripts
            await self._inject_stealth_scripts(context)
            
            # Set default timeouts
            context.set_default_timeout(120000)  # 2 minutes
            context.set_default_navigation_timeout(120000)
            
            return browser, context
            
        except Exception as e:
            logging.error(f"Failed to create stealth browser for {self.account_username}: {e}")
            raise
    
    async def _inject_stealth_scripts(self, context: BrowserContext):
        """Inject comprehensive stealth scripts to avoid detection"""
        
        stealth_script = f"""
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined
        }});
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {{
            get: () => {json.dumps(self.fingerprints['plugins'])}
        }});
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {{
            get: () => {json.dumps(self.fingerprints['languages'])}
        }});
        
        // Override hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {self.fingerprints['hardware_concurrency']}
        }});
        
        // Override platform
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{self.fingerprints['platform']}'
        }});
        
        // Chrome runtime
        window.chrome = {{
            runtime: {{
                onConnect: undefined,
                onMessage: undefined
            }}
        }};
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
        );
        
        // Canvas fingerprint protection
        const canvas_fp = '{self.fingerprints['canvas_fp']}';
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(...args) {{
            const result = originalToDataURL.apply(this, args);
            return result + canvas_fp;
        }};
        
        // WebGL fingerprint protection
        const webgl_fp = {json.dumps(self.fingerprints['webgl_fp'])};
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return webgl_fp.vendor;
            if (parameter === 37446) return webgl_fp.renderer;
            return getParameter.apply(this, arguments);
        }};
        
        // Audio fingerprint protection  
        const audio_fp = '{self.fingerprints['audio_fp']}';
        const originalGetChannelData = AudioBuffer.prototype.getChannelData;
        AudioBuffer.prototype.getChannelData = function(...args) {{
            const result = originalGetChannelData.apply(this, args);
            // Slightly modify audio data to create consistent fingerprint
            for (let i = 0; i < result.length; i += 100) {{
                result[i] = result[i] + parseFloat('0.00000' + audio_fp.charCodeAt(i % audio_fp.length));
            }}
            return result;
        }};
        
        // Screen properties
        Object.defineProperty(screen, 'width', {{
            get: () => {self.fingerprints['screen']['width']}
        }});
        Object.defineProperty(screen, 'height', {{
            get: () => {self.fingerprints['screen']['height']}
        }});
        Object.defineProperty(screen, 'colorDepth', {{
            get: () => {self.fingerprints['screen']['colorDepth']}
        }});
        
        // Timezone consistency
        const originalDateTimeFormat = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {{
            const options = args[1] || {{}};
            options.timeZone = options.timeZone || '{self.timezone}';
            return new originalDateTimeFormat(args[0], options);
        }};
        
        // Geolocation consistency
        const originalGetCurrentPosition = navigator.geolocation.getCurrentPosition;
        navigator.geolocation.getCurrentPosition = function(success, error, options) {{
            success({{
                coords: {{
                    latitude: {self.coordinates[0]},
                    longitude: {self.coordinates[1]},
                    accuracy: 100,
                    altitude: null,
                    altitudeAccuracy: null,
                    heading: null,
                    speed: null
                }},
                timestamp: Date.now()
            }});
        }};
        
        // Remove automation indicators
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """
        
        await context.add_init_script(stealth_script)
        
        logging.info(f"Injected stealth scripts for {self.account_username}")

# Global function for backward compatibility
async def create_stealth_browser_for_account(account_username: str) -> Tuple[Browser, BrowserContext]:
    """Create a stealth browser for a specific account"""
    manager = StealthBrowserManager(account_username)
    return await manager.create_stealth_browser()

# Convenience function to ensure proxy-account binding
def ensure_proxy_assignment(account_username: str) -> bool:
    """Ensure account has a proxy assigned"""
    try:
        existing_proxy = proxy_manager.get_account_proxy(account_username)
        if not existing_proxy:
            # Auto-assign next available proxy
            proxy_manager.assign_proxy_to_account(account_username)
            logging.info(f"Auto-assigned proxy to {account_username}")
        return True
    except Exception as e:
        logging.error(f"Failed to ensure proxy assignment for {account_username}: {e}")
        return False
