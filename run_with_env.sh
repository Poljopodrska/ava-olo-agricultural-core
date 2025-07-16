#\!/bin/bash
export DB_HOST="farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com"
export DB_NAME="farmer_crm"
export DB_USER="postgres"
export DB_PASSWORD='2hpzvrg_xP~qNbz1[_NppSK$e*O1'
export DB_PORT="5432"
export GOOGLE_MAPS_API_KEY="AIzaSyDyFXHN3VqQ9kWvj9ihcLjkpemf1FBc3uo"

echo "Environment variables set:"
echo "DB_HOST: $DB_HOST"
echo "DB_USER: $DB_USER"
echo "DB_NAME: $DB_NAME"
echo "DB_PASSWORD: SET (${#DB_PASSWORD} chars)"
echo "GOOGLE_MAPS_API_KEY: ${GOOGLE_MAPS_API_KEY:0:10}..."

if [ "$1" == "test" ]; then
    echo -e "\n=== Running deployment test ===\n"
    python3 test_deployment.py
else
    echo -e "\n=== Starting application server ===\n"
    python3 main.py
fi
EOF < /dev/null
