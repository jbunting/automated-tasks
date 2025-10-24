#!/usr/bin/env python3
"""
School Lunch Menu Fetcher - Working Version Using Saved GraphQL Data

Since the GraphQL API requires browser authentication, this script:
1. Uses saved GraphQL JSON responses
2. Parses them into calendar events
3. Generates ICS file

To update monthly:
1. Open the menu page in browser: https://www.schoolnutritionandfitness.com/webmenus2/#/view?id=MENU_ID&siteCode=4657
2. Open Developer Tools (F12) → Network tab
3. Look for GraphQL request to api.isitesoftware.com/graphql
4. Copy the response JSON
5. Save to discovery/menu_YYYY_MM.json
6. Run this script
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from icalendar import Calendar, Event


def find_graphql_json_files(discovery_dir: Path) -> List[Path]:
    """Find all GraphQL JSON files in the discovery directory."""
    json_files = []

    # Pattern 1: menu_YYYY_MM.json
    for file in discovery_dir.glob("menu_*.json"):
        json_files.append(file)

    # Pattern 2: *-graphql.json
    for file in discovery_dir.glob("*-graphql.json"):
        json_files.append(file)

    return sorted(json_files)


def load_graphql_json(json_path: Path) -> Optional[Dict]:
    """Load a GraphQL response JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Handle both raw GraphQL response and extracted menu data
        if 'data' in data and 'menu' in data['data']:
            return data['data']['menu']
        elif 'menu' in data:
            return data['menu']
        elif 'items' in data:  # Already extracted menu data
            return data
        else:
            print(f"⚠ Unexpected JSON structure in {json_path}")
            return None

    except Exception as e:
        print(f"❌ Error loading {json_path}: {e}")
        return None


