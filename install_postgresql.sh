#!/bin/bash
# AVA OLO PostgreSQL Installation Script for WSL2

echo "🚀 Installing PostgreSQL for AVA OLO..."

# Update package lists
echo "📦 Updating package lists..."
sudo apt update

# Install PostgreSQL and contrib packages
echo "🐘 Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL service
echo "▶️ Starting PostgreSQL service..."
sudo service postgresql start

# Enable PostgreSQL to start automatically
echo "🔄 Enabling PostgreSQL auto-start..."
sudo systemctl enable postgresql 2>/dev/null || echo "Note: systemctl not available in WSL, use 'sudo service postgresql start' manually"

# Wait for PostgreSQL to be ready
sleep 3

# Create database and user
echo "🏗️ Creating database and user..."
sudo -u postgres psql <<EOF
CREATE DATABASE ava_olo;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE ava_olo TO postgres;
\q
EOF

# Check if create_schema.sql exists
if [ -f "create_schema.sql" ]; then
    echo "📋 Applying database schema..."
    PGPASSWORD=password psql -U postgres -h localhost -d ava_olo -f create_schema.sql
    
    # Add sample data
    echo "🌾 Adding sample farmers data..."
    PGPASSWORD=password psql -U postgres -h localhost -d ava_olo <<EOF
-- Insert sample Croatian farmers
INSERT INTO ava_farmers (state_farm_number, farm_name, manager_name, manager_last_name, 
                        city, email, phone_number, wa_phone_number, farmer_type, total_hectares)
VALUES 
    ('HR001', 'Horvat Farm', 'Marko', 'Horvat', 'Zagreb', 'marko@horvat-farm.hr', 
     '385912345678', '385912345678', 'grain', 45.5),
    ('HR002', 'Novak Vineyard', 'Ana', 'Novak', 'Split', 'ana@novak-vineyard.hr', 
     '385987654321', '385987654321', 'winegrower', 12.3),
    ('HR003', 'Petrovic Vegetables', 'Ivo', 'Petrovic', 'Osijek', 'ivo@petrovic-veg.hr', 
     '385911223344', '385911223344', 'vegetable', 8.7),
    ('HR004', 'Babic Grain Co.', 'Petra', 'Babic', 'Slavonski Brod', 'petra@babic-grain.hr', 
     '385923456789', '385923456789', 'grain', 120.0),
    ('HR005', 'Jovanovic Livestock', 'Milan', 'Jovanovic', 'Vukovar', 'milan@jovanovic-farm.hr', 
     '385934567890', '385934567890', 'livestock', 85.3),
    ('HR006', 'Milic Organic Farm', 'Dragana', 'Milic', 'Rijeka', 'dragana@milic-organic.hr', 
     '385945678901', '385945678901', 'mixed', 28.7);

-- Test the data
SELECT COUNT(*) as farmer_count FROM ava_farmers;
EOF
else
    echo "⚠️ create_schema.sql not found. Please run from project directory."
fi

# Test connection
echo "✅ Testing database connection..."
PGPASSWORD=password psql -U postgres -h localhost -d ava_olo -c "SELECT COUNT(*) FROM ava_farmers;" 2>/dev/null && echo "✅ Database ready!" || echo "❌ Connection failed"

# Update pg_hba.conf to allow password authentication
echo "🔧 Configuring PostgreSQL authentication..."
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
if [ -f "$PG_CONFIG" ]; then
    sudo sed -i 's/local   all             postgres                                peer/local   all             postgres                                md5/' $PG_CONFIG
    sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' $PG_CONFIG
    sudo service postgresql restart
fi

echo "🎉 PostgreSQL installation complete!"
echo ""
echo "📌 Connection details:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: ava_olo"
echo "   Username: postgres"
echo "   Password: password"
echo ""
echo "🔗 Connection string: postgresql://postgres:password@localhost:5432/ava_olo"
echo ""
echo "Next steps:"
echo "1. Restart the API gateway to use the real database"
echo "2. Check http://localhost:8006 for Mock WhatsApp UI"
echo "3. Check http://localhost:8007 for Agronomic Dashboard"