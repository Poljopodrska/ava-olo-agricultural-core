"""
Memory Training Routes - Examples of perfect memory demonstration
"""
from fastapi import APIRouter
from typing import Dict, List

router = APIRouter(prefix="/api/v1", tags=["memory"])

@router.post("/cava/train-memory")
async def train_memory_response():
    """Train the system on what good memory demonstration looks like"""
    
    # Example of perfect memory demonstration
    perfect_examples = [
        {
            "context": {
                "farmer_name": "Ivan",
                "location": "Bulgaria",
                "crop": "mangoes",
                "hectares": 25
            },
            "user_message": "When should I harvest?",
            "perfect_response": """Hello Ivan! For your 25 hectares of mangoes in Bulgaria, this is quite an unusual but interesting venture! 

Since Bulgaria's climate is typically temperate and mangoes are tropical fruits, I assume you're using greenhouse technology or have found a particularly warm microclimate. 

For mango harvesting in your unique Bulgarian conditions:
- Mangoes typically take 100-150 days from flowering to harvest
- In your climate, you'll want to harvest before the first frost
- Look for slight color change and a fruity aroma
- The fruit should yield slightly to gentle pressure

Given you're growing tropical fruit in Bulgaria, I'd recommend closely monitoring temperature and humidity. Your 25 hectares is a significant investment in such an unusual crop for the region!

Would you like specific advice for greenhouse mango cultivation in temperate climates?"""
        },
        {
            "context": {
                "farmer_name": "Maria",
                "location": "Croatia, near Zagreb",
                "crop": "tomatoes",
                "hectares": 3,
                "previous_problems": "fungal issues last season"
            },
            "user_message": "Should I use the same fungicide again?",
            "perfect_response": """Hi Maria! I remember you mentioned having fungal issues with your tomatoes last season on your 3-hectare farm near Zagreb.

Before recommending whether to use the same fungicide, I need to consider a few things about your Croatian growing conditions:

1. **Resistance Development**: If you used the same fungicide extensively last season, the fungi may have developed resistance. It's generally recommended to rotate fungicide classes.

2. **Weather Patterns**: Zagreb's humid continental climate can promote fungal growth, especially during wet springs and summers.

3. **Previous Effectiveness**: How well did the fungicide work last season on your 3 hectares?

For your tomato farm in Croatia, I'd suggest:
- Rotating to a different fungicide class this season
- Implementing preventive measures like proper spacing and pruning
- Consider copper-based organic options if you're interested in reducing chemical use

What specific fungal disease were you dealing with? This would help me give you more targeted advice for your Zagreb-area conditions."""
        },
        {
            "context": {
                "farmer_name": "Hans",
                "location": "Germany, Bavaria",
                "crop": "wheat",
                "hectares": 50,
                "soil_type": "loamy"
            },
            "user_message": "What's the weather forecast impact?",
            "perfect_response": """Hello Hans! For your 50 hectares of wheat in Bavaria, let me analyze the weather forecast impact on your loamy soil conditions.

Bavaria's current weather patterns are crucial for your wheat at this stage. Your loamy soil is excellent for wheat cultivation as it retains moisture well while still providing good drainage - particularly important given the region's variable precipitation.

Key weather considerations for your Bavarian wheat farm:
- **Temperature**: Wheat in Bavaria needs accumulated heat units. Current forecasts suggest [you'd check actual forecast]
- **Precipitation**: Your 50 hectares of loamy soil can handle moderate rainfall well, but excessive rain during harvest can be problematic
- **Wind**: Strong winds can cause lodging in wheat, especially on larger fields like yours

Specific recommendations for your situation:
1. Monitor soil moisture - loamy soils in Bavaria can become waterlogged
2. Plan harvest timing carefully if rain is forecast
3. Consider growth regulators if strong winds are expected

Would you like me to focus on a specific weather concern for your wheat fields, Hans?"""
        }
    ]
    
    return {
        "examples": perfect_examples,
        "key_elements": [
            "Uses farmer's name (Ivan, Maria, Hans)",
            "Mentions specific location (Bulgaria, Zagreb, Bavaria)",
            "References exact quantity (25 hectares, 3 hectares, 50 hectares)",
            "Acknowledges unusual aspects (tropical in temperate)",
            "Remembers previous problems or context",
            "Provides specific, contextual advice",
            "Shows understanding of the unique situation",
            "Never asks for information already provided"
        ],
        "scoring_criteria": {
            "name_usage": "Must use farmer's name naturally in response",
            "location_reference": "Must mention and consider geographic location",
            "quantity_precision": "Must use exact numbers provided",
            "context_awareness": "Must show understanding of full context",
            "memory_demonstration": "Must explicitly reference remembered information",
            "personalization": "Must feel like talking to someone who knows their farm"
        }
    }

@router.get("/cava/memory-examples")
async def get_memory_examples():
    """Get examples of good vs bad memory demonstration"""
    
    return {
        "good_examples": {
            "greeting": "Hello Ivan! Regarding your 25 hectares of mangoes in Bulgaria...",
            "context_reference": "As we discussed last time about your unusual tropical crop in temperate climate...",
            "specific_advice": "For your specific situation growing mangoes in Bulgaria's climate...",
            "quantity_mention": "Your 25 hectares will require approximately...",
            "problem_continuity": "Following up on the fungal issues you mentioned..."
        },
        "bad_examples": {
            "generic_greeting": "Hello! How can I help you with farming today?",
            "no_context": "To answer your question about harvesting...",
            "asking_known_info": "What crop are you growing?",
            "no_specifics": "Fruit should be harvested when ripe.",
            "ignoring_unusual": "Mango harvesting follows standard procedures."
        },
        "memory_indicators": [
            "Uses farmer's name",
            "Mentions location",
            "References crop type",
            "States exact quantities", 
            "Acknowledges previous conversations",
            "Provides location-specific advice",
            "Shows contextual understanding"
        ]
    }