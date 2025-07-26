#!/bin/bash
# SkyDash Terminal Admin Setup Script

echo "🚀 Setting up SkyDash Terminal Admin..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python 3.8+ required. Current version: $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p ~/.skydash/{logs,domains,backups}

# Set permissions for log directories (if running as root/sudo)
if [ "$EUID" -eq 0 ]; then
    echo "🔐 Setting up system directories..."
    mkdir -p /var/log/skydash/domains
    chown -R $SUDO_USER:$SUDO_USER /var/log/skydash 2>/dev/null || true
    chmod 755 /var/log/skydash
fi

# Make main.py executable
chmod +x main.py

# Create desktop shortcut (optional)
if command -v desktop-file-install &> /dev/null; then
    echo "🖥️  Creating desktop shortcut..."
    cat > skydash.desktop << EOF
[Desktop Entry]
Name=SkyDash Terminal Admin
Comment=AI-driven DevOps control center
Exec=$(pwd)/venv/bin/python $(pwd)/main.py
Icon=utilities-terminal
Terminal=true
Type=Application
Categories=System;Administration;
EOF
    
    desktop-file-install --dir=$HOME/.local/share/applications skydash.desktop 2>/dev/null || true
    rm -f skydash.desktop
fi

echo ""
echo "🎉 SkyDash Terminal Admin setup complete!"
echo ""
echo "To run SkyDash:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the application: python main.py"
echo ""
echo "Or use the run script: ./run.sh"
echo ""
echo "📚 For help and documentation, press 'H' in the main menu"
echo ""
