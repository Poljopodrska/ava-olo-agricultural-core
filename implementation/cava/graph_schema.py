"""
🏛️ CAVA Neo4j Graph Schema Initialization
Creates the constitutional farming graph structure
Principles: MANGO RULE, MODULE INDEPENDENCE
"""

import logging
from .database_connections import CAVANeo4jConnection

logger = logging.getLogger(__name__)

class CAVAGraphSchema:
    """Initialize and manage CAVA graph schema"""
    
    def __init__(self):
        self.neo4j = CAVANeo4jConnection()
    
    async def initialize_schema(self):
        """Create CAVA graph schema - works for ANY crop, ANY country"""
        await self.neo4j.connect()
        
        # Constitutional constraints (MANGO RULE compliant)
        constraints = [
            # Farmer constraints
            "CREATE CONSTRAINT farmer_id IF NOT EXISTS FOR (f:Farmer) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT farmer_phone IF NOT EXISTS FOR (f:Farmer) REQUIRE f.phone IS UNIQUE",
            
            # Field constraints  
            "CREATE CONSTRAINT field_id IF NOT EXISTS FOR (field:Field) REQUIRE field.id IS UNIQUE",
            
            # Product constraints (universal - works for any product)
            "CREATE CONSTRAINT product_name IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE",
            
            # Crop constraints (universal - watermelon, mango, dragonfruit, etc.)
            "CREATE CONSTRAINT crop_id IF NOT EXISTS FOR (c:Crop) REQUIRE c.id IS UNIQUE"
        ]
        
        # Performance indexes
        indexes = [
            # Name indexes for search
            "CREATE INDEX farmer_name IF NOT EXISTS FOR (f:Farmer) ON (f.name)",
            "CREATE INDEX field_name IF NOT EXISTS FOR (field:Field) ON (field.name)",
            "CREATE INDEX crop_type IF NOT EXISTS FOR (c:Crop) ON (c.type)",
            
            # Date indexes for temporal queries
            "CREATE INDEX application_date IF NOT EXISTS FOR (app:Application) ON (app.date)",
            "CREATE INDEX planting_date IF NOT EXISTS FOR (c:Crop) ON (c.planting_date)",
            
            # Location indexes (country-aware localization)
            "CREATE INDEX farmer_country IF NOT EXISTS FOR (f:Farmer) ON (f.country)",
            "CREATE INDEX field_location IF NOT EXISTS FOR (field:Field) ON (field.location)"
        ]
        
        logger.info("🏗️ Initializing CAVA graph schema...")
        
        # Create constraints
        for constraint in constraints:
            try:
                result = await self.neo4j.execute_query(constraint)
                logger.info("✅ Created constraint: %s", constraint.split()[2])
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.debug("⏭️ Constraint already exists: %s", constraint.split()[2])
                else:
                    logger.error("❌ Failed to create constraint: %s", str(e))
        
        # Create indexes
        for index in indexes:
            try:
                result = await self.neo4j.execute_query(index)
                logger.info("✅ Created index: %s", index.split()[2])
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.debug("⏭️ Index already exists: %s", index.split()[2])
                else:
                    logger.error("❌ Failed to create index: %s", str(e))
        
        # Create example data structure (for testing)
        if self.neo4j.dry_run:
            logger.info("🔍 DRY RUN: Would create example graph structure")
        else:
            await self._create_example_structure()
        
        logger.info("✅ CAVA graph schema initialized!")
        await self.neo4j.close()
    
    async def _create_example_structure(self):
        """Create example structure for testing (MANGO RULE compliant)"""
        
        # Example: Bulgarian mango farmer (constitutional test)
        example_queries = [
            """
            MERGE (f:Farmer {
                id: 999,
                name: 'Test Bulgarian Farmer',
                phone: '+359888123456',
                farm_name: 'Bulgarian Mango Paradise',
                country: 'Bulgaria',
                language: 'bg'
            })
            """,
            """
            MERGE (field:Field {
                id: 'field_999_south',
                name: 'South Mango Field',
                area_ha: 2.5,
                location: 'Southern Bulgaria',
                soil_type: 'Sandy loam'
            })
            """,
            """
            MERGE (mango:Crop {
                id: 'crop_mango_999',
                type: 'Mango',
                variety: 'Keitt',
                planting_date: date('2024-03-15'),
                expected_harvest: date('2024-10-15')
            })
            """,
            """
            MATCH (f:Farmer {id: 999})
            MATCH (field:Field {id: 'field_999_south'})
            MERGE (f)-[:OWNS]->(field)
            """,
            """
            MATCH (field:Field {id: 'field_999_south'})
            MATCH (crop:Crop {id: 'crop_mango_999'})
            MERGE (field)-[:PLANTED_WITH]->(crop)
            """
        ]
        
        for query in example_queries:
            try:
                await self.neo4j.execute_query(query)
            except Exception as e:
                logger.debug("Example data creation: %s", str(e))

async def initialize_cava_schema():
    """Initialize CAVA graph schema"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    schema = CAVAGraphSchema()
    await schema.initialize_schema()

if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_cava_schema())