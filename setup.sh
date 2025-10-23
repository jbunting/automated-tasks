#!/bin/bash
# Setup script for School Lunch Menu Calendar

set -e

echo "======================================"
echo "School Lunch Menu Calendar Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Test imports
echo "Testing imports..."
python3 << EOF
try:
    import requests
    import bs4
    import icalendar
    from dateutil import parser
    print("✓ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
EOF
echo ""

# Create docs directory if it doesn't exist
if [ ! -d "docs" ]; then
    mkdir docs
    echo "✓ Created docs directory"
fi

# Test basic functionality
echo "Testing menu fetcher..."
echo "Running a test fetch (this may take a moment)..."
python3 fetch_menu.py || echo "⚠ API fetch failed (this is normal if the website doesn't have an API)"
echo ""

# Check if calendar was created
if [ -f "docs/school-lunch.ics" ]; then
    echo "✓ Calendar file created successfully!"
    echo ""
    echo "Preview of calendar file:"
    head -20 docs/school-lunch.ics
else
    echo "⚠ Calendar file not created yet."
    echo "   You may need to:"
    echo "   1. Configure your menu ID and site code in config.py"
    echo "   2. Try the Selenium-based fetcher: python3 fetch_menu_selenium.py"
    echo "   3. Or use the PDF parser if you have a PDF URL: python3 fetch_menu_pdf.py"
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit config.py with your menu ID and site code"
echo "2. Test locally: python3 fetch_menu.py"
echo "3. Enable GitHub Pages in your repository settings"
echo "4. Push changes to GitHub"
echo "5. Calendar will be available at: https://YOUR-USERNAME.github.io/automated-tasks/school-lunch.ics"
echo ""
echo "For more information, see README.md"
echo ""
