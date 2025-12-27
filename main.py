from flask import Flask, render_template, jsonify
import random
import string
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time
import os
import sys
import zipfile
import json
import requests

app = Flask(__name__)

# NopeCHA Configuration - MUST BE SET AS ENVIRONMENT VARIABLE
NOPECHA_API_KEY = os.environ.get('NOPECHA_API_KEY')

if not NOPECHA_API_KEY:
    raise ValueError(
        "❌ NOPECHA_API_KEY environment variable is not set!\n"
        "Please set it in Railway or your environment:\n"
        "  Railway: Settings → Variables → Add NOPECHA_API_KEY\n"
        "  Local: export NOPECHA_API_KEY='your-key-here'"
    )

def log(message):
    """Enhanced logging that flushes immediately"""
    print(message, flush=True)
    sys.stdout.flush()

class RobloxGenerator:
    def __init__(self):
        self.accounts = []
        self.nopecha_key = NOPECHA_API_KEY
        self.extension_path = None
        
        log("=" * 60)
        log("Initializing Roblox Account Generator")
        log("Using NopeCHA Browser Extension Method")
        log("=" * 60)
        
        # Setup extension on initialization
        self.setup_nopecha_extension()
    
    def setup_nopecha_extension(self):
        """Download and setup NopeCHA extension"""
        try:
            log("\n🔧 Setting up NopeCHA extension...")
            
            extension_dir = '/tmp/nopecha_extension'
            os.makedirs(extension_dir, exist_ok=True)
            
            crx_path = '/tmp/NopeCHA.crx'
            
            # Download the extension from GitHub
            if not os.path.exists(crx_path):
                log("   📥 Downloading NopeCHA extension from GitHub...")
                url = "https://github.com/I0re/RobloxAccountGenerator/raw/master/NopeCHA.crx"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    with open(crx_path, 'wb') as f:
                        f.write(response.content)
                    log("   ✅ Extension downloaded successfully")
                else:
                    log(f"   ❌ Failed to download extension: HTTP {response.status_code}")
                    return False
            else:
                log("   ✅ Extension already downloaded")
            
            # Unpack CRX to directory
            log("   📦 Unpacking extension...")
            try:
                with zipfile.ZipFile(crx_path, 'r') as zip_ref:
                    zip_ref.extractall(extension_dir)
                log("   ✅ Extension unpacked")
            except Exception as unpack_error:
                log(f"   ⚠️  Could not unpack as ZIP, trying alternative method...")
                # CRX files have a header, skip it and extract
                with open(crx_path, 'rb') as f:
                    data = f.read()
                    # Skip CRX header (usually first 16 bytes for CRX3)
                    zip_data = data[16:]
                    with open('/tmp/temp.zip', 'wb') as temp_zip:
                        temp_zip.write(zip_data)
                    
                    with zipfile.ZipFile('/tmp/temp.zip', 'r') as zip_ref:
                        zip_ref.extractall(extension_dir)
                    log("   ✅ Extension unpacked (alternative method)")
            
            # Configure extension with API key
            log("   🔑 Configuring extension with API key...")
            settings_file = os.path.join(extension_dir, 'settings.json')
            
            # Create/update settings file with API key
            settings = {
                "key": self.nopecha_key,
                "enabled": True,
                "autosolve": True
            }
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f)
            
            log(f"   ✅ API key configured")
            
            self.extension_path = extension_dir
            log(f"✅ NopeCHA extension ready at: {extension_dir}")
            return True
            
        except Exception as e:
            log(f"❌ Error setting up extension: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_username(self):
        """Generate random username"""
        adjectives = ['Cool', 'Epic', 'Pro', 'Super', 'Mega', 'Ultra', 'Ninja', 'Master', 'Swift', 'Dark', 
                     'Fire', 'Ice', 'Thunder', 'Shadow', 'Cosmic', 'Cyber', 'Blaze', 'Storm', 'Nova', 'Stellar']
        nouns = ['Gamer', 'Player', 'User', 'Dude', 'King', 'Boss', 'Legend', 'Hero', 'Wolf', 'Tiger',
                'Dragon', 'Phoenix', 'Warrior', 'Knight', 'Falcon', 'Viper', 'Titan', 'Racer', 'Hunter', 'Reaper']
        numbers = ''.join(random.choices(string.digits, k=4))
        username = f"{random.choice(adjectives)}{random.choice(nouns)}{numbers}"
        log(f"📝 Generated username: {username}")
        return username
    
    def generate_password(self, length=12):
        """Generate secure password"""
        characters = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choices(characters, k=length))
        
        # Ensure it has at least one uppercase, lowercase, and digit
        while not (any(c.isupper() for c in password) and 
                   any(c.islower() for c in password) and 
                   any(c.isdigit() for c in password)):
            password = ''.join(random.choices(characters, k=length))
        
        log(f"🔒 Generated password: {password}")
        return password
    
    def get_chrome_driver(self):
        """Setup Chrome driver with NopeCHA extension"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Load NopeCHA extension
        if self.extension_path and os.path.exists(self.extension_path):
            chrome_options.add_argument(f'--load-extension={self.extension_path}')
            chrome_options.add_argument('--disable-extensions-except=' + self.extension_path)
            log("✅ NopeCHA extension will be loaded into Chrome")
        else:
            log("⚠️  Extension not found - CAPTCHAs will fail!")
        
        try:
            log("\n🌐 Initializing Chrome driver...")
            
            # Check if we're on Railway/Linux with chromium
            if os.path.exists('/usr/bin/chromium'):
                chrome_options.binary_location = '/usr/bin/chromium'
                log("   Found Chromium at /usr/bin/chromium")
                
                if os.path.exists('/usr/bin/chromedriver'):
                    service = Service('/usr/bin/chromedriver')
                    log("   Using chromedriver at /usr/bin/chromedriver")
                else:
                    log("   Installing chromedriver via webdriver-manager...")
                    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                
                driver = webdriver.Chrome(service=service, options=chrome_options)
                log("✅ Chrome driver initialized successfully!")
                return driver
            else:
                log("   Chromium not found, using webdriver-manager for Chrome...")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                log("✅ Chrome driver initialized successfully!")
                return driver
                
        except Exception as e:
            log(f"❌ Error creating Chrome driver: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_birthday(self):
        """Generate valid birthday (13-25 years old for Roblox TOS)"""
        today = datetime.now()
        min_age = today - timedelta(days=365*25)
        max_age = today - timedelta(days=365*13)
        random_date = min_age + timedelta(
            days=random.randint(0, (max_age - min_age).days)
        )
        birthday = {
            'month': random_date.strftime("%b"),
            'day': str(random_date.day),
            'year': str(random_date.year)
        }
        log(f"🎂 Generated birthday: {birthday['month']} {birthday['day']}, {birthday['year']}")
        return birthday
    
    def create_account_browser(self):
        """Create Roblox account using browser automation with NopeCHA extension"""
        username = self.generate_username()
        password = self.generate_password()
        birthday = self.generate_birthday()
        
        driver = None
        try:
            log("\n" + "=" * 60)
            log("🎮 STARTING ROBLOX ACCOUNT CREATION")
            log("=" * 60)
            
            driver = self.get_chrome_driver()
            if not driver:
                error_msg = "Could not initialize Chrome driver"
                log(f"❌ {error_msg}")
                return {
                    "username": username,
                    "password": password,
                    "status": "error",
                    "error": error_msg
                }
            
            # Navigate to Roblox signup
            log("\n🌐 Navigating to Roblox.com...")
            driver.get("https://www.roblox.com/")
            log(f"   Current URL: {driver.current_url}")
            time.sleep(3)
            
            log("\n📝 Filling signup form...")
            wait = WebDriverWait(driver, 15)
            
            # Fill birthday
            log("   → Selecting birthday...")
            
            try:
                # Month dropdown
                month_select = wait.until(EC.presence_of_element_located((By.ID, "MonthDropdown")))
                month_select.click()
                time.sleep(0.5)
                month_option = driver.find_element(By.XPATH, f"//option[@value='{birthday['month']}']")
                month_option.click()
                log(f"      ✓ Month: {birthday['month']}")
                
                # Day dropdown
                day_select = driver.find_element(By.ID, "DayDropdown")
                day_select.click()
                time.sleep(0.5)
                day_option = driver.find_element(By.XPATH, f"//option[@value='{birthday['day']}']")
                day_option.click()
                log(f"      ✓ Day: {birthday['day']}")
                
                # Year dropdown
                year_select = driver.find_element(By.ID, "YearDropdown")
                year_select.click()
                time.sleep(0.5)
                year_option = driver.find_element(By.XPATH, f"//option[@value='{birthday['year']}']")
                year_option.click()
                log(f"      ✓ Year: {birthday['year']}")
                
                time.sleep(1)
            except Exception as bday_error:
                log(f"❌ Error filling birthday: {bday_error}")
                return {
                    "username": username,
                    "password": password,
                    "status": "error",
                    "error": f"Could not fill birthday fields: {str(bday_error)}"
                }
            
            # Fill username
            log("   → Entering username...")
            try:
                username_field = driver.find_element(By.ID, "signup-username")
                username_field.clear()
                username_field.send_keys(username)
                time.sleep(1)
                log(f"      ✓ Username: {username}")
            except Exception as user_error:
                log(f"❌ Error filling username: {user_error}")
                return {
                    "username": username,
                    "password": password,
                    "status": "error",
                    "error": f"Could not fill username: {str(user_error)}"
                }
            
            # Fill password
            log("   → Entering password...")
            try:
                password_field = driver.find_element(By.ID, "signup-password")
                password_field.clear()
                password_field.send_keys(password)
                time.sleep(1)
                log(f"      ✓ Password: [HIDDEN]")
            except Exception as pass_error:
                log(f"❌ Error filling password: {pass_error}")
                return {
                    "username": username,
                    "password": password,
                    "status": "error",
                    "error": f"Could not fill password: {str(pass_error)}"
                }
            
            # Select gender (optional)
            log("   → Selecting gender...")
            try:
                gender = random.choice(['male', 'female'])
                try:
                    gender_button = driver.find_element(By.ID, f"signup-{gender}")
                    gender_button.click()
                    log(f"      ✓ Gender: {gender}")
                except:
                    gender_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in gender_buttons:
                        aria_label = btn.get_attribute("aria-label") or ""
                        if gender.lower() in btn.text.lower() or gender.lower() in aria_label.lower():
                            btn.click()
                            log(f"      ✓ Gender: {gender}")
                            break
                time.sleep(1)
            except Exception as gender_error:
                log(f"      ⚠️  Gender selection skipped: {gender_error}")
            
            # Click signup button
            log("\n🚀 Submitting signup form...")
            try:
                signup_button = driver.find_element(By.ID, "signup-button")
                signup_button.click()
                log("   ✓ Signup button clicked")
            except Exception as btn_error:
                log(f"❌ Error clicking signup button: {btn_error}")
                return {
                    "username": username,
                    "password": password,
                    "status": "error",
                    "error": f"Could not click signup button: {str(btn_error)}"
                }
            
            # Wait for NopeCHA extension to solve CAPTCHA automatically
            log("\n⏳ Waiting for NopeCHA extension to solve CAPTCHA...")
            log("   (This may take 30-120 seconds)")
            
            # Monitor for success for up to 3 minutes
            max_wait = 180  # 3 minutes
            check_interval = 5
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(check_interval)
                elapsed += check_interval
                
                current_url = driver.current_url
                
                # Check for success indicators
                success_indicators = ["home", "games", "/home", "/discover"]
                if any(indicator in current_url.lower() for indicator in success_indicators):
                    log(f"\n   [{elapsed}s] SUCCESS URL DETECTED: {current_url}")
                    log("\n" + "=" * 60)
                    log("✅ SUCCESS! ACCOUNT CREATED!")
                    log("=" * 60)
                    log(f"   NopeCHA solved the CAPTCHA in ~{elapsed} seconds")
                    
                    account_info = {
                        "username": username,
                        "password": password,
                        "status": "success",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "solve_time": f"{elapsed}s"
                    }
                    
                    self.accounts.append(account_info)
                    self.save_account(username, password)
                    
                    log(f"Username: {username}")
                    log(f"Password: {password}")
                    log(f"Created: {account_info['created_at']}")
                    
                    return account_info
                
                # Progress update every 15 seconds
                if elapsed % 15 == 0:
                    log(f"   [{elapsed}s] Still waiting... URL: {current_url}")
            
            # Timeout
            log(f"\n❌ Timeout after {max_wait} seconds")
            log(f"   Final URL: {driver.current_url}")
            log("   CAPTCHA may not have been solved by extension")
            
            return {
                "username": username,
                "password": password,
                "status": "timeout",
                "error": f"Account creation timed out after {max_wait}s - CAPTCHA may not have been solved",
                "final_url": driver.current_url
            }
                    
        except Exception as e:
            log(f"\n❌ EXCEPTION OCCURRED: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "username": username,
                "password": password,
                "status": "error",
                "error": str(e)
            }
        finally:
            if driver:
                log("\n🔧 Cleaning up browser...")
                try:
                    driver.quit()
                    log("✅ Browser closed")
                except:
                    log("⚠️  Error closing browser")
    
    def save_account(self, username, password):
        """Save account to file"""
        try:
            with open('accounts.txt', 'a') as f:
                f.write(f"{username}:{password}\n")
            log(f"💾 Account saved to accounts.txt")
        except Exception as e:
            log(f"⚠️  Could not save to file: {e}")

# Initialize generator
generator = RobloxGenerator()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Generate a new Roblox account"""
    log("\n" + "=" * 60)
    log("📨 Received account generation request from client")
    log("=" * 60)
    
    result = generator.create_account_browser()
    
    log("\n📤 Sending response to client:")
    log(f"   Status: {result.get('status')}")
    log("=" * 60 + "\n")
    
    return jsonify(result)

@app.route('/accounts', methods=['GET'])
def get_accounts():
    """Get all generated accounts"""
    return jsonify({"accounts": generator.accounts})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "method": "nopecha_extension",
        "extension_loaded": generator.extension_path is not None,
        "accounts_generated": len(generator.accounts)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    log("\n" + "=" * 60)
    log(f"🚀 Starting Flask server on port {port}")
    log("=" * 60)
    log(f"📍 Local: http://localhost:{port}")
    log(f"🌐 Network: http://0.0.0.0:{port}")
    log("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
