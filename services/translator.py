import subprocess
import sys
import os
import platform
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
import time
import json
from typing import List, Dict, Union
import requests
import zipfile
import io
import shutil

class RuntimeBrowserSetup:
    """
    Simplified ChromeDriver setup that just uses webdriver-manager properly.
    """
    
    def __init__(self):
        self.chrome_driver_path = None
    
    def install_required_packages(self):
        """Install required Python packages at runtime."""
        required_packages = [
            'selenium',
            'requests',
            'webdriver-manager'
        ]
        
        print("Installing required packages...")
        for package in required_packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ])
                print(f"✓ {package} installed")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to install {package}: {e}")
                raise
    
    def setup_chrome_driver(self):
        """Setup ChromeDriver using webdriver-manager with proper cache directory."""
        try:
            print("Setting up ChromeDriver...")
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.os_manager import ChromeType
            
            # Set cache directory to current working directory to avoid permission issues
            cache_dir = Path.cwd() / "webdriver_cache"
            print("cache_dir: ", cache_dir)
            cache_dir.mkdir(exist_ok=True)
            
            # Force webdriver-manager to use a proper cache folder
            os.environ.pop('WDM_CACHE_PATH', None)  # remove bad env var if set
            os.environ.pop('WDM_LOCAL', None)

            self.chrome_driver_path = ChromeDriverManager().install()

            print(f"✓ ChromeDriver ready at: {self.chrome_driver_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup ChromeDriver with webdriver-manager: {e}")
            # Fallback to system ChromeDriver if available
            return self.try_system_chromedriver()
    
    def try_system_chromedriver(self):
        """Try to use system chromedriver if available."""
        try:
            # Check if chromedriver is in PATH
            result = subprocess.run(['which', 'chromedriver'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.chrome_driver_path = result.stdout.strip()
                print(f"✓ Using system ChromeDriver: {self.chrome_driver_path}")
                return True
            
            # Check common installation locations (cross-platform)
            system = platform.system().lower()
            if system == "darwin":  # macOS
                common_paths = [
                    '/usr/local/bin/chromedriver',
                    '/opt/homebrew/bin/chromedriver',
                    '/Applications/Google Chrome.app/Contents/MacOS/chromedriver'
                ]
            elif system == "linux":  # Ubuntu/Linux
                common_paths = [
                    '/usr/local/bin/chromedriver',
                    '/usr/bin/chromedriver',
                    '/snap/bin/chromedriver',
                    '/home/*/chromedriver'  # User installations
                ]
            else:  # Windows
                common_paths = [
                    'C:\\Windows\\chromedriver.exe',
                    'C:\\Program Files\\chromedriver.exe'
                ]
            
            for path in common_paths:
                if os.path.exists(path):
                    self.chrome_driver_path = path
                    print(f"✓ Found ChromeDriver at: {path}")
                    return True
            
            print("✗ No ChromeDriver found on system")
            return False
            
        except Exception as e:
            print(f"✗ Error checking system ChromeDriver: {e}")
            return False
    
    def get_chrome_driver_service(self):
        """Get Chrome service object."""
        if self.chrome_driver_path:
            return Service(executable_path=self.chrome_driver_path)
        return None

class GoogleTranslateWebService:
    """
    Service class using Google Translate web interface.
    """
    
    def __init__(self, headless: bool = True, wait_timeout: int = 15, typing_delay: float = 0.05, wait_time: int = 5):
        self.wait_timeout = wait_timeout
        self.typing_delay = typing_delay
        self.wait_time = wait_time
        self.driver = None
        self.headless = headless
        self.browser_setup = RuntimeBrowserSetup()
        
        # Setup browser environment
        self._setup_environment()
        self._setup_driver()
    
    def _setup_environment(self):
        """Setup the entire browser environment."""
        try:
            print("=== Setting up browser environment ===")
            
            # Install required packages
            self.browser_setup.install_required_packages()
            
            # Setup ChromeDriver
            if not self.browser_setup.setup_chrome_driver():
                raise Exception("Failed to setup ChromeDriver")
            
            print("✓ Browser environment ready")
            
        except Exception as e:
            print(f"✗ Failed to setup browser environment: {e}")
            raise
    
    def _setup_driver(self):
        """Initialize Chrome driver with essential anti-detection measures."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # Essential Chrome options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Key anti-detection options (keep only essential ones)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Language settings
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_experimental_option('prefs', {
            'intl.accept_languages': 'en-US,en;q=0.9'
        })
        
        # Realistic User-Agent
        system = platform.system().lower()
        if system == "linux":
            user_agent = ("Mozilla/5.0 (X11; Linux x86_64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36")
        elif system == "darwin":
            user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36")
        else:  # Windows
            user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36")
        
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        try:
            service = self.browser_setup.get_chrome_driver_service()
            if service:
                print(f"Using ChromeDriver service")
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Let Selenium handle it automatically
                print("Letting Selenium manage ChromeDriver automatically...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Post-initialization: Remove automation indicators and set headers
            self._setup_stealth_mode()
                
            print("✓ Chrome driver initialized successfully")
            
        except Exception as e:
            print(f"✗ Error initializing Chrome driver: {e}")
            
            # Final fallback: try manual ChromeDriver installation
            print("Trying manual ChromeDriver installation...")
            manual_driver_path = self._install_chromedriver_manually()
            if manual_driver_path:
                try:
                    service = Service(executable_path=manual_driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self._setup_stealth_mode()
                    print("✓ Chrome driver initialized with manual installation")
                except Exception as manual_error:
                    print(f"✗ Manual installation also failed: {manual_error}")
                    raise
            else:
                raise
    
    def _setup_stealth_mode(self):
        """Configure the browser to avoid detection after initialization."""
        try:
            # Remove webdriver property (this is the most important one)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set basic properties to look more like a real browser
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            print("✓ Basic stealth mode configured")
            
        except Exception as e:
            print(f"! Stealth setup warning: {e}")
            # Continue anyway
    
    def _install_chromedriver_manually(self):
        """Manual ChromeDriver installation as last resort."""
        try:
            # Determine the right URL based on system and architecture
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            if system == "darwin":  # macOS
                if 'arm' in machine or 'aarch64' in machine:
                    arch = "mac-arm64"
                else:
                    arch = "mac-x64"
            elif system == "linux":  # Ubuntu/Linux
                if 'arm' in machine or 'aarch64' in machine:
                    arch = "linux-arm64"
                else:
                    arch = "linux64"
            elif system == "windows":  # Windows
                arch = "win64" if "64" in machine else "win32"
            else:
                print(f"✗ Unsupported system: {system}")
                return None
            
            url = f"https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.109/{arch}/chromedriver-{arch}.zip"
            
            print(f"Downloading ChromeDriver for {system}/{machine} from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Create a temporary directory for extraction
            temp_dir = Path("/tmp/chromedriver_temp")
            temp_dir.mkdir(exist_ok=True)
            
            # Extract the zip file
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                zip_file.extractall(temp_dir)
            
            # Find the actual chromedriver executable
            chromedriver_path = None
            executable_name = 'chromedriver.exe' if system == 'windows' else 'chromedriver'
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == executable_name:
                        chromedriver_path = Path(root) / file
                        break
                if chromedriver_path:
                    break
            
            if not chromedriver_path:
                print(f"✗ ChromeDriver executable ({executable_name}) not found in downloaded package")
                return None
            
            # Copy to a consistent location and make executable
            final_name = 'chromedriver_final.exe' if system == 'windows' else 'chromedriver_final'
            final_path = Path("/tmp") / final_name
            shutil.copy2(str(chromedriver_path), str(final_path))
            
            # Make executable (Unix systems only)
            if system != 'windows':
                final_path.chmod(0o755)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            print(f"✓ Manual ChromeDriver installation successful: {final_path}")
            return str(final_path)
            
        except Exception as e:
            print(f"✗ Manual ChromeDriver installation failed: {e}")
            return None
    
    def _navigate_to_translator(self):
        """Navigate to Google Translate with clean approach."""
        try:
            # Direct navigation to Google Translate
            url = "https://google.com"
            print(f"Navigating to: {url}")
            self.driver.get(url)

            time.sleep(2)

            # Direct navigation to Google Translate
            url = "https://translate.google.com/?sl=en&tl=ur&text=&op=translate"
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load completely
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )
            
            # Additional wait for JavaScript to load
            time.sleep(3)
            
            # Verify we're on the right page
            current_url = self.driver.current_url
            if "translate.google.com" in current_url:
                print("✓ Successfully loaded Google Translate")
            else:
                print(f"⚠ Unexpected URL: {current_url}")
            
            # Check for and dismiss any popups
            self._dismiss_popups()
            
        except TimeoutException:
            print("✗ Timeout waiting for Google Translate to load")
            raise
        except Exception as e:
            print(f"✗ Error navigating to translator: {e}")
            raise
    
    def _dismiss_popups(self):
        """Dismiss any cookie banners or popups."""
        popup_selectors = [
            "button[aria-label*='Accept']",
            "button[aria-label*='I agree']", 
            "button[id*='accept']",
            "button[class*='accept']",
            ".gb_g[aria-label='Close']",
            "[data-ved] button"
        ]
        
        for selector in popup_selectors:
            try:
                popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                if popup.is_displayed():
                    popup.click()
                    time.sleep(1)
                    print(f"✓ Dismissed popup with selector: {selector}")
                    break
            except:
                continue
    
    def translate_single(self, text: str) -> str:
        """Translate a single text with human-like behavior."""
        if not text or not text.strip():
            return text
        
        for attempt in range(3):
            try:
                if "translate.google.com" not in self.driver.current_url:
                    self._navigate_to_translator()
                
                # Find the source textarea with more specific selector
                input_selectors = [
                    "textarea[aria-label*='Source text']",
                    "textarea[placeholder*='Enter text']", 
                    "textarea",
                    "[aria-label*='Source text'] textarea"
                ]
                
                input_area = None
                for selector in input_selectors:
                    try:
                        input_area = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if not input_area:
                    raise Exception("Could not find input textarea")
                
                # Clear the input area using multiple methods
                input_area.click()
                time.sleep(0.5)
                
                # Clear using keyboard shortcut (most human-like)
                input_area.send_keys(Keys.CONTROL + "a")  # Select all
                time.sleep(0.3)
                input_area.send_keys(Keys.DELETE)  # Delete
                time.sleep(0.5)
                
                # Also clear using JavaScript as backup
                self.driver.execute_script("arguments[0].value = '';", input_area)
                time.sleep(0.5)
                
                # Type text naturally (simulate human typing)
                words = text.split()
                for i, word in enumerate(words):
                    if i > 0:
                        input_area.send_keys(" ")
                        time.sleep(0.1)
                    
                    for char in word:
                        input_area.send_keys(char)
                        time.sleep(self.typing_delay)
                
                # Wait for Google to process and translate
                time.sleep(self.wait_time)
                
                # Try to find translation with multiple approaches
                translation = self._extract_translation()
                
                if translation and translation != text and len(translation.strip()) > 0:
                    print(f"✓ Successfully translated: {text[:30]}...")
                    return translation
                
                # If first attempt failed, try clicking elsewhere and back
                if attempt < 2:
                    print(f"Attempt {attempt + 1} - trying refresh approach...")
                    try:
                        # Click outside textarea, then back in
                        body = self.driver.find_element(By.TAG_NAME, "body")
                        body.click()
                        time.sleep(1)
                        input_area.click()
                        time.sleep(2)
                        
                        translation = self._extract_translation()
                        if translation and translation != text:
                            return translation
                    except:
                        pass
                    
                    time.sleep(2)
                    continue
                
                return text
                
            except Exception as e:
                if attempt < 2:
                    print(f"Retrying translation (attempt {attempt + 1}): {str(e)[:50]}")
                    time.sleep(3)
                    try:
                        self._navigate_to_translator()
                        time.sleep(2)
                    except:
                        pass
                else:
                    print(f"✗ Failed to translate after all attempts: {str(e)}")
                    return text
        
        return text
    
    def _extract_translation(self) -> str:
        """Extract translation using multiple selectors and methods."""
        translation_selectors = [
            # Main translation area
            "[data-language-code='ur'] span",
            "span[lang='ur']",
            "[data-language-code='ur']",
            
            # Translation result containers
            ".translation span",
            "[jsname='W297wb']",
            ".result-dict-wrapper span",
            
            # General containers that might contain Urdu text
            "[dir='rtl']",
            "*[lang='ur']"
        ]
        
        for selector in translation_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    # Check if text contains Urdu characters
                    if text and self._contains_urdu(text):
                        print(f"✓ Found translation with selector: {selector}")
                        return text
            except:
                continue
        
        # Fallback: look for any RTL text
        try:
            rtl_elements = self.driver.find_elements(By.CSS_SELECTOR, "[dir='rtl']")
            for element in rtl_elements:
                text = element.text.strip()
                if text and self._contains_urdu(text):
                    return text
        except:
            pass
        
        return ""
    
    def _contains_urdu(self, text: str) -> bool:
        """Check if text contains Urdu/Arabic characters."""
        if not text:
            return False
        
        # Unicode range for Arabic/Urdu characters
        urdu_range = range(0x0600, 0x06FF)  # Arabic Unicode block
        urdu_range_2 = range(0xFE70, 0xFEFF)  # Arabic Presentation Forms-B
        
        for char in text:
            char_code = ord(char)
            if char_code in urdu_range or char_code in urdu_range_2:
                return True
        
        return False
    
    def translate_batch(self, texts: List[str]) -> Dict[str, str]:
        """Translate multiple texts."""
        results = {}
        
        try:
            self._navigate_to_translator()
            
            for i, text in enumerate(texts, 1):
                print(f"Translating {i}/{len(texts)}: {text[:50]}...")
                translated = self.translate_single(text)
                results[text] = translated
                time.sleep(1)
        
        except Exception as e:
            print(f"Batch translation error: {str(e)}")
        
        return results
    
    def close(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                print("✓ Browser closed")
            except:
                pass

class AutoTranslator:
    """
    Main translator class.
    """
    
    def __init__(self, headless: bool = True, typing_delay: float = 0, wait_time: int = 5):
        self.service = None
        self.headless = headless
        self.typing_delay = typing_delay  # Delay between characters
        self.wait_time = wait_time  # Wait time after typing
    
    def translate(self, addresses: Union[str, List[str]], slow_mode: bool = False) -> Dict[str, str]:
        """
        Translate addresses.
        
        Args:
            addresses: String or list of strings to translate
            slow_mode: If True, uses even slower typing to mimic human behavior
        """
        try:
            if self.service is None:
                # Pass timing parameters to service
                if slow_mode:
                    self.service = GoogleTranslateWebService(
                        headless=self.headless,
                        typing_delay=0.03,
                        wait_time=8
                    )
                else:
                    self.service = GoogleTranslateWebService(
                        headless=self.headless,
                        typing_delay=self.typing_delay,
                        wait_time=self.wait_time
                    )
            
            if isinstance(addresses, str):
                translated = self.service.translate_single(addresses)
                return {addresses: translated}
            else:
                return self.service.translate_batch(addresses)
            
        except Exception as e:
            print(f"✗ Translation error: {str(e)}")
            if isinstance(addresses, str):
                return {addresses: addresses}
            else:
                return {addr: addr for addr in addresses}
    
    def close(self):
        """Clean up."""
        if self.service:
            self.service.close()

def demo_auto_translation():
    """Demo with automatic setup."""
    translator = AutoTranslator(headless=True)
    
    try:
        addresses = [
            "Mohalla Aminabad, Near Masjid, Jhang Road, Faisalabad",
            "House No 123, Block A, Gulshan Colony, Faisalabad",
            "Shop 45, Main Market, Sargodha Road, Faisalabad",
            "PAK ARFUJI GOODs"
        ]
        
        print("=== Auto-Setup Translation Demo ===\n")
        
        results = translator.translate(addresses)

        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        print("\n=== Results ===")
        for i, (original, translated) in enumerate(results.items(), 1):
            print(f"{i}. Original: {original}")
            print(f"   Translated: {translated}\n")
            
    except Exception as e:
        print(f"Demo error: {e}")
    finally:
        translator.close()

if __name__ == "__main__":
    print("Google Translate Automation")
    print("===========================")
    demo_auto_translation()
