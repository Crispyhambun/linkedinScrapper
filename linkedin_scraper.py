"""
LinkedIn Profile Scraper
Extracts data from LinkedIn profiles including experience, education, certifications, and skills
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json


class LinkedInProfileScraper:
    def __init__(self, email=None, password=None, headless=False, manual_login=False):
        """
        Initialize the LinkedIn profile scraper
        
        Args:
            email: LinkedIn account email (not needed for manual_login)
            password: LinkedIn account password (not needed for manual_login)
            headless: Run browser in headless mode
            manual_login: If True, opens browser for manual login (supports Google OAuth)
        """
        self.email = email
        self.password = password
        self.driver = None
        self.headless = headless
        self.manual_login = manual_login
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        
    def login(self):
        """Login to LinkedIn"""
        # Manual login mode (supports Google OAuth, Microsoft, etc.)
        if self.manual_login:
            return self.manual_login_flow()
        
        # Standard email/password login
        if not self.email or not self.password:
            print("Warning: No credentials provided. Some content may not be accessible.")
            return False
            
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            
            # Click login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                print("Successfully logged in to LinkedIn")
                return True
            else:
                print("Login may have failed. Please check credentials.")
                return False
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            return False
    
    def manual_login_flow(self):
        """
        Manual login flow - opens browser and waits for user to login
        Supports Google OAuth, Microsoft login, or any authentication method
        """
        try:
            print("\n" + "="*60)
            print("MANUAL LOGIN MODE")
            print("="*60)
            print("1. A browser window will open with LinkedIn login page")
            print("2. Please login using your preferred method:")
            print("   - Email/Password")
            print("   - Sign in with Google")
            print("   - Sign in with Microsoft")
            print("   - Or any other method")
            print("3. Wait until you see your LinkedIn feed")
            print("4. The scraper will automatically detect successful login")
            print("="*60)
            
            self.driver.get("https://www.linkedin.com/login")
            
            print("\nWaiting for you to login...")
            print("(You have up to 120 seconds to complete login)")
            
            # Wait for user to login (check if redirected to feed or home)
            wait_time = 120  # 2 minutes
            start_time = time.time()
            
            while time.time() - start_time < wait_time:
                current_url = self.driver.current_url
                
                # Check if login successful (redirected away from login page)
                if ("feed" in current_url or 
                    "mynetwork" in current_url or 
                    current_url == "https://www.linkedin.com/" or
                    "/in/" in current_url):
                    print("\n✓ Login detected successfully!")
                    print("Proceeding with scraping...")
                    return True
                
                time.sleep(2)  # Check every 2 seconds
            
            # Timeout
            print("\n⚠ Login timeout. Please try again.")
            return False
            
        except Exception as e:
            print(f"Manual login error: {str(e)}")
            return False
    
    def scrape_profile(self, profile_url):
        """
        Scrape data from a LinkedIn profile
        
        Args:
            profile_url: URL of the LinkedIn profile (e.g., https://www.linkedin.com/in/username)
            
        Returns:
            dict: Dictionary containing profile data
        """
        if not self.driver:
            self.setup_driver()
            if self.manual_login or self.email and self.password:
                self.login()
        
        try:
            self.driver.get(profile_url)
            time.sleep(5)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Check what elements exist
            edu_headers = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Education')]")
            cert_headers = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Licenses')]")

            print(f"Education headers found: {len(edu_headers)}")
            print(f"Certification headers found: {len(cert_headers)}")

            profile_data = {
                "url": profile_url,
                "name": None,
                "headline": None,
                "location": None,
                "about": None,
                "current_company": None,
                "experience": [],
                "education": [],
                "certifications": [],
                "skills": [],
                "languages": []
            }
            
            # Extract name
            try:
                # Try multiple selectors for name
                name_elem = None
                selectors = [
                    "h1",  # Simple h1
                    "div[data-test-id='top-card-profile-name']",  # Test ID
                    ".text-heading-xlarge",  # Class
                    "h1.text-heading-xlarge",  # Combined
                ]
                
                for selector in selectors:
                    try:
                        name_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if name_elem.text.strip():
                            profile_data["name"] = name_elem.text.strip()
                            break
                    except:
                        continue
                
                if not profile_data["name"]:
                    # Try by getting all h1 elements and picking the first one with text
                    h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
                    for h1 in h1_elements:
                        text = h1.text.strip()
                        if text and len(text) > 2:
                            profile_data["name"] = text
                            break
                            
            except Exception as e:
                print(f"Error extracting name: {str(e)}")
            
            # Extract headline
            try:
                headline = self.driver.find_element(By.CSS_SELECTOR, "div.text-body-medium")
                profile_data["headline"] = headline.text
            except:
                try:
                    headline = self.driver.find_element(By.CSS_SELECTOR, ".pv-text-details__left-panel .text-body-medium")
                    profile_data["headline"] = headline.text
                except:
                    print("Could not extract headline")
            
            # Extract location
            try:
                location = self.driver.find_element(By.CSS_SELECTOR, "span.text-body-small.inline")
                profile_data["location"] = location.text
            except:
                try:
                    location = self.driver.find_element(By.CSS_SELECTOR, ".pv-text-details__left-panel .text-body-small")
                    profile_data["location"] = location.text
                except:
                    print("Could not extract location")
            
            # Extract About section
            try:
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                try:
                    show_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-expanded='false']")
                    for btn in show_more_buttons:
                        try:
                            if "show more" in btn.text.lower() or "see more" in btn.text.lower():
                                self.driver.execute_script("arguments[0].scrollIntoView();", btn)
                                time.sleep(0.5)
                                btn.click()
                                time.sleep(1)
                        except:
                            pass
                except:
                    pass
                
                about_text = None
                
                try:
                    about_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'About')]")
                    parent = about_section.find_element(By.XPATH, "./ancestor::section")
                    about_elem = parent.find_element(By.CSS_SELECTOR, "p, div[class*='text']")
                    about_text = about_elem.text.strip()
                except:
                    pass
                
                if not about_text:
                    try:
                        all_p_tags = self.driver.find_elements(By.TAG_NAME, "p")
                        for p in all_p_tags:
                            text = p.text.strip()
                            if text and len(text) > 50:
                                about_text = text
                                break
                    except:
                        pass
                
                if not about_text:
                    try:
                        divs_with_text = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='t-normal']")
                        for div in divs_with_text:
                            text = div.text.strip()
                            if text and len(text) > 50 and "following" not in text.lower():
                                about_text = text
                                break
                    except:
                        pass
                
                if about_text:
                    profile_data["about"] = about_text
                    
            except Exception as e:
                print(f"Error extracting about section: {str(e)}")
            
            # Extract Experience
            try:
                # Scroll to experience section
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(2)
                
                # Try to find experience section using multiple strategies
                experience_items = []
                
                # Strategy 1: Find by "Experience" heading
                try:
                    exp_headers = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Experience')]")
                    if exp_headers:
                        parent = exp_headers[0].find_element(By.XPATH, "./ancestor::section")
                        exp_list_items = parent.find_elements(By.CSS_SELECTOR, "div[class*='experience'] div, li[class*='experience']")
                        if exp_list_items:
                            experience_items = exp_list_items
                except:
                    pass
                
                # Strategy 2: Find experience items by common patterns
                if not experience_items:
                    try:
                        experience_items = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='pvs-entity']")
                    except:
                        pass
                
                # Strategy 3: Use data test IDs if available
                if not experience_items:
                    try:
                        experience_items = self.driver.find_elements(By.CSS_SELECTOR, "div[data-test-id*='experience']")
                    except:
                        pass
                
                # Extract data from experience items
                for item in experience_items[:15]:  # Limit to first 15
                    try:
                        exp_data = {}
                        item_text = item.text
                        
                        if not item_text:
                            continue
                        
                        # Try to extract position/title (usually first line or bold text)
                        try:
                            title_elem = item.find_element(By.CSS_SELECTOR, "span[class*='t-bold'], h3, strong")
                            exp_data["title"] = title_elem.text.strip()
                        except:
                            # Get first line as title
                            lines = item_text.split('\n')
                            if lines:
                                exp_data["title"] = lines[0]
                        
                        # Extract company name (usually second line)
                        try:
                            company_elem = item.find_element(By.CSS_SELECTOR, "span[class*='t-14']")
                            exp_data["company"] = company_elem.text.strip()
                        except:
                            # Try to extract from text
                            lines = item_text.split('\n')
                            if len(lines) > 1:
                                exp_data["company"] = lines[1]
                        
                        # Extract duration
                        try:
                            duration_elem = item.find_element(By.CSS_SELECTOR, "span[class*='t-black--light']")
                            exp_data["duration"] = duration_elem.text.strip()
                        except:
                            # Try to find date pattern
                            import re
                            dates = re.findall(r'([A-Za-z]+\s+\d{4}.*)', item_text)
                            if dates:
                                exp_data["duration"] = dates[0]
                        
                        # Extract location
                        try:
                            location_elems = item.find_elements(By.CSS_SELECTOR, "span[class*='text-body-small']")
                            if location_elems:
                                exp_data["location"] = location_elems[-1].text.strip()
                        except:
                            pass
                        
                        # Extract description
                        try:
                            desc_elem = item.find_element(By.CSS_SELECTOR, "div[class*='show-more']")
                            exp_data["description"] = desc_elem.text.strip()
                        except:
                            pass
                        
                        if exp_data and ("title" in exp_data or "company" in exp_data):
                            profile_data["experience"].append(exp_data)
                            
                            # Set current company from first experience
                            if not profile_data["current_company"] and "company" in exp_data:
                                profile_data["current_company"] = exp_data["company"]
                    
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Error extracting experience: {str(e)}")
            
            # Extract Education
            try:
                # Scroll to education section
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                
                education_items = []
                
                try:
                    edu_headers = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Education')]")
                    if edu_headers:
                        parent = edu_headers[0].find_element(By.XPATH, "./ancestor::section")
                        edu_list_items = parent.find_elements(By.CSS_SELECTOR, "div[class*='education'] div, li[class*='education']")
                        if edu_list_items:
                            education_items = edu_list_items
                except:
                    pass
                
                if not education_items:
                    try:
                        education_items = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='pvs-entity']")
                    except:
                        pass
                
                for item in education_items[:10]:
                    try:
                        edu_data = {}
                        item_text = item.text
                        
                        if not item_text or "education" not in item_text.lower():
                            continue
                        
                        try:
                            spans = item.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
                            school_name = None
                            degree_name = None
                            
                            for span in spans:
                                span_text = span.text.strip()
                                if span_text and len(span_text) > 3:
                                    if not school_name:
                                        school_name = span_text
                                    elif not degree_name and school_name != span_text:
                                        degree_name = span_text
                                        break
                            
                            if school_name:
                                edu_data["school"] = school_name
                            if degree_name:
                                edu_data["degree"] = degree_name
                        except:
                            pass
                        
                        try:
                            import re
                            dates = re.findall(r'(\d{4}\s*[-–]\s*\d{4}|\d{4})', item_text)
                            if dates:
                                edu_data["duration"] = dates[0]
                        except:
                            pass
                        
                        if edu_data and ("school" in edu_data or "degree" in edu_data):
                            profile_data["education"].append(edu_data)
                    
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Error extracting education: {str(e)}")
            
            # Extract Certifications/Licenses
            try:
                # Scroll to certifications section
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
                time.sleep(2)
                
                certification_items = []
                
                try:
                    cert_headers = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Licenses') or contains(text(), 'Certifications')]")
                    if cert_headers:
                        parent = cert_headers[0].find_element(By.XPATH, "./ancestor::section")
                        cert_list_items = parent.find_elements(By.CSS_SELECTOR, "div[class*='pvs-entity']")
                        if cert_list_items:
                            certification_items = cert_list_items
                except:
                    pass
                
                if not certification_items:
                    try:
                        all_divs = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='pvs-entity']")
                        for div in all_divs:
                            try:
                                text = div.text.lower()
                                if any(keyword in text for keyword in ['certified', 'certification', 'license', 'credential', 'issued']):
                                    certification_items.append(div)
                            except:
                                continue
                    except:
                        pass
                
                for item in certification_items[:15]:
                    try:
                        cert_data = {}
                        item_text = item.text
                        
                        if not item_text:
                            continue
                        
                        try:
                            spans = item.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
                            cert_name = None
                            issuer_name = None
                            
                            for i, span in enumerate(spans):
                                span_text = span.text.strip()
                                if span_text and len(span_text) > 3:
                                    if not cert_name:
                                        cert_name = span_text
                                    elif not issuer_name and issuer_name != span_text:
                                        issuer_name = span_text
                                        break
                            
                            if cert_name:
                                cert_data["name"] = cert_name
                            if issuer_name:
                                cert_data["issuer"] = issuer_name
                        except:
                            pass
                        
                        try:
                            import re
                            dates = re.findall(r'(Issued|Expires)?\s*([A-Za-z]+\s+\d{4})', item_text)
                            if dates:
                                cert_data["date"] = dates[0][1]
                        except:
                            pass
                        
                        if cert_data and ("name" in cert_data or "issuer" in cert_data):
                            profile_data["certifications"].append(cert_data)
                    
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Error extracting certifications: {str(e)}")
            
            # Extract Skills
            try:
                # Click "Show all skills" if available
                try:
                    show_all = self.driver.find_element(By.XPATH, "//a[contains(@href, '/details/skills')]")
                    show_all.click()
                    time.sleep(3)
                    
                    skill_items = self.driver.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
                    skills_list = []
                    for skill in skill_items:
                        skill_text = skill.text.strip()
                        if skill_text and len(skill_text) < 50 and skill_text not in skills_list:
                            skills_list.append(skill_text)
                    
                    profile_data["skills"] = skills_list[:20]
                    
                    self.driver.back()
                    time.sleep(2)
                except:
                    try:
                        skills_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Skills')]")
                        parent = skills_section.find_element(By.XPATH, "./ancestor::section")
                        skill_items = parent.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
                        skills_list = []
                        for skill in skill_items:
                            skill_text = skill.text.strip()
                            if skill_text and len(skill_text) < 50 and skill_text not in skills_list:
                                skills_list.append(skill_text)
                        profile_data["skills"] = skills_list[:10]
                    except:
                        print("Could not extract skills")
                    
            except Exception as e:
                print(f"Error extracting skills: {str(e)}")
            
            # Extract Languages
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                languages = []
                
                try:
                    lang_headers = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Languages')]")
                    if lang_headers:
                        parent = lang_headers[0].find_element(By.XPATH, "./ancestor::section")
                        lang_spans = parent.find_elements(By.CSS_SELECTOR, "span[aria-hidden='true']")
                        for span in lang_spans:
                            lang_text = span.text.strip()
                            if lang_text and len(lang_text) < 50 and lang_text != "Languages":
                                languages.append(lang_text)
                except Exception as e:
                    print(f"Debug: Languages extraction error: {str(e)}")
                
                if not languages:
                    try:
                        all_spans = self.driver.find_elements(By.TAG_NAME, "span")
                        for i, span in enumerate(all_spans):
                            text = span.text.strip()
                            if text == "Languages":
                                next_elements = all_spans[i+1:i+15]
                                for elem in next_elements:
                                    lang_text = elem.text.strip()
                                    if lang_text and len(lang_text) < 30 and lang_text not in ["Languages", "+", "show all"]:
                                        languages.append(lang_text)
                                        if len(languages) >= 5:
                                            break
                                break
                    except Exception as e:
                        print(f" fallback languages extraction error: {str(e)}")
                
                if languages:
                    profile_data["languages"] = languages
                    
            except Exception as e:
                print(f"Error extracting languages: {str(e)}")
            
            return profile_data
            
        except Exception as e:
            print(f"Error scraping profile: {str(e)}")
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def scrape_linkedin_profile(profile_url, email=None, password=None, headless=False, manual_login=False):
    """
    Convenience function to scrape a single LinkedIn profile
    
    Args:
        profile_url: URL of the LinkedIn profile (e.g., https://www.linkedin.com/in/username)
        email: LinkedIn account email (optional, not needed for manual_login)
        password: LinkedIn account password (optional, not needed for manual_login)
        headless: Run browser in headless mode
        manual_login: If True, opens browser for manual login (supports Google Google)
        
    Returns:
        dict: Dictionary containing profile data
    """
    with LinkedInProfileScraper(email=email, password=password, headless=headless, manual_login=manual_login) as scraper:
        return scraper.scrape_profile(profile_url)


if __name__ == "__main__":
    # LinkedIn Profile Scraper
    print("\nLinkedIn Profile Scraper")
    print("=" * 50)
    
    profile_url = input("\nEnter LinkedIn profile URL: ")
    
    # Ask about login method
    print("\nLogin Options:")
    print("1. No login (limited access)")
    print("2. Manual login (supports Google/Microsoft OAuth)")
    print("3. Email/Password login")
    
    choice = input("\nSelect option (1/2/3): ").strip()
    
    if choice == "1":
        data = scrape_linkedin_profile(profile_url)
    elif choice == "2":
        data = scrape_linkedin_profile(profile_url, manual_login=True)
    elif choice == "3":
        email = input("Enter your LinkedIn email: ")
        password = input("Enter your LinkedIn password: ")
        data = scrape_linkedin_profile(profile_url, email=email, password=password)
    else:
        print("Invalid choice. Using no login mode.")
        data = scrape_linkedin_profile(profile_url)
    
    if data:
        print("\n" + "="*50)
        print("PROFILE DATA")
        print("="*50)
        print(json.dumps(data, indent=2))
        
        # Save to file
        save = input("\nSave to file? (y/n): ").lower()
        if save == 'y':
            filename = f"profile_{data.get('name', 'unknown').replace(' ', '_')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved to {filename}")
    else:
        print("Failed to scrape profile data")
