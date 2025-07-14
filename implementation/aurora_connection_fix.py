"""
Aurora connection fix for authentication system
Handles password with special characters correctly
"""
import os

def get_aurora_password():
    """Get Aurora password with proper handling of special characters"""
    # The actual password with special characters
    # Using raw string to avoid issues with escaping
    password = r'2hpzvrg_xP~qNbz1[_NppSK$e*O1'
    return password

def get_aurora_config():
    """Get complete Aurora configuration"""
    # Try environment variables first (what actually works)
    if os.getenv('DB_HOST'):
        return {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', '5432'))
        }
    
    # Fallback to hardcoded
    return {
        'host': 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com',
        'database': 'farmer_crm',
        'user': 'postgres',
        'password': get_aurora_password(),
        'port': 5432
    }