#!/bin/bash
# SkyDash Terminal Admin Run Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting SkyDash Terminal Admin...${NC}"

# Check if we're in the correct directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found. Please run this script from the SkyDash directory.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Running setup...${NC}"
    bash setup.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Setup failed. Please check the error messages above.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import rich" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Dependencies missing. Installing...${NC}"
    pip install -r requirements.txt
fi

# Run the application
echo -e "${GREEN}🎯 Launching SkyDash...${NC}"
echo ""

# Handle command line arguments
if [ "$1" = "--debug" ]; then
    python main.py --debug
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "SkyDash Terminal Admin"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --debug    Run in debug mode"
    echo "  --help     Show this help message"
    echo "  --version  Show version information"
    echo ""
elif [ "$1" = "--version" ]; then
    python -c "print('SkyDash Terminal Admin v1.0.0')"
else
    python main.py
fi

# Capture exit code
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ SkyDash exited with error code $exit_code${NC}"
    echo -e "${YELLOW}💡 Try running with --debug for more information${NC}"
else
    echo ""
    echo -e "${GREEN}✅ SkyDash exited successfully${NC}"
fi

exit $exit_code
