# School Lunch Menu Calendar

Automatically fetch and convert school lunch menus to iCalendar (ICS) format for easy integration with Google Calendar, Home Assistant, and other calendar applications.

## Features

- 📅 Automatic monthly updates via GitHub Actions
- 🌐 Published via GitHub Pages with subscription URL
- 🔄 Multiple fetching strategies (API, Selenium, PDF)
- 📱 Works with Google Calendar, Apple Calendar, Home Assistant, and more
- 📊 Historical tracking through Git commits
- 🎨 Beautiful web interface for easy subscription

## Quick Start

### 1. Enable GitHub Pages

1. Go to your repository settings
2. Navigate to **Pages** section
3. Under "Source", select **Deploy from a branch**
4. Choose branch: **main** (or your default branch)
5. Choose folder: **/docs**
6. Click **Save**

Your calendar will be available at:
```
https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics
```

### 2. Configure Your Menu

Edit the configuration in `fetch_menu.py`, `fetch_menu_selenium.py`, or `fetch_menu_pdf.py`:

```python
MENU_ID = "68b708e20b1ac86f9b4efcfc"  # Your menu ID
SITE_CODE = "4657"                    # Your site code
```

These values come from your school's menu URL:
```
https://www.schoolnutritionandfitness.com/webmenus2/#/view?id=MENU_ID&siteCode=SITE_CODE
```

### 3. Test Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Try API-based fetch (fastest)
python fetch_menu.py

# If that fails, try Selenium (requires Chrome)
python fetch_menu_selenium.py

# Or use PDF parsing (if PDF URL is available)
python fetch_menu_pdf.py
```

The ICS file will be generated in `docs/school-lunch.ics`.

### 4. Trigger Automatic Updates

The GitHub Action runs automatically on the 1st of each month, but you can also:

- **Manual trigger**: Go to Actions → Update School Lunch Menu → Run workflow
- **Automatic on push**: Pushes to `main` branch trigger updates
- **Scheduled**: Runs monthly via cron schedule

## Usage

### Subscribe in Google Calendar

1. Open [Google Calendar](https://calendar.google.com)
2. Click the **+** next to "Other calendars"
3. Select **"From URL"**
4. Paste your calendar URL: `https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics`
5. Click **"Add calendar"**

**Note**: Google Calendar typically refreshes subscribed calendars every 24 hours.

### Add to Home Assistant

Add to your `configuration.yaml`:

```yaml
calendar:
  - platform: ical
    name: "School Lunch"
    url: "https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics"
```

Restart Home Assistant after updating the configuration.

### Subscribe in Apple Calendar

1. Open Calendar app
2. Go to **File** → **New Calendar Subscription**
3. Enter your calendar URL
4. Choose update frequency and location
5. Click **OK**

### Use with Other Apps

The ICS format is standard and works with:
- Microsoft Outlook
- Mozilla Thunderbird
- CalDAV clients
- Any application supporting iCalendar subscriptions

## Implementation Strategies

This project includes three different approaches to fetch menu data:

### 1. API-Based (`fetch_menu.py`)

**Best for**: Fast, reliable fetching when the website has an API

**Pros**:
- Fastest execution
- No browser required
- Lowest resource usage

**Cons**:
- May not work if website only renders via JavaScript
- Requires finding the API endpoint

### 2. Selenium-Based (`fetch_menu_selenium.py`)

**Best for**: JavaScript-heavy websites that don't expose APIs

**Pros**:
- Handles JavaScript rendering
- Can interact with dynamic content
- Works with most modern websites

**Cons**:
- Requires Chrome/ChromeDriver
- Slower execution
- Higher resource usage

### 3. PDF-Based (`fetch_menu_pdf.py`)

**Best for**: When PDF menus are available

**Pros**:
- PDFs are often more stable format
- Good for printed formats
- No JavaScript issues

**Cons**:
- Requires finding PDF URL
- PDF parsing can be tricky
- Layout changes can break parsing

## Project Structure

```
automated-tasks/
├── .github/
│   └── workflows/
│       └── update-menu.yml      # GitHub Actions workflow
├── docs/
│   ├── index.html               # Web interface
│   └── school-lunch.ics         # Generated calendar file
├── fetch_menu.py                # API-based fetcher
├── fetch_menu_selenium.py       # Selenium-based fetcher
├── fetch_menu_pdf.py           # PDF parser
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Customization

### Change Update Frequency

Edit `.github/workflows/update-menu.yml`:

```yaml
schedule:
  # Weekly on Monday at 3 AM
  - cron: '0 3 * * 1'

  # Daily at 3 AM
  - cron: '0 3 * * *'

  # First and 15th of month
  - cron: '0 3 1,15 * *'
```

### Customize Calendar Events

Edit the `ICSGenerator` class in your chosen script:

```python
event.add('summary', 'Lunch Menu')  # Change event title
event.add('description', ...)        # Customize description
event.add('location', 'School Cafeteria')  # Add location
```

### Add Reminders

Modify the event creation to add alarms:

```python
from icalendar import Alarm

alarm = Alarm()
alarm.add('action', 'DISPLAY')
alarm.add('trigger', timedelta(hours=-1))  # 1 hour before
event.add_component(alarm)
```

## Troubleshooting

### Calendar Not Updating

1. **Check GitHub Actions**: Go to Actions tab and verify the workflow runs successfully
2. **Force manual run**: Actions → Update School Lunch Menu → Run workflow
3. **Check for errors**: Review workflow logs for error messages
4. **Verify menu ID**: Ensure MENU_ID and SITE_CODE are correct

### No Events in Calendar

1. **Test locally**: Run the fetch script on your computer
2. **Check debug files**: GitHub Actions uploads screenshots and page source
3. **Website changed**: The menu website structure may have changed
4. **Menu not published**: Check if the menu for the current month is available

### Google Calendar Not Refreshing

- Google Calendar updates subscribed calendars approximately every 24 hours
- You cannot force an immediate refresh for subscribed calendars
- Consider using a different calendar app for faster updates

### Selenium Issues in GitHub Actions

The workflow automatically installs Chrome and ChromeDriver, but if you encounter issues:

1. Check Chrome version compatibility
2. Update ChromeDriver version in workflow
3. Review the uploaded screenshot to see what's rendering

## Advanced Usage

### Multiple Menus

To track multiple schools:

1. Create separate scripts for each menu
2. Generate different ICS files (e.g., `school1-lunch.ics`, `school2-lunch.ics`)
3. Update the workflow to run all scripts
4. Subscribe to each calendar separately

### Email Notifications

Add email notification to the workflow:

```yaml
- name: Send notification
  if: steps.check_calendar.outputs.has_events == 'true'
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: School lunch menu updated
    to: your-email@example.com
    from: GitHub Actions
    body: The school lunch menu has been updated!
```

### Webhook Integration

Trigger webhooks on update:

```yaml
- name: Trigger webhook
  if: steps.check_calendar.outputs.has_events == 'true'
  run: |
    curl -X POST https://your-webhook-url.com/notify \
      -H "Content-Type: application/json" \
      -d '{"message": "Menu updated", "date": "'$(date)'"}'
```

## Contributing

Found an issue or have an improvement? Feel free to open an issue or pull request!

## License

MIT License - See LICENSE file for details

## Acknowledgments

- School Nutrition and Fitness for providing the menu data
- iCalendar library for ICS generation
- GitHub Pages for free hosting
- GitHub Actions for automation

## Support

If you find this useful, please star the repository! ⭐
