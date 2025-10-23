# School Lunch Menu Calendar

Automatically convert school lunch menus into an ICS calendar file for easy integration with Google Calendar, Home Assistant, and other calendar applications.

## Features

- 📅 Parses school lunch menu data from GraphQL JSON
- 🗓️ Generates standard ICS calendar format
- 🌐 Published via GitHub Pages for easy subscription
- 📱 Works with Google Calendar, Apple Calendar, Home Assistant, and more
- 📊 Historical tracking through Git commits
- 🎨 Beautiful web interface for easy access

## Quick Start

### 1. Generate the Calendar

The menu data is fetched from the school's website and saved as JSON files. Run the generator:

```bash
python3 fetch_menu.py
```

This will:
- Load saved GraphQL JSON files from `discovery/`
- Parse menu items for current and upcoming months
- Generate `docs/school-lunch.ics` with all lunch dates
- Skip past dates automatically

### 2. Enable GitHub Pages

1. Go to your repository settings on GitHub
2. Navigate to **Pages** section
3. Under "Source", select **Deploy from a branch**
4. Choose branch: **main** (or your default branch)
5. Choose folder: **/docs**
6. Click **Save**

Your calendar will be available at:
```
https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics
```

### 3. Subscribe to the Calendar

**Google Calendar:**
1. Open [Google Calendar](https://calendar.google.com)
2. Click **+** next to "Other calendars"
3. Select **"From URL"**
4. Paste: `https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics`
5. Click **"Add calendar"**

**Home Assistant:**
```yaml
calendar:
  - platform: ical
    name: "School Lunch"
    url: "https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics"
```

**Apple Calendar:**
1. File → New Calendar Subscription
2. Enter your calendar URL
3. Choose update frequency
4. Click OK

## Monthly Updates

To add next month's menu:

### Step 1: Get the GraphQL Data

1. Open the menu page:
   ```
   https://www.schoolnutritionandfitness.com/webmenus2/#/view?id=MENU_ID&siteCode=4657
   ```
   Find the correct `MENU_ID` from the [menu list page](https://talawandafoodservice.com/index.php?sid=1533570452221&page=menus)

2. Open Developer Tools (F12) → Network tab

3. Reload the page and look for: `api.isitesoftware.com/graphql`

4. Click on the request → Response tab → Copy all the JSON

### Step 2: Save and Generate

5. Save the JSON to `discovery/menu_YYYY_MM.json`
   Example: `discovery/menu_2025_11.json` for November 2025

6. Run the generator:
   ```bash
   python3 fetch_menu.py
   ```

### Step 3: Publish

7. Commit and push:
   ```bash
   git add docs/school-lunch.ics discovery/menu_2025_11.json
   git commit -m "Add November 2025 lunch menu"
   git push
   ```

The calendar will update automatically on GitHub Pages!

## How It Works

### Data Flow

1. **Menu Data Source**: School Nutrition and Fitness website uses GraphQL API
2. **JSON Storage**: GraphQL responses saved in `discovery/` directory
3. **Parser**: `fetch_menu.py` reads JSON files and extracts menu items
4. **ICS Generation**: Creates standard iCalendar format
5. **GitHub Pages**: Serves the ICS file at a public URL
6. **Calendar Apps**: Subscribe and auto-refresh (usually daily)

### File Structure

```
automated-tasks/
├── discovery/              # Saved GraphQL JSON files
│   ├── kramer-graphql.json
│   └── menu_YYYY_MM.json   # Add new months here
├── docs/                   # GitHub Pages root
│   ├── index.html          # Web interface
│   └── school-lunch.ics    # Generated calendar
├── fetch_menu.py           # Main script (WORKING!)
└── README.md               # This file
```

### JSON File Formats

The script accepts GraphQL responses in these formats:

**Full GraphQL response:**
```json
{
  "data": {
    "menu": {
      "year": 2025,
      "month": 10,
      "items": [...]
    }
  }
}
```

**Or just the menu data:**
```json
{
  "year": 2025,
  "month": 10,
  "items": [...]
}
```

## Configuration

Edit `fetch_menu.py` to customize:

```python
# Lines 231-235
DISCOVERY_DIR = Path("discovery")      # Where JSON files are stored
OUTPUT_DIR = Path("docs")              # Where to save ICS file
OUTPUT_FILE = OUTPUT_DIR / "school-lunch.ics"  # Calendar filename
CALENDAR_NAME = "Kramer Elementary Lunch"      # Calendar display name
```

## Troubleshooting

### No Events Found

- Check that JSON files are in `discovery/` directory
- Verify JSON has `items` array with menu data
- Ensure dates are current/upcoming (past dates are skipped)

### Calendar Not Updating

- Verify GitHub Pages is enabled
- Check that ICS file exists in `docs/` directory
- Calendar apps typically refresh every 24 hours
- Try removing and re-adding the subscription

### Invalid JSON

- Make sure you copied the complete JSON response
- Check that braces `{}` are properly matched
- Use a JSON validator to verify format

## Advanced Usage

### Multiple Schools

To track multiple schools:

1. Create separate JSON files for each school/meal type
2. Modify `fetch_menu.py` to generate separate ICS files
3. Subscribe to each calendar separately

### Automation Ideas

While the GraphQL API requires browser authentication, you could:
- Set up a monthly reminder to update the JSON
- Use a browser automation tool (Selenium, Puppeteer)
- Create a bookmarklet to extract and download the JSON

### Custom Formatting

Edit the `parse_graphql_to_events()` function in `fetch_menu.py` to customize:
- Event titles
- Description formatting
- Category grouping
- Additional fields

## Technical Details

**Language:** Python 3.8+

**Dependencies:**
- `icalendar` - ICS file generation
- `requests` - HTTP requests (for future API automation)
- `beautifulsoup4` - HTML parsing (for future scraping)

**Install:**
```bash
pip install -r requirements.txt
```

**API Details:**
- GraphQL endpoint: `https://api.isitesoftware.com/graphql`
- Requires browser session (cookies/headers)
- Returns menu data with items array
- Month is 0-indexed (0=January, 11=December)

## Contributing

Found a bug or have an improvement? Feel free to open an issue or pull request!

## License

MIT License - See LICENSE file for details

## Acknowledgments

- School Nutrition and Fitness for providing the menu data
- iCalendar library for ICS generation
- GitHub Pages for free hosting
