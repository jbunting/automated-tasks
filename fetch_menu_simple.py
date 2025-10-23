#!/usr/bin/env python3
"""
School Lunch Menu Fetcher - Simple API-based version

Uses the discovered API endpoints to fetch menu data directly.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import requests
from icalendar import Calendar, Event


class SchoolMenuFetcher:
    """Fetches menu data using the School Nutrition API."""

    def __init__(self, menu_type_id: str):
        """
        Initialize the fetcher.

        Args:
            menu_type_id: The menu type ID (e.g., '62eaf1787057ec305d5532cb')
        """
        self.menu_type_id = menu_type_id
        self.base_url = "https://www.schoolnutritionandfitness.com/webmenus2/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.schoolnutritionandfitness.com/webmenus2/',
            'Origin': 'https://www.schoolnutritionandfitness.com',
            'X-Requested-With': 'XMLHttpRequest',
        })

    def fetch_menu_type(self) -> Optional[Dict]:
        """
        Fetch the menu type data which includes all available months.

        Returns:
            Dict with menu type data including list of all menus
        """
        url = f"{self.base_url}/menutypeController.php/show?_id={self.menu_type_id}"

        try:
            print(f"Fetching menu type from: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(f"✓ Successfully fetched menu type: {data.get('name', 'Unknown')}")
            return data
        except Exception as e:
            print(f"❌ Error fetching menu type: {e}")
            return None

    def fetch_menu_details(self, menu_id: str) -> Optional[Dict]:
        """
        Fetch detailed menu data for a specific month.

        Args:
            menu_id: The specific menu ID (e.g., '68b708e20b1ac86f9b4efcfc')

        Returns:
            Dict with detailed menu data including days and items
        """
        # Try different possible API endpoints
        possible_urls = [
            f"{self.base_url}/menuController.php/show?_id={menu_id}",
            f"{self.base_url}/menu/{menu_id}",
            f"https://www.schoolnutritionandfitness.com/webmenus2/index.php/api/menu/{menu_id}",
        ]

        for url in possible_urls:
            try:
                print(f"Trying: {url}")
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data and 'days' in data:
                            print(f"✓ Successfully fetched menu details from {url}")
                            return data
                    except json.JSONDecodeError:
                        continue
            except requests.RequestException:
                continue

        print(f"⚠ Could not fetch details for menu {menu_id}")
        return None

    def get_current_and_next_month_menus(self, menu_type_data: Dict) -> List[Dict]:
        """
        Get the current and next month's menus from the menu type data.

        Args:
            menu_type_data: The menu type data from API

        Returns:
            List of menu dictionaries for current and next month
        """
        if 'menus' not in menu_type_data:
            return []

        now = datetime.now()
        current_month = now.month - 1  # API uses 0-indexed months
        current_year = now.year

        # Also get next month
        next_month_date = now + timedelta(days=32)
        next_month = next_month_date.month - 1
        next_year = next_month_date.year

        target_months = [
            (current_year, current_month),
            (next_year, next_month)
        ]

        matching_menus = []
        for menu in menu_type_data['menus']:
            menu_year = menu.get('year')
            menu_month = menu.get('month')

            if (menu_year, menu_month) in target_months:
                matching_menus.append(menu)
                print(f"Found menu for {menu_year}/{menu_month + 1}: {menu.get('id')}")

        return matching_menus

    def parse_menu_days(self, menu_data: Dict) -> List[Dict]:
        """
        Parse menu days into calendar events.

        Args:
            menu_data: The detailed menu data with days array

        Returns:
            List of event dictionaries
        """
        events = []

        if 'days' not in menu_data or not menu_data['days']:
            print("⚠ No days found in menu data")
            return events

        year = menu_data.get('year', datetime.now().year)
        month = menu_data.get('month', 0) + 1  # Convert from 0-indexed to 1-indexed

        for day in menu_data['days']:
            try:
                # Get the day number
                day_num = day.get('day', day.get('dayNum'))
                if not day_num:
                    continue

                # Create date
                date = datetime(year, month, int(day_num))

                # Get menu items
                items = []

                # Days can have different structures, try common ones
                if 'menu_items' in day:
                    for item in day['menu_items']:
                        if isinstance(item, dict):
                            items.append(item.get('name', item.get('text', str(item))))
                        else:
                            items.append(str(item))

                elif 'items' in day:
                    for item in day['items']:
                        if isinstance(item, dict):
                            items.append(item.get('name', item.get('text', str(item))))
                        else:
                            items.append(str(item))

                elif 'recipes' in day:
                    for recipe in day['recipes']:
                        if isinstance(recipe, dict):
                            items.append(recipe.get('name', recipe.get('recipeName', str(recipe))))
                        else:
                            items.append(str(recipe))

                if items:
                    description = '\n'.join(items)
                    events.append({
                        'date': date,
                        'title': 'School Lunch',
                        'description': description
                    })

            except Exception as e:
                print(f"Error parsing day: {e}")
                continue

        return events


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
        print(f"✓ Calendar written to {output_path}")
        print(f"  Contains {len(events)} events")
        return True
    except Exception as e:
        print(f"❌ Error writing calendar: {e}")
        return False


def main():
    """Main execution function."""
    # Configuration - from your discovery
    MENU_TYPE_ID = "62eaf1787057ec305d5532cb"  # Kramer Elementary Lunch
    OUTPUT_DIR = Path("docs")
    OUTPUT_FILE = OUTPUT_DIR / "school-lunch.ics"

    print("School Lunch Menu Fetcher (API)")
    print("=" * 50)

    # Initialize fetcher
    fetcher = SchoolMenuFetcher(MENU_TYPE_ID)

    # Fetch menu type data (this gives us list of all months)
    menu_type_data = fetcher.fetch_menu_type()
    if not menu_type_data:
        print("\n❌ Failed to fetch menu type data")
        sys.exit(1)

    # Save menu type data for debugging
    with open('debug_menu_type.json', 'w') as f:
        json.dump(menu_type_data, f, indent=2)
    print("Saved menu type data to debug_menu_type.json")

    # Get current and next month menus
    target_menus = fetcher.get_current_and_next_month_menus(menu_type_data)

    if not target_menus:
        print("\n⚠ No menus found for current/next month")
        print("   The menu might not be published yet")
        # Fall back to using the data from menu_type_data directly
        print("\n📋 Available months:")
        for menu in menu_type_data.get('menus', [])[-3:]:  # Show last 3 months
            year = menu.get('year')
            month = menu.get('month', 0) + 1
            menu_id = menu.get('id')
            print(f"   {year}-{month:02d}: {menu_id}")

        # For now, just create a placeholder calendar
        # In production, you might want to use the most recent menu instead
        target_menus = menu_type_data.get('menus', [])[-1:]  # Use last month as fallback

    all_events = []

    # Fetch detailed data for each menu
    for menu in target_menus:
        menu_id = menu.get('id')
        year = menu.get('year')
        month = menu.get('month', 0) + 1

        print(f"\nFetching menu for {year}-{month:02d}...")

        # Try to fetch detailed menu data
        detailed_menu = fetcher.fetch_menu_details(menu_id)

        if detailed_menu:
            # Save for debugging
            with open(f'debug_menu_{year}_{month:02d}.json', 'w') as f:
                json.dump(detailed_menu, f, indent=2)

            events = fetcher.parse_menu_days(detailed_menu)
            all_events.extend(events)
            print(f"✓ Found {len(events)} events for {year}-{month:02d}")
        else:
            print(f"⚠ Using basic menu data from menu type (may not have daily items)")
            # The menu_type_data has basic info but days array is likely empty
            # This is expected - we may need to discover the correct API endpoint

    if all_events:
        # Generate ICS file
        success = generate_ics(all_events, OUTPUT_FILE, menu_type_data.get('name', 'School Lunch'))

        if success:
            print("\n" + "=" * 50)
            print("✅ Success!")
            print(f"\n📅 Created calendar with {len(all_events)} lunch dates")
            print(f"\nNext steps:")
            print("1. Push to GitHub")
            print("2. Enable GitHub Pages in repository settings")
            print("3. Subscribe to: https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics")
        else:
            sys.exit(1)
    else:
        print("\n" + "=" * 50)
        print("⚠ No events found in menu data")
        print("\nThis could mean:")
        print("1. The 'days' data requires a different API endpoint")
        print("2. The menu for this month hasn't been populated yet")
        print("3. We need to discover the correct API for detailed menu data")
        print("\nCheck debug_*.json files for the raw API responses")

        # Create a placeholder calendar anyway
        generate_ics([], OUTPUT_FILE, menu_type_data.get('name', 'School Lunch'))
        sys.exit(1)


if __name__ == "__main__":
    main()
