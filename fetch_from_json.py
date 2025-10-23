#!/usr/bin/env python3
"""
School Lunch Menu Generator from JSON

This script generates an ICS calendar from the menu JSON file.
To update the menu, save the latest JSON from the browser and run this script.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from icalendar import Calendar, Event


def load_menu_json(json_path: Path) -> Optional[Dict]:
    """Load the menu JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        print(f"✓ Loaded menu data from {json_path}")
        return data
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return None


def get_current_and_upcoming_menus(menu_data: Dict, months_ahead: int = 2) -> List[Dict]:
    """
    Get menus for current month and upcoming months.

    Args:
        menu_data: The loaded JSON data
        months_ahead: Number of months ahead to include

    Returns:
        List of menu dictionaries
    """
    if 'menus' not in menu_data:
        return []

    now = datetime.now()
    target_months = []

    # Get current and future months
    for i in range(months_ahead + 1):
        date = now + timedelta(days=32 * i)
        # API uses 0-indexed months (0 = January)
        target_months.append((date.year, date.month - 1))

    matching_menus = []
    for menu in menu_data['menus']:
        year = menu.get('year')
        month = menu.get('month')

        if (year, month) in target_months:
            matching_menus.append(menu)
            month_name = datetime(year, month + 1, 1).strftime('%B %Y')
            print(f"  Including: {month_name}")

    return matching_menus


def parse_menu_to_events(menu: Dict) -> List[Dict]:
    """
    Parse a menu object into calendar events.

    Note: The 'days' array from the API response may be empty in the initial
    response. This function expects the full menu data with populated days.
    """
    events = []

    if 'days' not in menu or not menu['days']:
        year = menu.get('year')
        month = menu.get('month', 0) + 1
        print(f"  ⚠ No daily menu items for {year}-{month:02d}")
        print(f"     The 'days' array is empty - menu may not be published yet")
        return events

    year = menu.get('year')
    month = menu.get('month', 0) + 1

    for day_entry in menu['days']:
        try:
            # Parse day information
            day_num = day_entry.get('day') or day_entry.get('dayNum')
            if not day_num:
                continue

            date = datetime(year, month, int(day_num))

            # Extract menu items from various possible structures
            menu_items = extract_menu_items(day_entry)

            if menu_items:
                description = '\n'.join(menu_items)
                events.append({
                    'date': date,
                    'title': 'School Lunch',
                    'description': description
                })

        except Exception as e:
            print(f"  Warning: Could not parse day entry: {e}")
            continue

    return events


def extract_menu_items(day_entry: Dict) -> List[str]:
    """Extract menu items from a day entry, handling various formats."""
    items = []

    # Try different possible structures
    possible_keys = ['menu_items', 'items', 'recipes', 'menuItems', 'recipeItems']

    for key in possible_keys:
        if key in day_entry and day_entry[key]:
            for item in day_entry[key]:
                if isinstance(item, dict):
                    # Try different name fields
                    name = (item.get('name') or
                           item.get('recipeName') or
                           item.get('text') or
                           item.get('label') or
                           str(item))
                    if name:
                        items.append(str(name))
                else:
                    items.append(str(item))
            break

    # If still no items, try to find any text content
    if not items and 'html' in day_entry:
        # Sometimes menu is in HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(day_entry['html'], 'html.parser')
        text = soup.get_text(strip=True)
        if text:
            items.append(text)

    return items


def generate_ics(events: List[Dict], output_path: Path, calendar_name: str) -> bool:
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
        print(f"\n✓ Calendar written to {output_path}")
        print(f"  Contains {len(events)} events")
        return True
    except Exception as e:
        print(f"\n❌ Error writing calendar: {e}")
        return False


def main():
    """Main execution function."""
    # Configuration
    JSON_PATH = Path("discovery/kramer_elementary_lunch.json")
    OUTPUT_DIR = Path("docs")
    OUTPUT_FILE = OUTPUT_DIR / "school-lunch.ics"

    print("School Lunch Menu Generator (from JSON)")
    print("=" * 50)

    # Load JSON data
    menu_data = load_menu_json(JSON_PATH)
    if not menu_data:
        print("\n❌ Failed to load menu data")
        print(f"\nMake sure {JSON_PATH} exists")
        sys.exit(1)

    menu_name = menu_data.get('name', 'School Lunch Menu')
    print(f"Menu Type: {menu_name}")

    # Get current and upcoming menus
    print(f"\nFinding current and upcoming menus...")
    menus = get_current_and_upcoming_menus(menu_data, months_ahead=2)

    if not menus:
        print("\n⚠ No menus found for current/upcoming months")
        print("\nThis could mean:")
        print("1. The menu JSON needs to be updated with newer data")
        print("2. The current month's menu hasn't been published yet")
        sys.exit(1)

    print(f"✓ Found {len(menus)} relevant menus")

    # Parse all menus into events
    print("\nParsing menu data...")
    all_events = []
    for menu in menus:
        events = parse_menu_to_events(menu)
        all_events.extend(events)
        year = menu.get('year')
        month = menu.get('month', 0) + 1
        month_name = datetime(year, month, 1).strftime('%B %Y')
        print(f"  {month_name}: {len(events)} lunch dates")

    if not all_events:
        print("\n⚠ No events found in menu data")
        print("\nThe 'days' arrays in the JSON are empty.")
        print("\nTo get the full menu data:")
        print("1. Open the menu page in your browser")
        print("2. Open Developer Tools (F12)")
        print("3. Go to Network tab")
        print("4. Reload the page")
        print("5. Look for API calls that return menu data with 'days' populated")
        print("6. Save that response as the JSON file")
        print("\nAlternatively, we need to find the correct API endpoint")
        print("that returns the full menu data with daily items.")
        sys.exit(1)

    # Generate ICS file
    success = generate_ics(all_events, OUTPUT_FILE, menu_name)

    if success:
        print("\n" + "=" * 50)
        print("✅ Success!")
        print(f"\nGenerated calendar with {len(all_events)} lunch dates")
        print(f"\nTo update the menu:")
        print(f"1. Get the latest JSON data (see instructions above)")
        print(f"2. Save it to {JSON_PATH}")
        print(f"3. Run this script again: python3 {Path(__file__).name}")
        print(f"\nCalendar URL (after pushing to GitHub):")
        print(f"https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
