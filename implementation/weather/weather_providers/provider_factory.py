#!/usr/bin/env python3
"""
Weather Provider Factory
Constitutional weather provider factory for managing multiple providers
"""

import logging
from typing import Dict, Optional, Any, List
from enum import Enum

from .base_provider import BaseWeatherProvider
from .openweathermap_provider import OpenWeatherMapProvider

logger = logging.getLogger(__name__)

class WeatherProviderType(Enum):
    """Supported weather provider types"""
    OPENWEATHERMAP = "openweathermap"
    METEOMATICS = "meteomatics"
    ACCUWEATHER = "accuweather"

class WeatherProviderFactory:
    """
    Constitutional Weather Provider Factory
    
    Manages creation and configuration of weather providers
    while maintaining constitutional compliance.
    """
    
    def __init__(self):
        """Initialize the provider factory"""
        self.providers = {}
        self.active_providers = []
        self.primary_provider = None
        
        # Provider class mappings
        self.provider_classes = {
            WeatherProviderType.OPENWEATHERMAP: OpenWeatherMapProvider,
            # WeatherProviderType.METEOMATICS: MeteomaticsProvider,  # Future
            # WeatherProviderType.ACCUWEATHER: AccuWeatherProvider,  # Future
        }
        
        logger.info("🏛️ Weather Provider Factory initialized")
    
    def create_provider(self, provider_type: WeatherProviderType, 
                       config: Dict[str, Any]) -> Optional[BaseWeatherProvider]:
        """
        Create a weather provider instance
        
        Args:
            provider_type: Type of weather provider
            config: Provider configuration
            
        Returns:
            Weather provider instance or None
        """
        try:
            # Validate constitutional compliance
            compliance_score = config.get('compliance_score', 0)
            if compliance_score < 80:
                logger.warning(f"⚠️ Provider {provider_type.value} below constitutional compliance threshold")
                return None
            
            # Get provider class
            provider_class = self.provider_classes.get(provider_type)
            if not provider_class:
                logger.error(f"❌ Provider type {provider_type.value} not implemented")
                return None
            
            # Create provider instance
            provider = provider_class(config)
            
            # Validate MANGO RULE compliance if required
            if not config.get('mango_rule_verified', False):
                logger.warning(f"⚠️ Provider {provider_type.value} not MANGO RULE verified")
            
            # Store provider
            self.providers[provider_type] = provider
            
            logger.info(f"✅ Created weather provider: {provider_type.value}")
            return provider
            
        except Exception as e:
            logger.error(f"❌ Failed to create provider {provider_type.value}: {e}")
            return None
    
    def get_provider(self, provider_type: WeatherProviderType) -> Optional[BaseWeatherProvider]:
        """
        Get a weather provider instance
        
        Args:
            provider_type: Type of weather provider
            
        Returns:
            Weather provider instance or None
        """
        return self.providers.get(provider_type)
    
    def get_active_providers(self) -> List[BaseWeatherProvider]:
        """Get list of active weather providers"""
        return self.active_providers
    
    def set_primary_provider(self, provider_type: WeatherProviderType) -> bool:
        """
        Set primary weather provider
        
        Args:
            provider_type: Type of weather provider
            
        Returns:
            True if successfully set
        """
        try:
            provider = self.providers.get(provider_type)
            if not provider:
                logger.error(f"❌ Provider {provider_type.value} not found")
                return False
            
            self.primary_provider = provider
            
            # Move to front of active providers list
            if provider in self.active_providers:
                self.active_providers.remove(provider)
            self.active_providers.insert(0, provider)
            
            logger.info(f"✅ Set primary weather provider: {provider_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set primary provider: {e}")
            return False
    
    def get_primary_provider(self) -> Optional[BaseWeatherProvider]:
        """Get primary weather provider"""
        return self.primary_provider
    
    def add_to_active_providers(self, provider_type: WeatherProviderType) -> bool:
        """
        Add provider to active providers list
        
        Args:
            provider_type: Type of weather provider
            
        Returns:
            True if successfully added
        """
        try:
            provider = self.providers.get(provider_type)
            if not provider:
                logger.error(f"❌ Provider {provider_type.value} not found")
                return False
            
            if provider not in self.active_providers:
                self.active_providers.append(provider)
                logger.info(f"✅ Added {provider_type.value} to active providers")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add provider to active list: {e}")
            return False
    
    def remove_from_active_providers(self, provider_type: WeatherProviderType) -> bool:
        """
        Remove provider from active providers list
        
        Args:
            provider_type: Type of weather provider
            
        Returns:
            True if successfully removed
        """
        try:
            provider = self.providers.get(provider_type)
            if not provider:
                return False
            
            if provider in self.active_providers:
                self.active_providers.remove(provider)
                logger.info(f"✅ Removed {provider_type.value} from active providers")
            
            # If this was the primary provider, set a new one
            if self.primary_provider == provider and self.active_providers:
                self.primary_provider = self.active_providers[0]
                logger.info(f"✅ New primary provider: {self.primary_provider.provider_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to remove provider from active list: {e}")
            return False
    
    async def test_all_providers(self) -> Dict[str, bool]:
        """
        Test all available providers
        
        Returns:
            Dictionary of provider test results
        """
        results = {}
        
        for provider_type, provider in self.providers.items():
            try:
                result = await provider.test_provider_connection()
                results[provider_type.value] = result
                
                if result:
                    logger.info(f"✅ Provider {provider_type.value} test passed")
                else:
                    logger.warning(f"⚠️ Provider {provider_type.value} test failed")
                    
            except Exception as e:
                logger.error(f"❌ Provider {provider_type.value} test error: {e}")
                results[provider_type.value] = False
        
        return results
    
    def get_provider_failover_order(self) -> List[WeatherProviderType]:
        """
        Get provider failover order based on priority and compliance
        
        Returns:
            List of provider types in failover order
        """
        # Sort by constitutional compliance score and priority
        sorted_providers = sorted(
            self.providers.items(),
            key=lambda x: (x[1].constitutional_compliance_score, x[1].mango_rule_verified),
            reverse=True
        )
        
        return [provider_type for provider_type, _ in sorted_providers]
    
    async def get_weather_with_failover(self, method: str, *args, **kwargs) -> Optional[Any]:
        """
        Get weather data with automatic failover
        
        Args:
            method: Provider method name to call
            *args: Method arguments
            **kwargs: Method keyword arguments
            
        Returns:
            Weather data or None if all providers fail
        """
        failover_order = self.get_provider_failover_order()
        
        for provider_type in failover_order:
            provider = self.providers.get(provider_type)
            if not provider:
                continue
            
            try:
                # Get the method from the provider
                provider_method = getattr(provider, method, None)
                if not provider_method:
                    continue
                
                # Call the method
                result = await provider_method(*args, **kwargs)
                
                if result:
                    logger.info(f"✅ Weather data obtained from {provider_type.value}")
                    return result
                
            except Exception as e:
                logger.warning(f"⚠️ Provider {provider_type.value} failed: {e}")
                continue
        
        logger.error("❌ All weather providers failed")
        return None
    
    def get_factory_status(self) -> Dict[str, Any]:
        """Get factory status information"""
        return {
            'total_providers': len(self.providers),
            'active_providers': len(self.active_providers),
            'primary_provider': self.primary_provider.provider_name if self.primary_provider else None,
            'available_provider_types': [pt.value for pt in self.provider_classes.keys()],
            'configured_providers': [pt.value for pt in self.providers.keys()],
            'constitutional_compliance': self.get_overall_compliance_score()
        }
    
    def get_overall_compliance_score(self) -> float:
        """Get overall constitutional compliance score"""
        if not self.providers:
            return 0.0
        
        total_score = sum(
            provider.constitutional_compliance_score 
            for provider in self.providers.values()
        )
        
        return total_score / len(self.providers)
    
    def create_providers_from_config(self, providers_config: List[Dict[str, Any]]) -> List[BaseWeatherProvider]:
        """
        Create multiple providers from configuration
        
        Args:
            providers_config: List of provider configurations
            
        Returns:
            List of created providers
        """
        created_providers = []
        
        for config in providers_config:
            provider_name = config.get('provider_name', '').lower()
            
            # Map provider name to enum
            provider_type = None
            for pt in WeatherProviderType:
                if pt.value == provider_name:
                    provider_type = pt
                    break
            
            if not provider_type:
                logger.warning(f"⚠️ Unknown provider type: {provider_name}")
                continue
            
            # Create provider
            provider = self.create_provider(provider_type, config)
            if provider:
                created_providers.append(provider)
                
                # Add to active providers if enabled
                if config.get('is_active', False):
                    self.add_to_active_providers(provider_type)
                
                # Set as primary if specified
                if config.get('is_primary', False):
                    self.set_primary_provider(provider_type)
        
        logger.info(f"✅ Created {len(created_providers)} weather providers")
        return created_providers