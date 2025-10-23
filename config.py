"""
Configuration file for school lunch menu scraper

Edit these values to match your school's menu information.
"""

# Menu Configuration
# Get these values from your school's menu URL:
# https://www.schoolnutritionandfitness.com/webmenus2/#/view?id=MENU_ID&siteCode=SITE_CODE

MENU_ID = "68b708e20b1ac86f9b4efcfc"
SITE_CODE = "4657"

# Calendar Configuration
CALENDAR_NAME = "School Lunch Menu"
CALENDAR_DESCRIPTION = "Automated school lunch menu calendar"
EVENT_TITLE = "School Lunch"

# Timezone
# Set to your local timezone (e.g., 'America/New_York', 'America/Chicago', 'America/Los_Angeles')
TIMEZONE = "America/New_York"

# Output Configuration
OUTPUT_DIR = "docs"
OUTPUT_FILENAME = "school-lunch.ics"

# PDF Configuration (if using PDF parser)
# Find the PDF URL from your school's menu page
# Examples:
#   - Direct PDF link
#   - API endpoint that returns PDF
PDF_URL = None  # Set this if using PDF parser

# Fetching Strategy Priority
# The scripts will try these methods in order
# Options: 'api', 'selenium', 'pdf'
FETCH_PRIORITY = ['api', 'selenium', 'pdf']

# Advanced Configuration

# Selenium options
SELENIUM_HEADLESS = True  # Run browser in headless mode
SELENIUM_TIMEOUT = 20     # Seconds to wait for page load

# Calendar event customization
ADD_LOCATION = False      # Add school location to events
LOCATION_NAME = "School Cafeteria"

ADD_REMINDER = False      # Add reminder to events
REMINDER_HOURS = 1        # Hours before event

# Date range
# Set to None to include all available dates
# Or set specific date ranges:
DATE_RANGE_START = None   # datetime object or None
DATE_RANGE_END = None     # datetime object or None
