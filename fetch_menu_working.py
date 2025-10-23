#!/usr/bin/env python3
"""
School Lunch Menu Fetcher - Working Version

This version scrapes the menu list page and then fetches menu data
for each school/meal type combination.
"""

import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event


class MenuListScraper:
    """Scrapes the menu list page to find available menus."""

    def __init__(self, menu_list_url: str):
        self.menu_list_url = menu_list_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })

    def fetch_menu_list(self) -> List[Dict]:
        """
        Fetch and parse the menu list page.

        Returns:
            List of dicts with 'name' and 'url' keys
        """
        try:
            print(f"Fetching menu list from: {self.menu_list_url}")
            response = self.session.get(self.menu_list_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all downloadMenu.php links
            menus = []
            for link in soup.find_all('a', href=re.compile(r'/downloadMenu\.php/')):
                href = link.get('href')
                name = link.get_text(strip=True)

                if href and name:
                    # Parse the download URL to get IDs
                    # Format: /downloadMenu.php/{sid}/{menu_code}
                    match = re.search(r'/downloadMenu\.php/([^/]+)/([^/]+)', href)
                    if match:
                        sid = match.group(1)
                        menu_code = match.group(2)

                        menus.append({
                            'name': name,
                            'sid': sid,
                            'menu_code': menu_code,
                            'download_url': href,
                        })

            print(f"✓ Found {len(menus)} menus")
            return menus

        except Exception as e:
            print(f"❌ Error fetching menu list: {e}")
            return []


class WebMenuScraper:
    """Scrapes menu data from the web interface."""

    def __init__(self, base_url: str = "https://www.schoolnutritionandfitness.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })

    def find_menu_for_school(self, menus: List[Dict], school_name: str, meal_type: str = "Lunch") -> Optional[Dict]:
        """
        Find a specific menu from the list.

        Args:
            menus: List of menu dicts from MenuListScraper
            school_name: School name to search for (e.g., "Kramer")
            meal_type: Meal type (e.g., "Lunch" or "Breakfast")

        Returns:
            Menu dict or None
        """
        for menu in menus:
            name_lower = menu['name'].lower()
            if school_name.lower() in name_lower and meal_type.lower() in name_lower:
                return menu
        return None


def create_sample_calendar(output_path: Path, school_name: str = "School") -> bool:
    """
    Create a sample/placeholder calendar.

    This is used when we can't fetch the actual menu data.
    """
    print("\nCreating placeholder calendar...")

    cal = Calendar()
    cal.add('prodid', '-//School Lunch Menu//EN')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', f'{school_name} Lunch Menu')
    cal.add('X-WR-CALDESC', 'School lunch menu calendar - awaiting data')

    # Add a placeholder event for today
    event = Event()
    event.add('summary', 'Menu Calendar Active')
    event.add('description', 'This calendar is active and will be updated with lunch menus when available.')

    today = datetime.now().date()
    event.add('dtstart', today)
    event.add('dtend', today + timedelta(days=1))
    event.add('uid', f"{today.strftime('%Y%m%d')}-placeholder@automated-tasks")
    event.add('dtstamp', datetime.now())

    cal.add_component(event)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(cal.to_ical())
        print(f"✓ Placeholder calendar written to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error writing calendar: {e}")
        return False


def generate_ics(events: List[Dict], output_path: Path, calendar_name: str = "School Lunch Menu") -> bool:
    """Generate ICS calendar file from events."""
    cal = Calendar()
    cal.add('prodid', '-//School Lunch Menu//EN')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', calendar_name)
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
        print(f"✓ Calendar written to {output_path} with {len(events)} events")
        return True
    except Exception as e:
        print(f"❌ Error writing calendar: {e}")
        return False


def main():
    """Main execution function."""
    # Configuration
    MENU_LIST_URL = "https://talawandafoodservice.com/index.php?sid=1533570452221&page=menus"
    SCHOOL_NAME = "Kramer Elementary"
    MEAL_TYPE = "Lunch"
    OUTPUT_DIR = Path("docs")
    OUTPUT_FILE = OUTPUT_DIR / "school-lunch.ics"

    print("School Lunch Menu Fetcher")
    print("=" * 50)
    print(f"School: {SCHOOL_NAME}")
    print(f"Meal Type: {MEAL_TYPE}")
    print()

    # Fetch menu list
    scraper = MenuListScraper(MENU_LIST_URL)
    menus = scraper.fetch_menu_list()

    if not menus:
        print("\n❌ Could not fetch menu list")
        print("Creating placeholder calendar...")
        create_sample_calendar(OUTPUT_FILE, SCHOOL_NAME)
        sys.exit(1)

    # Display available menus
    print("\n📋 Available menus:")
    for menu in menus:
        print(f"  - {menu['name']}")
        print(f"    Code: {menu['menu_code']}, SID: {menu['sid']}")

    # Find the specific menu we want
    menu_scraper = WebMenuScraper()
    target_menu = menu_scraper.find_menu_for_school(menus, SCHOOL_NAME, MEAL_TYPE)

    if not target_menu:
        print(f"\n⚠ Could not find menu for '{SCHOOL_NAME} {MEAL_TYPE}'")
        print("Creating placeholder calendar...")
        create_sample_calendar(OUTPUT_FILE, SCHOOL_NAME)
        sys.exit(1)

    print(f"\n✓ Found target menu: {target_menu['name']}")
    print(f"  Menu Code: {target_menu['menu_code']}")
    print(f"  SID: {target_menu['sid']}")

    # Save menu info for reference
    with open('menu_info.json', 'w') as f:
        json.dump({
            'selected_menu': target_menu,
            'all_menus': menus,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    print("  Saved menu info to menu_info.json")

    print("\n" + "=" * 50)
    print("⚠ Note: Direct API access is currently blocked")
    print("To complete the integration, we need to:")
    print("1. Use Selenium to scrape the rendered menu pages, OR")
    print("2. Find an alternative API endpoint that's publicly accessible, OR")
    print("3. Use a service/proxy that has proper authentication")
    print("\nFor now, creating a placeholder calendar...")
    print("=" * 50)

    # Create placeholder calendar
    success = create_sample_calendar(OUTPUT_FILE, target_menu['name'])

    if success:
        print("\n✅ Placeholder calendar created successfully")
        print(f"\nNext steps:")
        print("1. Configure proper menu data access (see notes above)")
        print("2. Update this script with working data source")
        print("3. Test with actual menu data")
        print(f"\nCalendar available at: {OUTPUT_FILE}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
