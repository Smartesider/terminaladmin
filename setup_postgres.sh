#!/bin/bash

# PostgreSQL Setup Script for SkyDash
# Creates database and user: skyhost with password: Klokken!12!?!

echo "🐘 Setting up PostgreSQL database for SkyDash..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL..."
    apt update
    apt install -y postgresql postgresql-contrib python3-psycopg2
    
    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 3

# Create user and database
echo "👤 Creating PostgreSQL user and database..."

# Switch to postgres user and run commands
sudo -u postgres psql << EOF
-- Create user skyhost with password
CREATE USER skyhost WITH PASSWORD 'Klokken!12!?!';

-- Grant superuser privileges
ALTER USER skyhost WITH SUPERUSER;

-- Create database skyhost owned by skyhost
CREATE DATABASE skyhost OWNER skyhost;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE skyhost TO skyhost;

-- Show created user
\du skyhost

-- Show created database
\l skyhost

EOF

echo "✅ PostgreSQL setup completed!"
echo ""
echo "📋 Database Configuration:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: skyhost"
echo "  Username: skyhost"
echo "  Password: Klokken!12!?!"
echo ""
echo "🔗 Connection string: postgresql://skyhost:Klokken!12!?!@localhost:5432/skyhost"
echo ""
echo "🧪 Testing connection..."

# Test connection
sudo -u postgres psql -h localhost -U skyhost -d skyhost -c "SELECT version();" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Database connection test successful!"
else
    echo "❌ Database connection test failed!"
    echo "You may need to configure pg_hba.conf for password authentication"
fi

echo ""
echo "📝 To connect manually: psql -h localhost -U skyhost -d skyhost"
