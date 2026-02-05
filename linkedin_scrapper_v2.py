"""
LinkedIn Profile Scraper v2.0
================================================================================
A comprehensive LinkedIn profile scraper with advanced features:
- Multiple authentication methods (Google OAuth, Microsoft, email/password)
- Batch processing with rate limiting
- Enhanced data extraction with fallback strategies
- Export to multiple formats (JSON, CSV, Excel)
- Profile comparison and analysis
- Robust error handling and logging
- Anti-detection features
================================================================================
"""

import json
import csv
import time
import random
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class ScraperConfig:
    """Configuration class for the LinkedIn scraper"""
    headless: bool = False
    wait_timeout: int = 10
    page_load_timeout: int = 30
    implicit_wait: int = 3
    retry_attempts: int = 3
    delay_between_profiles: tuple = (5, 10)  # (min, max) seconds
    delay_between_actions: tuple = (1, 3)   # (min, max) seconds
    max_scroll_attempts: int = 5
    enable_logging: bool = True
    log_level: str = "INFO"
    output_dir: str = "linkedin_data"
    user_agents: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]


@dataclass
class LinkedInProfile:
    """Data class for LinkedIn profile information"""
    url: str = ""
    name: str = ""
    headline: str = ""
    location: str = ""
    about: str = ""
    current_company: str = ""
    profile_image_url: str = ""
    background_image_url: str = ""
    followers_count: str = ""
    connections_count: str = ""
    experience: List[Dict] = None
    education: List[Dict] = None
    certifications: List[Dict] = None
    skills: List[str] = None
    languages: List[Dict] = None
    projects: List[Dict] = None
    volunteer_experience: List[Dict] = None
    recommendations: List[Dict] = None
    publications: List[Dict] = None
    patents: List[Dict] = None
    honors_awards: List[Dict] = None
    test_scores: List[Dict] = None
    courses: List[Dict] = None
    organizations: List[Dict] = None
    contact_info: Dict = None
    scraped_at: str = ""
    
    def __post_init__(self):
        if self.experience is None:
            self.experience = []
        if self.education is None:
            self.education = []
        if self.certifications is None:
            self.certifications = []
        if self.skills is None:
            self.skills = []
        if self.languages is None:
            self.languages = []
        if self.projects is None:
            self.projects = []
        if self.volunteer_experience is None:
            self.volunteer_experience = []
        if self.recommendations is None:
            self.recommendations = []
        if self.publications is None:
            self.publications = []
        if self.patents is None:
            self.patents = []
        if self.honors_awards is None:
            self.honors_awards = []
        if self.test_scores is None:
            self.test_scores = []
        if self.courses is None:
            self.courses = []
        if self.organizations is None:
            self.organizations = []
        if self.contact_info is None:
            self.contact_info = {}
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class LinkedInScraperV2:
    """Enhanced LinkedIn Profile Scraper with advanced features"""
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        """Initialize the scraper with configuration"""
        self.config = config or ScraperConfig()
        self.driver = None
        self.wait = None
        self.logger = self._setup_logging()
        self.session_stats = {
            "profiles_scraped": 0,
            "profiles_failed": 0,
            "session_start": datetime.now(),
            "errors": []
        }
        
        # Create output directory
        Path(self.config.output_dir).mkdir(exist_ok=True)
        
        self.logger.info("LinkedInScraperV2 initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("LinkedInScraperV2")
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            if self.config.enable_logging:
                log_file = Path(self.config.output_dir) / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(console_formatter)
                logger.addHandler(file_handler)
        
        return logger
    
    def setup_driver(self) -> None:
        """Setup Chrome driver with anti-detection features"""
        try:
            chrome_options = Options()
            
            if self.config.headless:
                chrome_options.add_argument("--headless=new")
            
            # Anti-detection options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Faster loading
            chrome_options.add_argument("--disable-javascript")  # Sometimes helps
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-popup-blocking")
            
            # Random user agent
            user_agent = random.choice(self.config.user_agents)
            chrome_options.add_argument(f"user-agent={user_agent}")
            
            # Exclude automation indicators
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set preferences
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to hide automation
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            # Set timeouts
            self.driver.set_page_load_timeout(self.config.page_load_timeout)
            self.driver.implicitly_wait(self.config.implicit_wait)
            
            # Create wait object
            self.wait = WebDriverWait(self.driver, self.config.wait_timeout)
            
            self.logger.info("Chrome driver setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup driver: {str(e)}")
            raise
    
    def _random_delay(self, delay_range: tuple = None) -> None:
        """Add random delay between actions"""
        if delay_range is None:
            delay_range = self.config.delay_between_actions
        
        delay = random.uniform(delay_range[0], delay_range[1])
        time.sleep(delay)
    
    def _safe_click(self, element) -> bool:
        """Safely click an element with retry logic"""
        for attempt in range(3):
            try:
                ActionChains(self.driver).move_to_element(element).click().perform()
                return True
            except Exception as e:
                self.logger.warning(f"Click attempt {attempt + 1} failed: {str(e)}")
                time.sleep(1)
        return False
    
    def _safe_get_text(self, element) -> str:
        """Safely get text from element"""
        try:
            return element.text.strip()
        except StaleElementReferenceException:
            return ""
        except Exception as e:
            self.logger.warning(f"Error getting text: {str(e)}")
            return ""
    
    def _smart_scroll(self, pause_time: float = 2) -> None:
        """Intelligent scrolling to load dynamic content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for scroll_attempt in range(self.config.max_scroll_attempts):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._random_delay((pause_time, pause_time + 1))
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        self._random_delay()
    
    def login_manual(self) -> bool:
        """Manual login with support for all authentication methods"""
        try:
            self.logger.info("Starting manual login process")
            
            self.driver.get("https://www.linkedin.com/login")
            self._random_delay((3, 5))
            
            print("\n" + "="*80)
            print("🔐 LINKEDIN LOGIN REQUIRED")
            print("="*80)
            print("Choose your preferred login method:")
            print("✓ Email/Password")
            print("✓ Sign in with Google")
            print("✓ Sign in with Microsoft")
            print("✓ Sign in with Apple")
            print("✓ Any other authentication method")
            print("\nPlease complete login in the browser window.")
            print("The scraper will automatically detect successful login.")
            print("="*80)
            
            # Wait for successful login (max 5 minutes)
            login_timeout = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < login_timeout:
                current_url = self.driver.current_url
                
                # Check various success indicators
                if any(indicator in current_url.lower() for indicator in [
                    "feed", "mynetwork", "/in/", "messaging", "jobs", "notifications"
                ]) or current_url == "https://www.linkedin.com/":
                    
                    # Double-check by looking for LinkedIn-specific elements
                    try:
                        self.wait.until(
                            EC.any_of(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-control-name]")),
                                EC.presence_of_element_located((By.CSS_SELECTOR, "nav.global-nav")),
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module"))
                            )
                        )
                        self.logger.info("✅ Login successful!")
                        print("\n✅ Login successful! Starting profile scrapping...")
                        return True
                    except TimeoutException:
                        pass
                
                time.sleep(2)
            
            self.logger.warning("Login timeout reached")
            print("⚠️  Login timeout. Please try again.")
            return False
            
        except Exception as e:
            self.logger.error(f"Manual login failed: {str(e)}")
            print(f"❌ Login error: {str(e)}")
            return False
    
    def login_email_password(self, email: str, password: str) -> bool:
        """Login with email and password"""
        try:
            self.logger.info(f"Attempting email login for: {email}")
            
            self.driver.get("https://www.linkedin.com/login")
            self._random_delay((3, 5))
            
            # Enter email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            for char in email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self._random_delay((1, 2))
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self._random_delay((1, 2))
            
            # Click sign in
            sign_in_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            self._safe_click(sign_in_btn)
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check for CAPTCHA or verification
            if "challenge" in self.driver.current_url or "checkpoint" in self.driver.current_url:
                self.logger.warning("CAPTCHA or security checkpoint detected")
                print("🔒 Security checkpoint detected. Please complete verification manually.")
                
                # Wait for user to complete verification
                input("Press Enter after completing the verification...")
            
            # Verify successful login
            if any(indicator in self.driver.current_url.lower() for indicator in [
                "feed", "mynetwork", "/in/"
            ]):
                self.logger.info("Email login successful")
                return True
            
            self.logger.warning("Email login might have failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Email login failed: {str(e)}")
            return False
    
    def scrape_profile(self, profile_url: str) -> Optional[LinkedInProfile]:
        """Scrape a LinkedIn profile with comprehensive data extraction"""
        try:
            self.logger.info(f"Starting to scrape profile: {profile_url}")
            
            if not self.driver:
                self.setup_driver()
            
            # Navigate to profile
            self.driver.get(profile_url)
            self._random_delay((5, 8))
            
            # Initialize profile object
            profile = LinkedInProfile(url=profile_url)
            
            # Scroll to load all content
            self._smart_scroll()
            
            # Extract basic information
            profile.name = self._extract_name()
            profile.headline = self._extract_headline()
            profile.location = self._extract_location()
            profile.about = self._extract_about()
            profile.profile_image_url = self._extract_profile_image()
            profile.followers_count = self._extract_followers_count()
            profile.connections_count = self._extract_connections_count()
            
            # Extract experience
            profile.experience = self._extract_experience()
            if profile.experience:
                profile.current_company = profile.experience[0].get('company', '')
            
            # Extract education
            profile.education = self._extract_education()
            
            # Extract certifications
            profile.certifications = self._extract_certifications()
            
            # Extract skills
            profile.skills = self._extract_skills()
            
            # Extract languages
            profile.languages = self._extract_languages()
            
            # Extract projects
            profile.projects = self._extract_projects()
            
            # Extract volunteer experience
            profile.volunteer_experience = self._extract_volunteer_experience()
            
            # Extract contact information
            profile.contact_info = self._extract_contact_info()
            
            self.session_stats["profiles_scraped"] += 1
            self.logger.info(f"Successfully scraped profile: {profile.name}")
            
            return profile
            
        except Exception as e:
            self.session_stats["profiles_failed"] += 1
            self.session_stats["errors"].append({
                "url": profile_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.logger.error(f"Failed to scrape profile {profile_url}: {str(e)}")
            return None
    
    def _extract_name(self) -> str:
        """Extract profile name with multiple fallback strategies"""
        selectors = [
            "h1.text-heading-xlarge",
            "h1[class*='text-heading-xlarge']",
            "div[class*='pv-text-details__left-panel'] h1",
            ".pv-top-card .pv-top-card__name",
            "h1",
            ".pv-entity__summary-title"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = self._safe_get_text(element)
                if text and len(text) > 2:
                    return text
            except NoSuchElementException:
                continue
        
        self.logger.warning("Could not extract name")
        return ""
    
    def _extract_headline(self) -> str:
        """Extract profile headline"""
        selectors = [
            ".text-body-medium.break-words",
            "div.text-body-medium",
            ".pv-text-details__left-panel .text-body-medium",
            ".pv-top-card .pv-top-card__headline",
            "div[class*='text-body-medium']"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = self._safe_get_text(element)
                if text and len(text) > 5:
                    return text
            except NoSuchElementException:
                continue
        
        return ""
    
    def _extract_location(self) -> str:
        """Extract profile location"""
        selectors = [
            "span.text-body-small.inline.break-words",
            "span.text-body-small.inline",
            ".pv-text-details__left-panel .text-body-small",
            ".pv-top-card .pv-top-card__location",
            "span[class*='text-body-small']"
            ""
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = self._safe_get_text(element)
                if text and any(indicator in text.lower() for indicator in ['area', 'city', 'state', 'country', ',']):
                    return text
            except NoSuchElementException:
                continue
        
        return ""
    
    def _extract_about(self) -> str:
        """Extract about section with show more handling"""
        try:
            # First try to find and click "show more" button
            self._handle_show_more_buttons()
            
            # Try multiple selectors for about section
            about_selectors = [
                "section[data-section='summary'] div[class*='pv-shared-text-with-see-more'] span",
                "section[data-section='summary'] .pv-entity__description",
                ".pv-about-section .pv-about__summary-text",
                "div[class*='pv-shared-text-with-see-more'] span[aria-hidden='true']"
            ]
            
            for selector in about_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = self._safe_get_text(element)
                        if text and len(text) > 50:
                            return text
                except NoSuchElementException:
                    continue
            
            # Fallback: look for any substantial text block
            all_divs = self.driver.find_elements(By.TAG_NAME, "div")
            for div in all_divs:
                text = self._safe_get_text(div)
                if text and len(text) > 100 and len(text) < 2000:
                    # Check if it looks like an about section
                    if any(keyword in text.lower() for keyword in [
                        'experience', 'passionate', 'background', 'skills', 'expertise'
                    ]):
                        return text
            
            return ""
            
        except Exception as e:
            self.logger.warning(f"Error extracting about section: {str(e)}")
            return ""
    
    def _handle_show_more_buttons(self) -> None:
        """Click all 'show more' buttons to expand content"""
        try:
            show_more_buttons = self.driver.find_elements(
                By.XPATH, 
                "//button[contains(text(), 'Show more') or contains(text(), 'See more') or @aria-expanded='false']"
            )
            
            for button in show_more_buttons[:5]:  # Limit to avoid infinite loops
                try:
                    if button.is_displayed() and button.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView();", button)
                        self._random_delay((0.5, 1))
                        self._safe_click(button)
                        self._random_delay((1, 2))
                except Exception:
                    continue
        except Exception as e:
            self.logger.debug(f"Error handling show more buttons: {str(e)}")
    
    def _extract_profile_image(self) -> str:
        """Extract profile image URL"""
        try:
            img_selectors = [
                ".pv-top-card__photo img",
                ".profile-photo-edit__preview img",
                "img[class*='profile-photo']",
                ".EntityPhoto-circle-5 img"
            ]
            
            for selector in img_selectors:
                try:
                    img_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return img_element.get_attribute('src') or ""
                except NoSuchElementException:
                    continue
            
            return ""
        except Exception:
            return ""
    
    def _extract_followers_count(self) -> str:
        """Extract followers count"""
        try:
            followers_selectors = [
                "span[class*='t-bold'] + span:contains('followers')",
                ".pv-top-card__connections"
            ]
            
            followers_text = self._safe_get_text(
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'followers') or contains(text(), 'follower')]")
            )
            
            if followers_text:
                # Extract number from text like "500+ followers"
                import re
                numbers = re.findall(r'[\d,]+', followers_text)
                if numbers:
                    return numbers[0]
            
            return ""
        except Exception:
            return ""
    
    def _extract_connections_count(self) -> str:
        """Extract connections count"""
        try:
            connections_text = self._safe_get_text(
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'connections') or contains(text(), 'connection')]")
            )
            
            if connections_text:
                import re
                numbers = re.findall(r'[\d,]+', connections_text)
                if numbers:
                    return numbers[0]
            
            return ""
        except Exception:
            return ""
    
    def login_with_email_password(self, email: str, password: str) -> bool:
        """Login using email and password - wrapper for existing method"""
        return self.login_email_password(email, password)
    
    def login_with_google(self) -> bool:
        """Login with Google OAuth"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Look for Google login button
            google_login_selectors = [
                "button[data-provider='google']",
                "a[href*='google']",
                "*[class*='google']",
                "button:contains('Google')"
            ]
            
            for selector in google_login_selectors:
                try:
                    google_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    google_button.click()
                    time.sleep(3)
                    
                    # User needs to complete OAuth manually
                    self.logger.info("Please complete Google OAuth in the browser window")
                    input("Press Enter after completing Google login...")
                    
                    # Check if login was successful
                    current_url = self.driver.current_url
                    if "feed" in current_url or "linkedin.com/in/" in current_url:
                        self.logger.info("Google login successful")
                        return True
                    break
                except NoSuchElementException:
                    continue
            
            return False
        except Exception as e:
            self.logger.error(f"Google login failed: {str(e)}")
            return False
    
    def login_with_microsoft(self) -> bool:
        """Login with Microsoft account"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Look for Microsoft login button
            microsoft_login_selectors = [
                "button[data-provider='microsoft']",
                "a[href*='microsoft']",
                "*[class*='microsoft']",
                "button:contains('Microsoft')"
            ]
            
            for selector in microsoft_login_selectors:
                try:
                    microsoft_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    microsoft_button.click()
                    time.sleep(3)
                    
                    # User needs to complete OAuth manually
                    self.logger.info("Please complete Microsoft OAuth in the browser window")
                    input("Press Enter after completing Microsoft login...")
                    
                    # Check if login was successful
                    current_url = self.driver.current_url
                    if "feed" in current_url or "linkedin.com/in/" in current_url:
                        self.logger.info("Microsoft login successful")  
                        return True
                    break
                except NoSuchElementException:
                    continue
            
            return False
        except Exception as e:
            self.logger.error(f"Microsoft login failed: {str(e)}")
            return False
    
    def save_to_json(self, profiles: List[LinkedInProfile], filename: str) -> bool:
        """Save profiles to JSON file"""
        try:
            # Convert dataclass objects to dictionaries
            profiles_dict = [asdict(profile) for profile in profiles]
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(profiles_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved {len(profiles)} profiles to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save JSON: {str(e)}")
            return False
    
    def save_to_csv(self, profiles: List[LinkedInProfile], filename: str) -> bool:
        """Save profiles to CSV file"""
        try:
            if not profiles:
                return False
            
            # Flatten the profile data for CSV
            flattened_data = []
            for profile in profiles:
                row = {
                    'name': profile.name,
                    'headline': profile.headline,
                    'location': profile.location,
                    'about': profile.about[:500] + '...' if len(profile.about) > 500 else profile.about,
                    'current_company': profile.current_company,
                    'url': profile.url,
                    'profile_image': profile.profile_image,
                    'followers_count': profile.followers_count,
                    'connections_count': profile.connections_count,
                    'experience_count': len(profile.experience),
                    'skills_count': len(profile.skills),
                    'certifications_count': len(profile.certifications),
                    'languages_count': len(profile.languages),
                    'experience': '; '.join([f"{exp.get('title', '')} at {exp.get('company', '')}" for exp in profile.experience[:3]]),
                    'skills': '; '.join(profile.skills[:10]),
                    'languages': '; '.join(profile.languages)
                }
                flattened_data.append(row)
            
            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if flattened_data:
                    writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_data)
            
            self.logger.info(f"Successfully saved {len(profiles)} profiles to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {str(e)}")
            return False
    
    def save_to_excel(self, profiles: List[LinkedInProfile], filename: str) -> bool:
        """Save profiles to Excel file (requires openpyxl)"""
        try:
            import pandas as pd
            
            # Convert to DataFrame
            profiles_dict = [asdict(profile) for profile in profiles]
            df = pd.json_normalize(profiles_dict)
            
            # Save to Excel
            df.to_excel(filename, index=False)
            self.logger.info(f"Successfully saved {len(profiles)} profiles to {filename}")
            return True
        except ImportError:
            self.logger.warning("pandas and openpyxl required for Excel export. Use: pip install pandas openpyxl")
            return False
        except Exception as e:
            self.logger.error(f"Failed to save Excel: {str(e)}")
            return False
    
    def close(self):
        """Close the browser and cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {str(e)}")


def main():
    """Main function to run the LinkedIn Profile Scraper"""
    print("=" * 80)
    print("LinkedIn Profile Scraper v2.0")
    print("=" * 80)
    
    # Configuration
    config = ScraperConfig(
        headless=False,  # Set to True for headless mode
        wait_timeout=15,
        retry_attempts=2
    )
    
    # Initialize scraper
    scraper = LinkedInProfileScraper(config)
    
    try:
        # Example usage - modify these URLs with actual LinkedIn profiles
        profile_urls = [
            "https://www.linkedin.com/in/example-profile/",
            # Add more profile URLs here
        ]
        
        print(f"\nStarting to scrape {len(profile_urls)} profile(s)...")
        
        # Option 1: Scrape without login (limited data)
        print("\n1. Scraping without login (public data only)")
        scraped_profiles = []
        for url in profile_urls:
            print(f"\nScraping: {url}")
            profile_data = scraper.scrape_profile(url)
            if profile_data:
                scraped_profiles.append(profile_data)
                print(f"✓ Successfully scraped: {profile_data.name}")
            else:
                print(f"✗ Failed to scrape profile")
        
        # Save results
        if scraped_profiles:
            # Save to JSON
            json_filename = f"scraped_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            scraper.save_to_json(scraped_profiles, json_filename)
            print(f"\n✓ Data saved to {json_filename}")
            
            # Save to CSV
            csv_filename = f"scraped_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            scraper.save_to_csv(scraped_profiles, csv_filename)
            print(f"✓ Data saved to {csv_filename}")
            
            print(f"\n📊 Summary: Successfully scraped {len(scraped_profiles)} out of {len(profile_urls)} profiles")
        else:
            print("\n❌ No profiles were successfully scraped")
        
        # Option 2: Login and scrape (uncomment to use)
        """
        print("\n2. Login required for full data access")
        login_choice = input("Do you want to login? (y/n): ").lower().strip()
        
        if login_choice == 'y':
            print("Choose login method:")
            print("1. Email/Password")
            print("2. Google OAuth")
            print("3. Microsoft")
            
            method = input("Enter choice (1-3): ").strip()
            
            if method == "1":
                email = input("Enter your LinkedIn email: ").strip()
                password = input("Enter your LinkedIn password: ").strip()
                if scraper.login_with_email_password(email, password):
                    print("✓ Login successful!")
                else:
                    print("✗ Login failed!")
                    return
            elif method == "2":
                if scraper.login_with_google():
                    print("✓ Google login successful!")
                else:
                    print("✗ Google login failed!")
                    return
            elif method == "3":
                if scraper.login_with_microsoft():
                    print("✓ Microsoft login successful!")
                else:
                    print("✗ Microsoft login failed!")
                    return
            else:
                print("Invalid choice!")
                return
        """
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        logging.exception("Unexpected error in main function")
    finally:
        scraper.close()
        print("\n🏁 Scraping session ended")


def interactive_mode():
    """Interactive mode for user-friendly operation"""
    print("=" * 80)
    print("LinkedIn Profile Scraper v2.0 - Interactive Mode")
    print("=" * 80)
    
    # Get configuration from user
    print("\n🔧 Configuration")
    headless = input("Run in headless mode? (y/n) [n]: ").lower().strip() == 'y'
    
    config = ScraperConfig(headless=headless)
    scraper = LinkedInProfileScraper(config)
    
    try:
        print("\n📝 Enter LinkedIn profile URLs (one per line, empty line to finish):")
        urls = []
        while True:
            url = input("URL: ").strip()
            if not url:
                break
            if "linkedin.com/in/" in url:
                urls.append(url)
            else:
                print("⚠️  Please enter a valid LinkedIn profile URL")
        
        if not urls:
            print("❌ No valid URLs provided!")
            return
        
        print(f"\n🚀 Starting to scrape {len(urls)} profile(s)...")
        
        scraped_profiles = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Scraping: {url}")
            profile_data = scraper.scrape_profile(url)
            
            if profile_data:
                scraped_profiles.append(profile_data)
                print(f"✓ Successfully scraped: {profile_data.name}")
                
                # Show preview
                preview = input("Preview data? (y/n) [n]: ").lower().strip()
                if preview == 'y':
                    print(f"\n--- Profile Preview ---")
                    print(f"Name: {profile_data.name}")
                    print(f"Headline: {profile_data.headline}")
                    print(f"Location: {profile_data.location}")
                    print(f"Experience: {len(profile_data.experience)} entries")
                    print(f"Skills: {len(profile_data.skills)} entries")
            else:
                print(f"✗ Failed to scrape profile")
            
            # Add delay between profiles
            if i < len(urls):
                print("⏱️  Waiting before next profile...")
                time.sleep(random.uniform(3, 7))
        
        # Save results
        if scraped_profiles:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Ask for export format
            print("\n💾 Choose export format:")
            print("1. JSON only")
            print("2. CSV only") 
            print("3. Both JSON and CSV")
            
            export_choice = input("Enter choice (1-3) [3]: ").strip() or "3"
            
            if export_choice in ["1", "3"]:
                json_filename = f"linkedin_profiles_{timestamp}.json"
                scraper.save_to_json(scraped_profiles, json_filename)
                print(f"✓ JSON saved: {json_filename}")
            
            if export_choice in ["2", "3"]:
                csv_filename = f"linkedin_profiles_{timestamp}.csv"
                scraper.save_to_csv(scraped_profiles, csv_filename)
                print(f"✓ CSV saved: {csv_filename}")
            
            print(f"\n🎉 Successfully scraped {len(scraped_profiles)} out of {len(urls)} profiles!")
        else:
            print("\n😞 No profiles were successfully scraped")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logging.exception("Error in interactive mode")
    finally:
        scraper.close()


if __name__ == "__main__":
    """Entry point of the script"""
    print("LinkedIn Profile Scraper v2.0")
    print("Choose mode:")
    print("1. Interactive mode (recommended)")
    print("2. Script mode (edit code for URLs)")
    
    try:
        mode = input("\nEnter choice (1-2) [1]: ").strip() or "1"
        
        if mode == "1":
            interactive_mode()
        elif mode == "2":
            main()
        else:
            print("Invalid choice!")
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"Startup error: {str(e)}")
        logging.exception("Startup error")
