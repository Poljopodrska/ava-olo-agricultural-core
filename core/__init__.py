"""
AVA OLO Agricultural Core - Localization Modules
Constitutional Amendment #13 Implementation

This package contains the core localization functionality:
- country_detector: Detects country from WhatsApp numbers
- localization_handler: Handles intelligent localization
- llm_router_with_localization: Enhanced router with country context
"""

from .country_detector import CountryDetector
from .localization_handler import (
    LocalizationHandler,
    LocalizationContext,
    InformationItem,
    InformationRelevance
)
from .llm_router_with_localization import (
    LocalizedLLMRouter,
    LLMRouterAdapter,
    QueryType,
    RoutingDecision
)

__all__ = [
    'CountryDetector',
    'LocalizationHandler',
    'LocalizationContext',
    'InformationItem',
    'InformationRelevance',
    'LocalizedLLMRouter',
    'LLMRouterAdapter',
    'QueryType',
    'RoutingDecision'
]

# Version info
__version__ = '1.0.0'
__amendment__ = 13