def is_current_or_upcoming_month(year: int, month: int, months_ahead: int = 2) -> bool:
    """Check if a year/month is within the target range."""
    now = datetime.now()
    target_date = datetime(year, month + 1, 1)  # month is 0-indexed

    # Calculate range - include current month even if we're near the end
    # Normalize to start of day for comparison
    earliest = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    latest = (now + timedelta(days=35 * (months_ahead + 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return earliest <= target_date < latest


def parse_graphql_to_events(menu_data: Dict) -> List[Dict]:
    """
    Parse GraphQL menu data into calendar events.

    Args:
        menu_data: The menu data from GraphQL response

    Returns:
        List of event dictionaries
    """
    events = []

    if 'items' not in menu_data or not menu_data['items']:
        print(f"  ⚠ No items in menu data")
        return events

    year = menu_data.get('year')
    month = menu_data.get('month', 0) + 1  # Convert from 0-indexed to 1-indexed

    print(f"  Parsing {datetime(year, month, 1).strftime('%B %Y')}")

    # Group items by day
    days_map = {}
    for item in menu_data['items']:
        # Skip hidden items
        if item.get('hidden'):
            continue

        day_num = item.get('day')
        if not day_num:
            continue

        if day_num not in days_map:
            days_map[day_num] = []

        product = item.get('product', {})
        if product and product.get('name'):
            days_map[day_num].append(product)

    # Create events for each day
    for day_num, products in sorted(days_map.items()):
        try:
            date = datetime(year, month, int(day_num))

            # Skip past dates
            if date.date() < datetime.now().date():
                continue

            # Group products by category
            by_category = {}
            for product in products:
                category = product.get('category', 'Items')
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(product['name'])

            # Format description
            description_parts = []

            # Show entrees first
            main_course = ""
            if 'Entrees' in by_category:
                description_parts.append("Main Dish:")
                for item in by_category['Entrees']:
                    description_parts.append(f"  • {item}")
                    if not main_course:
                        main_course = item
                del by_category['Entrees']

            # Then other categories
            for category, items in sorted(by_category.items()):
                if not category:
                    category = "Sides"
                if items:
                    description_parts.append(f"{category}:")
                    for item in items:
                        description_parts.append(f"  • {item}")

            description = '\n'.join(description_parts)

            title = f"Kramer Lunch: {main_course}" if main_course else "Kramer Lunch" 

            events.append({
                'date': date,
                'title': title,
                'description': description
            })

        except Exception as e:
            print(f"  Warning: Could not parse day {day_num}: {e}")
            continue

    return events


def generate_ics(events: List[Dict], output_path: Path, calendar_name: str) -> bool:
    """Generate ICS calendar file from events."""
    cal = Calendar()
    cal.add('prodid', '-//School Lunch Menu Generator//EN')
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


def print_update_instructions(discovery_dir: Path):
    """Print instructions for updating the menu data."""
    print("\n" + "=" * 50)
    print("📋 To Update the Menu for Next Month:")
    print("=" * 50)
    print("\n1. Open the menu page in your browser:")
    print("   https://www.schoolnutritionandfitness.com/webmenus2/#/view?id=MENU_ID&siteCode=4657")
    print("   (Check the menu list page for the correct MENU_ID)")
    print("\n2. Open Developer Tools (F12) → Network tab")
    print("\n3. Look for a request to: api.isitesoftware.com/graphql")
    print("   - Click on it")
    print("   - Go to 'Response' tab")
    print("   - Copy all the JSON")
    print("\n4. Save the JSON to:")
    now = datetime.now()
    next_month = now + timedelta(days=32)
    example_file = f"menu_{next_month.year}_{next_month.month:02d}.json"
    print(f"   {discovery_dir / example_file}")
    print("\n5. Run this script again:")
    print("   python3 fetch_menu.py")
    print("\n6. Commit and push to GitHub:")
    print("   git add docs/school-lunch.ics")
    print(f"   git add discovery/{example_file}")
    month_name = next_month.strftime("%B %Y")
    print(f'   git commit -m "Update lunch menu for {month_name}"')
    print("   git push")


def main():
    """Main execution function."""
    # Configuration
    DISCOVERY_DIR = Path("discovery")
    OUTPUT_DIR = Path("site")
    OUTPUT_FILE = OUTPUT_DIR / "school-lunch.ics"
    CALENDAR_NAME = "Kramer Elementary Lunch"

    print("School Lunch Menu Calendar Generator")
    print("=" * 50)

    # Find all GraphQL JSON files
    json_files = find_graphql_json_files(DISCOVERY_DIR)

    if not json_files:
        print("\n❌ No GraphQL JSON files found in discovery/")
        print_update_instructions(DISCOVERY_DIR)
        sys.exit(1)

    print(f"\nFound {len(json_files)} JSON file(s):")
    for file in json_files:
        print(f"  - {file.name}")

    # Load and parse all files
    all_events = []

    for json_file in json_files:
        print(f"\nProcessing {json_file.name}...")
        menu_data = load_graphql_json(json_file)

        if not menu_data:
            print(f"  ⚠ Skipping {json_file.name}")
            continue

        # Check if this month is relevant
        year = menu_data.get('year')
        month = menu_data.get('month')

        if year and month is not None:
            if not is_current_or_upcoming_month(year, month, months_ahead=3):
                month_name = datetime(year, month + 1, 1).strftime('%B %Y')
                print(f"  ⏭ Skipping {month_name} (too far past or future)")
                continue

        # Parse events
        events = parse_graphql_to_events(menu_data)
        all_events.extend(events)
        print(f"  ✓ Added {len(events)} lunch dates")

    if not all_events:
        print("\n⚠ No events found in any JSON file")
        print_update_instructions(DISCOVERY_DIR)
        sys.exit(1)

    # Generate ICS file
    success = generate_ics(all_events, OUTPUT_FILE, CALENDAR_NAME)

    if success:
        print("\n" + "=" * 50)
        print("✅ Success!")
        print("=" * 50)
        print(f"\nGenerated calendar with {len(all_events)} upcoming lunch dates")

        # Show date range
        dates = sorted([e['date'] for e in all_events])
        print(f"Date range: {dates[0].strftime('%B %d, %Y')} to {dates[-1].strftime('%B %d, %Y')}")

        print(f"\nCalendar file: {OUTPUT_FILE}")

        print("\n📤 Next steps:")
        print("1. git add docs/school-lunch.ics")
        print('2. git commit -m "Update school lunch calendar"')
        print("3. git push")
        print("\n📅 Subscribe to calendar at:")
        print("   https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics")

        # Check if we need more months
        latest_date = dates[-1]
        months_remaining = (latest_date.year - datetime.now().year) * 12 + (latest_date.month - datetime.now().month)

        if months_remaining < 2:
            print("\n⚠ Note: Less than 2 months of data available")
            print_update_instructions(DISCOVERY_DIR)

        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
