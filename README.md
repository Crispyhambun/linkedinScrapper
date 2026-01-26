# LinkedIn Profile Scraper

A comprehensive Python-based web scraper for LinkedIn profiles. Extract work experience, education, certifications, skills, and more from any LinkedIn profile.

## Features

- 👤 Extract name, headline, and location
- 💼 Get current company and full work experience history
- 🎓 Retrieve education history
- 📜 Extract certifications and licenses
- 💡 Get skills list
- 📄 Extract about/summary section
- 🔐 Multiple login options (manual/Google OAuth, email/password)
- 🚀 Batch scrape multiple profiles efficiently
- 💾 Save data to JSON files

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

The scraper will automatically download the appropriate ChromeDriver for your system.

## Quick Start

### Basic Usage

```python
from linkedin_scraper import scrape_linkedin_profile

profile_url = "https://www.linkedin.com/in/username/"
data = scrape_linkedin_profile(profile_url, manual_login=True)

print(f"Name: {data['name']}")
print(f"Current Company: {data['current_company']}")
print(f"Experience: {len(data['experience'])} positions")
print(f"Skills: {data['skills']}")
```

### With Email/Password Login

```python
from linkedin_scraper import scrape_linkedin_profile

profile_url = "https://www.linkedin.com/in/username/"
data = scrape_linkedin_profile(
    profile_url,
    email="your-email@example.com",
    password="your-password"
)

print(data)
```

### Interactive Mode

Run the scraper directly:
```bash
python linkedin_scraper.py
```

You'll be prompted to:
1. Enter a LinkedIn profile URL
2. Select login method (no login, manual login with Google OAuth, or email/password)

## Data Structure

The scraper returns a dictionary with the following structure:

```json
{
  "url": "https://www.linkedin.com/in/username/",
  "name": "John Doe",
  "headline": "Software Engineer at Tech Company",
  "location": "San Francisco, CA",
  "about": "Passionate software engineer with 10+ years...",
  "current_company": "Tech Company",
  "experience": [
    {
      "title": "Senior Software Engineer",
      "company": "Tech Company",
      "duration": "Jan 2020 - Present · 4 yrs",
      "location": "San Francisco, CA",
      "description": "Leading development of..."
    }
  ],
  "education": [
    {
      "school": "University Name",
      "degree": "Bachelor of Science - Computer Science",
      "duration": "2010 - 2014"
    }
  ],
  "certifications": [
    {
      "name": "AWS Certified Solutions Architect",
      "issuer": "Amazon Web Services",
      "date": "Issued Jan 2023"
    }
  ],
  "skills": ["Python", "JavaScript", "AWS", "Docker"],
  "languages": []
}
```

## Advanced Usage

### Scrape Multiple Profiles

```python
from linkedin_scraper import LinkedInProfileScraper

profile_urls = [
    "https://www.linkedin.com/in/person1/",
    "https://www.linkedin.com/in/person2/",
    "https://www.linkedin.com/in/person3/"
]

# Use context manager to reuse browser session
with LinkedInProfileScraper(manual_login=True) as scraper:
    for url in profile_urls:
        data = scraper.scrape_profile(url)
        print(f"{data['name']} - {data['current_company']}")
```

### Headless Mode

Run the browser in background (no visible window):

```python
data = scrape_linkedin_profile(
    profile_url,
    email="your-email@example.com",
    password="your-password",
    headless=True
)
```

### Save Profile Data to JSON File

```python
import json
from linkedin_scraper import scrape_linkedin_profile

profile_url = "https://www.linkedin.com/in/username/"
data = scrape_linkedin_profile(profile_url, manual_login=True)

if data:
    filename = f"profile_{data['name'].replace(' ', '_')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {filename}")
```

## Examples

Check out **[profile_scraper_example.py](profile_scraper_example.py)** for detailed examples:

1. Simple profile scrape
2. Extract work experience
3. Extract education & certifications
4. Scrape multiple profiles
5. Save profile to JSON
6. Extract skills
7. Compare two profiles

## Important Notes

### LinkedIn's Terms of Service
- This scraper is for educational purposes only
- Be respectful of LinkedIn's rate limits
- Avoid scraping too frequently to prevent account restrictions
- Review LinkedIn's Terms of Service before using

### Login Credentials
- Login provides access to more complete data
- Your credentials are only used locally and never stored
- Consider using environment variables for credentials:

```python
import os

email = os.getenv('LINKEDIN_EMAIL')
password = os.getenv('LINKEDIN_PASSWORD')
```

### Browser Requirements
- Chrome browser should be installed on your system
- ChromeDriver is automatically downloaded by webdriver-manager
- Internet connection required

## Troubleshooting

### Common Issues

**Issue: "Could not extract [field]"**
- Some fields may not be available depending on post privacy settings
- Try logging in for full access

**Issue: Login fails**
- Verify your credentials are correct
- LinkedIn may require 2FA - disable it temporarily or handle manually
- Check for CAPTCHA challenges

**Issue: Slow performance**
- Increase wait times in the code if needed
- Use headless mode for faster execution
- LinkedIn pages can take time to fully load

**Issue: Browser doesn't close**
- Use context manager (`with` statement) to ensure proper cleanup
- Manually call `scraper.close()` when done

**Issue: Can't extract all profile data**
- Login is required for full profile access
- Use `manual_login=True` for best results
- Some profiles may have privacy settings limiting data access
- Scroll behavior may need adjustment for longer profiles

## Requirements

- Python 3.7+
- Chrome browser
- Internet connection
- Dependencies listed in requirements.txt

## Project Structure

```
linkedInScrapper/
├── linkedin_scraper.py          # Main scraper module (posts & profiles)
├── example.py                   # Post scraping examples
├── profile_scraper_example.py   # Profile scraping examples
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Use Cases

- 🔍 Recruit and analyze candidates
- 📊 Research industry professionals
- 🤝 Build contact databases
- 📈 Analyze career paths and trends
- 🎯 Verify credentials and experience
- 💼 Competitive intelligence
- 🎓 Academic research

## Contributing

Feel free to submit issues or pull requests for improvements!

## License

This project is provided as-is for educational purposes.

## Disclaimer

This tool is for educational and research purposes only. Web scraping may violate LinkedIn's Terms of Service. Use responsibly and at your own risk. The authors are not responsible for any misuse or consequences resulting from the use of this tool.
