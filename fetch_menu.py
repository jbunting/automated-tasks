#!/usr/bin/env python3
"""
School Lunch Menu to ICS Calendar Converter

This script fetches the school lunch menu from the School Nutrition and Fitness website
and converts it into an ICS calendar file that can be imported into Google Calendar,
Home Assistant, and other calendar applications.
"""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from dateutil.parser import parse as parse_date


class MenuFetcher:
    """Fetches and parses school lunch menu data."""

    def __init__(self, menu_id: str, site_code: str):
        self.menu_id = menu_id
        self.site_code = site_code
        self.base_url = "https://www.schoolnutritionandfitness.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_menu_data(self) -> Optional[Dict]:
        """
        Fetch menu data from the API.
        The site likely has an API endpoint that returns JSON data.
        """
        # Try common API patterns
        api_urls = [
            f"{self.base_url}/api/menu/{self.menu_id}",
            f"{self.base_url}/api/menus/{self.menu_id}",
            f"{self.base_url}/api/v1/menu/{self.menu_id}",
            f"{self.base_url}/webmenus2/api/menu/{self.menu_id}",
        ]

        for api_url in api_urls:
            try:
                print(f"Trying API endpoint: {api_url}")
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✓ Successfully fetched data from {api_url}")
                        return data
                    except json.JSONDecodeError:
                        continue
            except requests.RequestException as e:
                print(f"  Failed: {e}")
                continue

        # If API endpoints don't work, try fetching the page and looking for embedded JSON
        print("\nAPI endpoints didn't work, trying to parse the page...")
        return self.fetch_from_page()

    def fetch_from_page(self) -> Optional[Dict]:
        """Fetch menu data embedded in the page HTML."""
        url = f"{self.base_url}/webmenus2/#/view?id={self.menu_id}&siteCode={self.site_code}"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch page: HTTP {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for JSON data in script tags
            for script in soup.find_all('script'):
                if script.string and 'menu' in script.string.lower():
                    # Try to extract JSON objects
                    json_matches = re.findall(r'\{[\s\S]*?\}', script.string)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if self.validate_menu_data(data):
                                print("✓ Found valid menu data in page")
                                return data
                        except json.JSONDecodeError:
                            continue

            print("Could not find menu data in page")
            return None

        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def validate_menu_data(self, data: Dict) -> bool:
        """Check if the data looks like menu data."""
        # Basic validation - adjust based on actual data structure
        if not isinstance(data, dict):
            return False

        # Look for common menu-related keys
        menu_keys = ['menu', 'items', 'dates', 'days', 'meals', 'calendar']
        return any(key in str(data).lower() for key in menu_keys)


class MenuParser:
    """Parses menu data and extracts meal information."""

    @staticmethod
    def parse_menu(data: Dict) -> List[Dict]:
        """
        Parse menu data and return a list of meal events.

        Returns:
            List of dicts with keys: date, title, description
        """
        events = []

        # The actual structure will depend on the API response
        # This is a flexible parser that handles common patterns

        if isinstance(data, dict):
            # Pattern 1: menu with days array
            if 'days' in data:
                events.extend(MenuParser._parse_days_format(data['days']))

            # Pattern 2: menu with dates object
            elif 'dates' in data:
                events.extend(MenuParser._parse_dates_format(data['dates']))

            # Pattern 3: menu with items array
            elif 'items' in data:
                events.extend(MenuParser._parse_items_format(data['items']))

            # Pattern 4: nested menu data
            elif 'menu' in data:
                events.extend(MenuParser.parse_menu(data['menu']))

        return events

    @staticmethod
    def _parse_days_format(days: List) -> List[Dict]:
        """Parse menu data in 'days' format."""
        events = []
        for day in days:
            if not isinstance(day, dict):
                continue

            date = day.get('date')
            items = day.get('items', []) or day.get('meals', [])

            if date and items:
                # Combine all items into description
                description = '\n'.join(str(item) for item in items if item)
                events.append({
                    'date': MenuParser._parse_date(date),
                    'title': 'School Lunch',
                    'description': description
                })

        return events

    @staticmethod
    def _parse_dates_format(dates: Dict) -> List[Dict]:
        """Parse menu data in 'dates' format (date -> items mapping)."""
        events = []
        for date_str, items in dates.items():
            try:
                date = MenuParser._parse_date(date_str)
                if isinstance(items, list):
                    description = '\n'.join(str(item) for item in items if item)
                else:
                    description = str(items)

                events.append({
                    'date': date,
                    'title': 'School Lunch',
                    'description': description
                })
            except (ValueError, TypeError):
                continue

        return events

    @staticmethod
    def _parse_items_format(items: List) -> List[Dict]:
        """Parse menu data in 'items' format."""
        events = []
        for item in items:
            if not isinstance(item, dict):
                continue

            date = item.get('date') or item.get('day')
            menu = item.get('menu') or item.get('items') or item.get('description')

            if date and menu:
                events.append({
                    'date': MenuParser._parse_date(date),
                    'title': 'School Lunch',
                    'description': str(menu)
                })

        return events

    @staticmethod
    def _parse_date(date_input) -> datetime:
        """Parse various date formats."""
        if isinstance(date_input, datetime):
            return date_input

        if isinstance(date_input, str):
            return parse_date(date_input)

        raise ValueError(f"Cannot parse date: {date_input}")


class ICSGenerator:
    """Generates ICS calendar files from meal events."""

    @staticmethod
    def generate_calendar(events: List[Dict], output_path: Path) -> bool:
        """
        Generate an ICS calendar file.

        Args:
            events: List of event dicts with date, title, description
            output_path: Path to save the ICS file

        Returns:
            True if successful
        """
        cal = Calendar()
        cal.add('prodid', '-//School Lunch Menu//EN')
        cal.add('version', '2.0')
        cal.add('X-WR-CALNAME', 'School Lunch Menu')
        cal.add('X-WR-TIMEZONE', 'America/New_York')  # Adjust as needed
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

            # Set timestamp
            event.add('dtstamp', datetime.now())

            cal.add_component(event)

        # Write to file
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
    # Configuration
    MENU_ID = "68b708e20b1ac86f9b4efcfc"
    SITE_CODE = "4657"
    OUTPUT_DIR = Path("docs")  # GitHub Pages serves from docs/
    OUTPUT_FILE = OUTPUT_DIR / "school-lunch.ics"

    print("School Lunch Menu to ICS Converter")
    print("=" * 50)

    # Fetch menu data
    fetcher = MenuFetcher(MENU_ID, SITE_CODE)
    menu_data = fetcher.fetch_menu_data()

    if not menu_data:
        print("\n❌ Failed to fetch menu data")
        print("\nTroubleshooting:")
        print("1. Check if the menu ID and site code are correct")
        print("2. The website might require JavaScript - consider using Selenium")
        print("3. Try downloading the PDF version and parsing it instead")
        sys.exit(1)

    # Parse menu data
    print("\nParsing menu data...")
    parser = MenuParser()
    events = parser.parse_menu(menu_data)

    if not events:
        print("❌ No events found in menu data")
        print("\nMenu data structure:")
        print(json.dumps(menu_data, indent=2)[:500])
        sys.exit(1)

    print(f"✓ Found {len(events)} meal events")

    # Generate ICS file
    print("\nGenerating ICS calendar...")
    generator = ICSGenerator()
    success = generator.generate_calendar(events, OUTPUT_FILE)

    if success:
        print("\n✅ Success! Calendar file created")
        print(f"\nTo subscribe in Google Calendar:")
        print(f"1. Go to Google Calendar settings")
        print(f"2. Click 'Add calendar' → 'From URL'")
        print(f"3. Enter: https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics")
        print(f"\nFor Home Assistant, add to configuration.yaml:")
        print(f"  - platform: ical")
        print(f"    name: School Lunch")
        print(f"    url: https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics")
    else:
        print("\n❌ Failed to generate calendar")
        sys.exit(1)


if __name__ == "__main__":
    main()
