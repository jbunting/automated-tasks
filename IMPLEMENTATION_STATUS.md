# School Lunch Menu Calendar - Implementation Status

## Current Status

We have discovered the API structure but are encountering access restrictions.

### What We Know

1. **Menu Type API**: `https://www.schoolnutritionandfitness.com/webmenus2/api/menutypeController.php/show?_id=62eaf1787057ec305d5532cb`
   - Returns metadata about all available months
   - Each month has an ID (e.g., `68b708e20b1ac86f9b4efcfc` for October 2025)
   - But the `days` array is empty

2. **Menu List Page**: `https://talawandafoodservice.com/index.php?sid=1533570452221&page=menus`
   - Lists all available menus with links
   - Format: `/downloadMenu.php/{sid}/{menu_code}`

3. **Individual Menu Views**: `https://www.schoolnutritionandfitness.com/webmenus2/#/view?id={menu_id}&siteCode={site_code}`
   - This is what displays in the browser
   - JavaScript loads the actual menu data

### The Problem

All API endpoints return **403 Forbidden** when accessed directly:
- The menu type API endpoint is blocked
- The download menu PHP endpoint is blocked
- The menu list page is blocked

This suggests the site has bot protection or requires:
- Session cookies from browsing the site
- Specific headers or referrers
- CAPTCHA completion
- Rate limiting

### What We Need to Discover

**Critical**: We need the API endpoint that returns the full menu data with the `days` array populated.

To find this:
1. Open `https://www.schoolnutritionandfitness.com/webmenus2/#/view?id=68b708e20b1ac86f9b4efcfc&siteCode=4657` in your browser
2. Open Developer Tools (F12) → Network tab
3. Filter by "XHR" or "Fetch"
4. Look for API calls that return JSON with daily menu items
5. Document the URL pattern and any required parameters

## Possible Solutions

### Option 1: Find the Correct API Endpoint (BEST)

If we can find the public API endpoint that returns full menu data, we can:
- Make direct API calls
- Run completely headless
- Very fast and reliable

**Action needed**: Inspect browser network traffic to find this endpoint

### Option 2: Selenium/Browser Automation

Use Selenium to:
- Load the page in a real browser
- Wait for JavaScript to render
- Extract the menu data from the DOM or intercept network requests

**Pros**: Will definitely work
**Cons**: Slower, requires Chrome/ChromeDriver, more resource-intensive

### Option 3: Manual JSON Updates

For now, we can:
- Manually save the JSON each month
- Run the `fetch_from_json.py` script
- Still get automation for ICS generation and GitHub Pages hosting

**Pros**: Simple, reliable
**Cons**: Not fully automated

### Option 4: Reverse Engineer the JavaScript

Analyze the frontend JavaScript to understand:
- How it loads the menu data
- What API calls it makes
- How to replicate those calls

## Scripts Available

### `fetch_from_json.py` ✅ WORKING

Generates ICS calendar from a saved JSON file.

**Usage**:
```bash
python3 fetch_from_json.py
```

**To update**:
1. Save the latest menu JSON to `discovery/kramer_elementary_lunch.json`
2. Run the script
3. Push to GitHub

### `fetch_menu_simple.py` ❌ BLOCKED

Attempts to fetch menu data directly from API.

**Status**: Returns 403 Forbidden

### `fetch_menu_working.py` ❌ BLOCKED

Scrapes menu list and attempts to fetch data.

**Status**: Returns 403 Forbidden

### `fetch_menu_selenium.py` ⚠️ NEEDS TESTING

Uses Selenium to load pages in a browser.

**Status**: Not yet updated with correct selectors/logic

## Next Steps

### Immediate (You)

1. **Discover the API endpoint**:
   - Open browser dev tools
   - Load a menu page
   - Find the API call that returns full menu data
   - Share the URL pattern and response structure

2. **Or, save a complete JSON**:
   - Find the network request that has the `days` array populated
   - Save that response
   - We can use it to generate the calendar

### Then (We'll Implement)

Based on what you find, we'll:
1. Update the fetcher scripts with the correct endpoint/method
2. Test the complete pipeline
3. Update GitHub Actions workflow
4. Deploy to GitHub Pages

## Current Workaround

Until we solve the API access issue:

1. **Monthly manual update**:
   ```bash
   # Save latest JSON to discovery/kramer_elementary_lunch.json
   python3 fetch_from_json.py
   git add docs/school-lunch.ics
   git commit -m "Update lunch menu"
   git push
   ```

2. **The calendar will still work**:
   - GitHub Pages serves the ICS file
   - Your calendar apps will auto-refresh
   - You just need to update the JSON monthly

## Files

- `fetch_from_json.py` - Working JSON-to-ICS converter
- `fetch_menu_simple.py` - API-based fetcher (blocked)
- `fetch_menu_working.py` - Menu list scraper (blocked)
- `fetch_menu_selenium.py` - Selenium-based (needs update)
- `discovery/` - Your API research
- `docs/school-lunch.ics` - Generated calendar (currently placeholder)

## Questions?

The key question is: **How do you access the menu data that has the daily items populated?**

Once we know that, we can fully automate this system!
