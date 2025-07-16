#!/usr/bin/env python3
"""
Geocode Farmers Database Update Script
Updates farmers table with GPS coordinates using constitutional geocoding service
"""

import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from constitutional_geocoding_service import ConstitutionalGeocodingService
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FarmerGeocodingUpdater:
    """Updates farmers table with GPS coordinates"""
    
    def __init__(self):
        self.geocoder = ConstitutionalGeocodingService()
        self.db_config = {
            'host': os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'),
            'database': os.getenv('DB_NAME', 'farmer_crm'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '2hpzvrg_xP~qNbz1[_NppSK$e*O1'),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    async def ensure_gps_columns_exist(self):
        """Ensure GPS columns exist in farmers table"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                print("📍 Ensuring GPS columns exist in farmers table...")
                
                # Add GPS coordinate columns if they don't exist
                cur.execute("""
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,8);
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS longitude DECIMAL(11,8);
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS gps_source VARCHAR(50) DEFAULT 'geocoded';
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS location_accuracy INTEGER;
                    ALTER TABLE farmers ADD COLUMN IF NOT EXISTS geocoded_at TIMESTAMP;
                """)
                
                conn.commit()
                print("✅ GPS columns ensured in farmers table")
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring GPS columns: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    async def get_farmers_without_gps(self) -> list:
        """Get farmers that don't have GPS coordinates"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get all farmers without GPS coordinates
                cur.execute("""
                    SELECT id, farm_name, manager_name, street_and_no, 
                           village, city, postal_code, country, latitude, longitude
                    FROM farmers 
                    WHERE latitude IS NULL OR longitude IS NULL
                    ORDER BY id;
                """)
                
                farmers = cur.fetchall()
                return [dict(farmer) for farmer in farmers]
                
        except Exception as e:
            logger.error(f"Error getting farmers without GPS: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    async def update_farmer_gps(self, farmer_id: int, location_result) -> bool:
        """Update a single farmer's GPS coordinates"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE farmers 
                    SET latitude = %s, 
                        longitude = %s, 
                        gps_source = %s,
                        location_accuracy = %s,
                        geocoded_at = %s
                    WHERE id = %s
                """, (
                    location_result.latitude,
                    location_result.longitude,
                    location_result.source,
                    location_result.accuracy,
                    datetime.now(),
                    farmer_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Database update error for farmer {farmer_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    async def geocode_all_farmers(self) -> dict:
        """Geocode all farmers and update database with GPS coordinates"""
        
        print("🌍 Starting Constitutional Farmer Geocoding Process...")
        
        # Ensure GPS columns exist
        if not await self.ensure_gps_columns_exist():
            return {"error": "Failed to ensure GPS columns exist"}
        
        # Get farmers without GPS
        farmers_without_gps = await self.get_farmers_without_gps()
        
        if not farmers_without_gps:
            print("✅ All farmers already have GPS coordinates!")
            return {"message": "All farmers already geocoded", "updated": 0}
        
        print(f"📊 Found {len(farmers_without_gps)} farmers to geocode")
        
        # Geocode farmers
        geocoding_results = await self.geocoder.geocode_farmers_batch(farmers_without_gps)
        
        # Update database
        successful_updates = 0
        failed_updates = 0
        update_results = []
        
        for farmer_id, location_result in geocoding_results.items():
            try:
                if await self.update_farmer_gps(farmer_id, location_result):
                    successful_updates += 1
                    update_results.append({
                        'farmer_id': farmer_id,
                        'status': 'success',
                        'coordinates': f"{location_result.latitude:.6f}, {location_result.longitude:.6f}",
                        'mango_rule_applicable': location_result.mango_rule_applicable
                    })
                else:
                    failed_updates += 1
                    update_results.append({
                        'farmer_id': farmer_id,
                        'status': 'failed',
                        'error': 'Database update failed'
                    })
                    
            except Exception as e:
                failed_updates += 1
                update_results.append({
                    'farmer_id': farmer_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Final verification
        total_farmers_with_gps = await self.get_total_farmers_with_gps()
        
        results = {
            'total_farmers_processed': len(farmers_without_gps),
            'successful_geocoding': len(geocoding_results),
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'total_farmers_with_gps': total_farmers_with_gps,
            'constitutional_compliance': successful_updates > 0,
            'mango_rule_farmers': len([r for r in update_results if r.get('mango_rule_applicable', False)]),
            'update_details': update_results
        }
        
        print(f"\n📈 Geocoding Results Summary:")
        print(f"  Farmers processed: {results['total_farmers_processed']}")
        print(f"  Successfully geocoded: {results['successful_geocoding']}")
        print(f"  Database updates successful: {results['successful_updates']}")
        print(f"  Database updates failed: {results['failed_updates']}")
        print(f"  Total farmers with GPS: {results['total_farmers_with_gps']}")
        print(f"  Bulgarian mango farmers: {results['mango_rule_farmers']}")
        print(f"  Constitutional compliance: {'✅ PASSED' if results['constitutional_compliance'] else '❌ FAILED'}")
        
        return results
    
    async def get_total_farmers_with_gps(self) -> int:
        """Get total count of farmers with GPS coordinates"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM farmers WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting total farmers with GPS: {e}")
            return 0
        finally:
            if conn:
                conn.close()
    
    async def verify_constitutional_compliance(self) -> dict:
        """Verify constitutional compliance of farmer geocoding"""
        
        print("🏛️ Verifying Constitutional Compliance...")
        
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get farmer GPS coverage
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_farmers,
                        COUNT(latitude) as farmers_with_gps,
                        ROUND(COUNT(latitude)::decimal / COUNT(*) * 100, 2) as gps_coverage_percent
                    FROM farmers;
                """)
                
                coverage = cur.fetchone()
                
                # Check Bulgarian farmers (MANGO RULE)
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_bulgarian_farmers,
                        COUNT(latitude) as bulgarian_farmers_with_gps
                    FROM farmers
                    WHERE country ILIKE '%bulgar%' OR country = 'BG';
                """)
                
                bulgarian_stats = cur.fetchone()
                
                # Sample Bulgarian farmers
                cur.execute("""
                    SELECT id, farm_name, manager_name, city, country, latitude, longitude
                    FROM farmers
                    WHERE country ILIKE '%bulgar%' OR country = 'BG'
                    ORDER BY id
                    LIMIT 5;
                """)
                
                bulgarian_farmers = cur.fetchall()
                
                compliance_results = {
                    'total_farmers': coverage['total_farmers'],
                    'farmers_with_gps': coverage['farmers_with_gps'],
                    'gps_coverage_percent': float(coverage['gps_coverage_percent']),
                    'constitutional_compliance': float(coverage['gps_coverage_percent']) >= 80,
                    'mango_rule': {
                        'total_bulgarian_farmers': bulgarian_stats['total_bulgarian_farmers'],
                        'bulgarian_farmers_with_gps': bulgarian_stats['bulgarian_farmers_with_gps'],
                        'bulgarian_gps_coverage': (bulgarian_stats['bulgarian_farmers_with_gps'] / bulgarian_stats['total_bulgarian_farmers'] * 100) if bulgarian_stats['total_bulgarian_farmers'] > 0 else 0,
                        'mango_rule_compliant': bulgarian_stats['bulgarian_farmers_with_gps'] > 0,
                        'sample_farmers': [dict(farmer) for farmer in bulgarian_farmers]
                    }
                }
                
                print(f"  📊 Total GPS Coverage: {compliance_results['gps_coverage_percent']:.1f}%")
                print(f"  🏛️ Constitutional Compliance: {'✅ PASSED' if compliance_results['constitutional_compliance'] else '❌ FAILED'}")
                print(f"  🥭 Bulgarian Farmers: {compliance_results['mango_rule']['total_bulgarian_farmers']} total, {compliance_results['mango_rule']['bulgarian_farmers_with_gps']} with GPS")
                print(f"  🥭 MANGO RULE: {'✅ PASSED' if compliance_results['mango_rule']['mango_rule_compliant'] else '❌ FAILED'}")
                
                return compliance_results
                
        except Exception as e:
            logger.error(f"Error verifying compliance: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

# Main execution function
async def main():
    """Main function to run farmer geocoding"""
    updater = FarmerGeocodingUpdater()
    
    # Run geocoding
    results = await updater.geocode_all_farmers()
    
    # Verify compliance
    compliance = await updater.verify_constitutional_compliance()
    
    print("\n🎯 CONSTITUTIONAL FARMER GEOCODING COMPLETE!")
    print("=" * 60)
    
    if 'error' not in results:
        print(f"✅ Successfully updated {results['successful_updates']} farmers with GPS coordinates")
        print(f"🏛️ Constitutional compliance: {compliance['constitutional_compliance']}")
        print(f"🥭 MANGO RULE compliance: {compliance['mango_rule']['mango_rule_compliant']}")
    else:
        print(f"❌ Error: {results['error']}")
    
    return results, compliance

if __name__ == "__main__":
    # For testing without database connection
    print("🧪 Testing Geocoding Service (without database connection)...")
    
    # Test the geocoding service
    async def test_only():
        geocoder = ConstitutionalGeocodingService()
        
        # Test Bulgarian mango farmer
        test_farmer = {
            'id': 999,
            'farm_name': 'Bulgarian Mango Farm',
            'street_and_no': 'Plovdiv Street 123',
            'village': 'Plovdiv',
            'city': 'Plovdiv',
            'country': 'Bulgaria',
            'postal_code': '4000'
        }
        
        print("🥭 Testing Bulgarian Mango Farmer Geocoding...")
        result = await geocoder.geocode_address({
            'street_and_no': test_farmer['street_and_no'],
            'village': test_farmer['village'],
            'city': test_farmer['city'],
            'country': test_farmer['country'],
            'postal_code': test_farmer['postal_code']
        })
        
        if result:
            print(f"✅ Bulgarian mango farmer geocoded successfully!")
            print(f"   📍 Coordinates: {result.latitude:.6f}, {result.longitude:.6f}")
            print(f"   🥭 MANGO RULE applicable: {result.mango_rule_applicable}")
            print(f"   🏛️ Constitutional compliance: {result.constitutional_compliance}")
        else:
            print("❌ Failed to geocode Bulgarian mango farmer")
        
        # Test constitutional compliance
        compliance = await geocoder.test_constitutional_compliance()
        
        print(f"\n🏛️ Constitutional Compliance Score: {compliance['constitutional_compliance_score']}%")
        print(f"🥭 MANGO RULE Status: {'✅ PASSED' if compliance['overall_compliance'] else '❌ FAILED'}")
        
        return result, compliance
    
    asyncio.run(test_only())