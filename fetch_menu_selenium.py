#!/usr/bin/env python3
"""
School Lunch Menu Scraper using Selenium

This version uses Selenium to handle JavaScript-rendered content,
which is likely needed for the School Nutrition and Fitness website.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from icalendar import Calendar, Event


class SeleniumMenuFetcher:
    """Fetches menu data using Selenium for JavaScript-rendered pages."""

    def __init__(self, menu_id: str, site_code: str, headless: bool = True):
        self.menu_id = menu_id
        self.site_code = site_code
        self.url = f"https://www.schoolnutritionandfitness.com/webmenus2/#/view?id={menu_id}&siteCode={site_code}"
        self.headless = headless

    def setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless=new')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def fetch_menu_html(self) -> Optional[Dict]:
        """Fetch and parse the menu page with Selenium."""
        driver = None

        try:
            print(f"Opening page: {self.url}")
            driver = self.setup_driver()
            driver.get(self.url)

            # Wait for the page to load - adjust selector based on actual page
            print("Waiting for menu to load...")
            wait = WebDriverWait(driver, 20)

            # Try to find common menu-related elements
            possible_selectors = [
                (By.CLASS_NAME, 'menu-item'),
                (By.CLASS_NAME, 'menu-day'),
                (By.CLASS_NAME, 'calendar'),
                (By.CLASS_NAME, 'meal'),
                (By.TAG_NAME, 'table'),
                (By.CSS_SELECTOR, '[class*="menu"]'),
                (By.CSS_SELECTOR, '[class*="lunch"]'),
            ]

            menu_element = None
            for by, selector in possible_selectors:
                try:
                    menu_element = wait.until(
                        EC.presence_of_element_located((by, selector))
                    )
                    print(f"✓ Found menu element using: {selector}")
                    break
                except:
                    continue

            # Give it a bit more time to fully render
            time.sleep(3)

            # Extract menu data
            menu_data = self.extract_menu_data(driver)

            # Take a screenshot for debugging
            screenshot_path = Path('menu_screenshot.png')
            driver.save_screenshot(str(screenshot_path))
            print(f"Screenshot saved to {screenshot_path}")

            return menu_data

        except Exception as e:
            print(f"Error fetching menu: {e}")
            if driver:
                # Save page source for debugging
                with open('page_source.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("Page source saved to page_source.html")
            return None

        finally:
            if driver:
                driver.quit()

    def extract_menu_data(self, driver) -> Dict:
        """Extract menu data from the loaded page."""
        menu_data = {'events': []}

        # Try to find calendar/table structure
        try:
            # Look for tables
            tables = driver.find_elements(By.TAG_NAME, 'table')
            if tables:
                menu_data['events'] = self._parse_table(tables[0])
                return menu_data

            # Look for divs with date information
            date_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="date"], [class*="day"]')
            if date_elements:
                menu_data['events'] = self._parse_date_elements(date_elements)
                return menu_data

            # Fallback: get all text content
            body = driver.find_element(By.TAG_NAME, 'body')
            menu_data['raw_text'] = body.text

        except Exception as e:
            print(f"Error extracting menu data: {e}")

        return menu_data

    def _parse_table(self, table_element) -> List[Dict]:
        """Parse menu from an HTML table."""
        events = []

        try:
            rows = table_element.find_elements(By.TAG_NAME, 'tr')

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td') or row.find_elements(By.TAG_NAME, 'th')

                if len(cells) >= 2:
                    # Assume first cell is date, rest is menu
                    date_text = cells[0].text.strip()
                    menu_text = ' | '.join(cell.text.strip() for cell in cells[1:] if cell.text.strip())

                    if date_text and menu_text:
                        try:
                            # Try to parse the date
                            date = self._parse_date_text(date_text)
                            if date:
                                events.append({
                                    'date': date,
                                    'title': 'School Lunch',
                                    'description': menu_text
                                })
                        except:
                            continue

        except Exception as e:
            print(f"Error parsing table: {e}")

        return events

    def _parse_date_elements(self, elements) -> List[Dict]:
        """Parse menu from date-labeled elements."""
        events = []

        for element in elements:
            try:
                text = element.text.strip()
                # Look for date patterns
                date = self._parse_date_text(text)
                if date:
                    # Find associated menu items (next siblings, parent, etc.)
                    # This will need to be customized based on actual HTML structure
                    parent = element.find_element(By.XPATH, '..')
                    menu_text = parent.text.strip()

                    events.append({
                        'date': date,
                        'title': 'School Lunch',
                        'description': menu_text
                    })
            except:
                continue

        return events

    def _parse_date_text(self, text: str) -> Optional[datetime]:
        """Try to parse a date from text."""
        import re
        from dateutil.parser import parse as date_parse

        # Common date patterns
        patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or M/D/YY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'[A-Za-z]+\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return date_parse(match.group())
                except:
                    continue

        return None


def generate_ics(events: List[Dict], output_path: Path) -> bool:
    """Generate ICS file from events."""
    cal = Calendar()
    cal.add('prodid', '-//School Lunch Menu//EN')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', 'School Lunch Menu')
    cal.add('X-WR-CALDESC', 'Automated school lunch menu calendar')

    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('description', event_data['description'])

        # Set as all-day event
        date = event_data['date']
        event.add('dtstart', date.date())
        event.add('dtend', (date + timedelta(days=1)).date())

        # Add unique ID
        uid = f"{date.strftime('%Y%m%d')}-lunch@automated-tasks"
        event.add('uid', uid)
        event.add('dtstamp', datetime.now())

        cal.add_component(event)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(cal.to_ical())
        print(f"✓ Calendar written to {output_path}")
        return True
    except Exception as e:
        print(f"Error writing calendar: {e}")
        return False


def main():
    """Main execution function."""
    MENU_ID = "68b708e20b1ac86f9b4efcfc"
    SITE_CODE = "4657"
    OUTPUT_DIR = Path("docs")
    OUTPUT_FILE = OUTPUT_DIR / "school-lunch.ics"

    print("School Lunch Menu Scraper (Selenium)")
    print("=" * 50)

    fetcher = SeleniumMenuFetcher(MENU_ID, SITE_CODE)
    menu_data = fetcher.fetch_menu_html()

    if not menu_data or not menu_data.get('events'):
        print("\n❌ Failed to fetch menu data or no events found")
        print("\nCheck the saved files:")
        print("- menu_screenshot.png: Visual of the loaded page")
        print("- page_source.html: HTML source for debugging")

        if menu_data and menu_data.get('raw_text'):
            print("\nExtracted text from page:")
            print(menu_data['raw_text'][:500])

        return

    events = menu_data['events']
    print(f"\n✓ Found {len(events)} meal events")

    # Show sample events
    if events:
        print("\nSample events:")
        for event in events[:3]:
            print(f"  {event['date'].strftime('%Y-%m-%d')}: {event['description'][:50]}...")

    success = generate_ics(events, OUTPUT_FILE)

    if success:
        print("\n✅ Success! Calendar file created")
    else:
        print("\n❌ Failed to generate calendar")


if __name__ == "__main__":
    main()
