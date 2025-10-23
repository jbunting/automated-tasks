#!/usr/bin/env python3
"""
School Lunch Menu PDF Parser

This script downloads and parses the PDF version of the lunch menu,
which may be more reliable than scraping the web interface.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import requests
from io import BytesIO

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyPDF2 not available. Install with: pip install PyPDF2")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not available. Install with: pip install pdfplumber")

from icalendar import Calendar, Event
from dateutil.parser import parse as parse_date


class PDFMenuParser:
    """Parse school lunch menu from PDF files."""

    def __init__(self, pdf_url: str):
        self.pdf_url = pdf_url

    def download_pdf(self) -> Optional[bytes]:
        """Download the PDF file."""
        try:
            print(f"Downloading PDF from: {self.pdf_url}")
            response = requests.get(self.pdf_url, timeout=30)
            response.raise_for_status()
            print(f"✓ Downloaded {len(response.content)} bytes")
            return response.content
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return None

    def extract_text_pypdf2(self, pdf_bytes: bytes) -> str:
        """Extract text using PyPDF2."""
        if not PDF_AVAILABLE:
            return ""

        try:
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"

            return text
        except Exception as e:
            print(f"Error extracting text with PyPDF2: {e}")
            return ""

    def extract_text_pdfplumber(self, pdf_bytes: bytes) -> str:
        """Extract text using pdfplumber (often better at preserving layout)."""
        if not PDFPLUMBER_AVAILABLE:
            return ""

        try:
            pdf_file = BytesIO(pdf_bytes)
            text = ""

            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n\n"

            return text
        except Exception as e:
            print(f"Error extracting text with pdfplumber: {e}")
            return ""

    def parse_menu_text(self, text: str, year: Optional[int] = None) -> List[Dict]:
        """
        Parse menu text and extract events.

        Args:
            text: The extracted PDF text
            year: The year for the menu (defaults to current year)

        Returns:
            List of event dictionaries
        """
        if year is None:
            year = datetime.now().year

        events = []

        # Common patterns in school lunch menus
        # Pattern 1: Date followed by menu items
        # Example: "Monday, January 15" or "1/15" or "Jan 15"

        lines = text.split('\n')

        current_date = None
        current_menu = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to detect if this line contains a date
            date = self._extract_date_from_line(line, year)

            if date:
                # Save previous date's menu
                if current_date and current_menu:
                    events.append({
                        'date': current_date,
                        'title': 'School Lunch',
                        'description': '\n'.join(current_menu)
                    })

                # Start new date
                current_date = date
                current_menu = []

                # Check if menu items are on the same line
                remaining = self._remove_date_from_line(line)
                if remaining:
                    current_menu.append(remaining)

            elif current_date:
                # This is a menu item for the current date
                current_menu.append(line)

        # Don't forget the last date
        if current_date and current_menu:
            events.append({
                'date': current_date,
                'title': 'School Lunch',
                'description': '\n'.join(current_menu)
            })

        return events

    def _extract_date_from_line(self, line: str, year: int) -> Optional[datetime]:
        """Try to extract a date from a line of text."""

        # Pattern 1: Full date like "Monday, January 15, 2024"
        date_patterns = [
            r'([A-Za-z]+day),?\s+([A-Za-z]+)\s+(\d{1,2})',  # Monday, January 15
            r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})',  # January 15, 2024
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',  # 1/15/2024 or 1/15/24
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})',  # 1-15-2024
            r'([A-Za-z]+)\s+(\d{1,2})',  # January 15
        ]

        for pattern in date_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    # Try to parse with dateutil
                    date_str = match.group(0)

                    # Add year if not present
                    if str(year) not in date_str and '/' in date_str:
                        date_str += f'/{year}'
                    elif str(year) not in date_str:
                        date_str += f', {year}'

                    parsed_date = parse_date(date_str, fuzzy=True)
                    return parsed_date

                except Exception:
                    continue

        return None

    def _remove_date_from_line(self, line: str) -> str:
        """Remove date information from line to get remaining menu text."""
        # Remove common date patterns
        cleaned = re.sub(r'^[A-Za-z]+day,?\s+', '', line, flags=re.IGNORECASE)  # Remove weekday
        cleaned = re.sub(r'^[A-Za-z]+\s+\d{1,2},?\s*', '', cleaned, flags=re.IGNORECASE)  # Remove month day
        cleaned = re.sub(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*', '', cleaned)  # Remove numeric date
        return cleaned.strip()


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
    # You'll need to find the PDF URL from the website
    # It might be something like:
    # PDF_URL = "https://www.schoolnutritionandfitness.com/menu/68b708e20b1ac86f9b4efcfc.pdf"

    print("School Lunch Menu PDF Parser")
    print("=" * 50)
    print("\nTo use this script:")
    print("1. Find the PDF download link on the menu website")
    print("2. Update the PDF_URL variable in this script")
    print("3. Run the script")
    print("\nExample PDF URLs to try:")
    print("- Check the page source for .pdf links")
    print("- Look for 'Print' or 'Download' buttons")
    print("- Try: https://www.schoolnutritionandfitness.com/api/menu/68b708e20b1ac86f9b4efcfc/pdf")

    PDF_URL = input("\nEnter PDF URL (or press Enter to see example): ").strip()

    if not PDF_URL:
        print("\nExample: Edit this script and set PDF_URL at the top of main()")
        return

    OUTPUT_DIR = Path("docs")
    OUTPUT_FILE = OUTPUT_DIR / "school-lunch.ics"

    parser = PDFMenuParser(PDF_URL)

    # Download PDF
    pdf_bytes = parser.download_pdf()
    if not pdf_bytes:
        print("❌ Failed to download PDF")
        return

    # Extract text (try both methods)
    print("\nExtracting text from PDF...")
    text = parser.extract_text_pdfplumber(pdf_bytes)
    if not text:
        text = parser.extract_text_pypdf2(pdf_bytes)

    if not text:
        print("❌ Failed to extract text from PDF")
        return

    print(f"✓ Extracted {len(text)} characters")

    # Save extracted text for debugging
    with open('menu_text.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Text saved to menu_text.txt")

    # Parse menu
    events = parser.parse_menu_text(text)
    print(f"\n✓ Found {len(events)} meal events")

    if events:
        print("\nSample events:")
        for event in events[:3]:
            print(f"  {event['date'].strftime('%Y-%m-%d')}: {event['description'][:50]}...")

    # Generate ICS
    if events:
        success = generate_ics(events, OUTPUT_FILE)
        if success:
            print("\n✅ Success! Calendar file created")
        else:
            print("\n❌ Failed to generate calendar")
    else:
        print("\n❌ No events found. Check menu_text.txt to adjust parsing logic")


if __name__ == "__main__":
    main()
