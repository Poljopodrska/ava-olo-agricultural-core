"""
🏛️ CAVA Production-Grade Error Handling
Enhancement 2: Circuit Breaker Pattern and Failover Strategies
Constitutional principles: ERROR ISOLATION, PRODUCTION-READY, FARMER-CENTRIC
"""

from __future__ import annotations

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    half_open_max_calls: int = 3
    
@dataclass 
class CircuitStats:
    """Statistics for circuit breaker"""
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[float] = None
    consecutive_successes: int = 0
    half_open_calls: int = 0

class CAVACircuitBreaker:
    """
    Circuit breaker pattern for CAVA services
    Prevents cascading failures and provides automatic recovery
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._lock = asyncio.Lock()
        logger.info(f"🔌 Circuit breaker '{name}' initialized")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            # Check if we should allow the call
            if not self._should_allow_request():
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")
            
            # For half-open state, track calls
            if self.state == CircuitState.HALF_OPEN:
                self.stats.half_open_calls += 1
        
        # Execute the function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    def _should_allow_request(self) -> bool:
        """Determine if request should be allowed"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.stats.last_failure_time:
                time_since_failure = time.time() - self.stats.last_failure_time
                if time_since_failure >= self.config.recovery_timeout:
                    logger.info(f"🔄 Circuit breaker '{self.name}' entering HALF_OPEN state")
                    self.state = CircuitState.HALF_OPEN
                    self.stats.half_open_calls = 0
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            return self.stats.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.stats.successes += 1
            self.stats.consecutive_successes += 1
            
            if self.state == CircuitState.HALF_OPEN:
                # Check if we can close the circuit
                if self.stats.consecutive_successes >= self.config.half_open_max_calls:
                    logger.info(f"✅ Circuit breaker '{self.name}' is now CLOSED")
                    self.state = CircuitState.CLOSED
                    self.stats.failures = 0
                    self.stats.consecutive_successes = 0
    
    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.stats.failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                # Check if we should open the circuit
                if self.stats.failures >= self.config.failure_threshold:
                    logger.warning(f"⚠️ Circuit breaker '{self.name}' is now OPEN")
                    self.state = CircuitState.OPEN
            
            elif self.state == CircuitState.HALF_OPEN:
                # Failed during recovery, go back to OPEN
                logger.warning(f"❌ Circuit breaker '{self.name}' recovery failed, returning to OPEN")
                self.state = CircuitState.OPEN
                self.stats.half_open_calls = 0

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CAVAFailoverManager:
    """
    Manages failover strategies for CAVA services
    Provides fallback options when primary services fail
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, 'CAVACircuitBreaker'] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self._initialize_circuit_breakers()
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each service"""
        services = [
            ("neo4j", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30)),
            ("redis", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=20)),
            ("pinecone", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60)),
            ("postgresql", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=45)),
            ("openai", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30))
        ]
        
        for service_name, config in services:
            self.circuit_breakers[service_name] = CAVACircuitBreaker(service_name, config)
    
    def register_fallback(self, service: str, handler: Callable):
        """Register a fallback handler for a service"""
        self.fallback_handlers[service] = handler
        logger.info(f"📦 Registered fallback handler for '{service}'")
    
    async def execute_with_failover(
        self, 
        service: str, 
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker and failover"""
        circuit_breaker = self.circuit_breakers.get(service)
        
        if not circuit_breaker:
            # No circuit breaker, execute directly
            return await primary_func(*args, **kwargs)
        
        try:
            # Try primary function with circuit breaker
            return await circuit_breaker.call(primary_func, *args, **kwargs)
        
        except CircuitBreakerOpenError:
            # Circuit is open, use fallback if available
            logger.warning(f"🔄 Circuit breaker open for '{service}', trying fallback")
            return await self._execute_fallback(service, *args, **kwargs)
        
        except Exception as e:
            # Primary failed, try fallback
            logger.error(f"❌ Primary '{service}' failed: {e}")
            return await self._execute_fallback(service, *args, **kwargs)
    
    async def _execute_fallback(self, service: str, *args, **kwargs) -> Any:
        """Execute fallback handler"""
        fallback = self.fallback_handlers.get(service)
        
        if fallback:
            try:
                logger.info(f"🔄 Executing fallback for '{service}'")
                return await fallback(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Fallback for '{service}' also failed: {e}")
                raise
        else:
            raise Exception(f"No fallback available for '{service}'")

# Retry decorator with exponential backoff
def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        # Calculate next delay
                        delay = min(delay * exponential_base, max_delay)
                        
                        logger.warning(
                            f"⏳ Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.1f}s delay. Error: {e}"
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ All {max_retries} retries failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

class CAVAErrorRecovery:
    """
    Error recovery strategies for CAVA
    Provides self-healing capabilities
    """
    
    def __init__(self, failover_manager: CAVAFailoverManager):
        self.failover_manager = failover_manager
        self.error_counts: Dict[str, int] = {}
        self.recovery_actions: Dict[str, List[Callable]] = {}
    
    def register_recovery_action(self, error_type: str, action: Callable):
        """Register a recovery action for specific error type"""
        if error_type not in self.recovery_actions:
            self.recovery_actions[error_type] = []
        self.recovery_actions[error_type].append(action)
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """
        Handle error with recovery strategies
        Returns recovery result if successful, None otherwise
        """
        error_type = type(error).__name__
        
        # Track error frequency
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log error with context
        logger.error(
            f"❌ Error in CAVA: {error_type} - {str(error)}\n"
            f"Context: {context}\n"
            f"Occurrences: {self.error_counts[error_type]}"
        )
        
        # Try recovery actions
        recovery_actions = self.recovery_actions.get(error_type, [])
        
        for action in recovery_actions:
            try:
                logger.info(f"🔧 Attempting recovery action for {error_type}")
                result = await action(error, context)
                if result is not None:
                    logger.info(f"✅ Recovery successful for {error_type}")
                    return result
            except Exception as recovery_error:
                logger.error(f"❌ Recovery action failed: {recovery_error}")
        
        return None

# Fallback implementations
async def redis_memory_fallback(session_id: str, operation: str, *args, **kwargs):
    """In-memory fallback for Redis"""
    # Simple in-memory cache (would be more sophisticated in production)
    if not hasattr(redis_memory_fallback, '_cache'):
        redis_memory_fallback._cache = {}
    
    cache = redis_memory_fallback._cache
    
    if operation == "get":
        return cache.get(session_id)
    elif operation == "set":
        cache[session_id] = args[0] if args else kwargs.get('data')
        # Implement simple TTL cleanup (simplified)
        asyncio.create_task(_cleanup_old_entries(cache))
        return True
    
    return None

async def _cleanup_old_entries(cache: dict, ttl_seconds: int = 3600):
    """Clean up old cache entries"""
    # Simplified cleanup - in production would track timestamps
    await asyncio.sleep(ttl_seconds)
    cache.clear()

async def postgresql_fallback_query(query: str, *args):
    """Fallback for PostgreSQL queries - return safe defaults"""
    logger.warning("📦 Using PostgreSQL fallback - returning safe defaults")
    
    # Return safe defaults based on query pattern
    if "EXISTS" in query.upper():
        return [{"exists": False}]
    elif "SELECT" in query.upper():
        return []
    else:
        return None

async def llm_fallback_response(prompt: str, context: Dict[str, Any]) -> str:
    """Fallback LLM response when primary fails"""
    logger.warning("📦 Using LLM fallback - generating simple response")
    
    # Simple rule-based responses
    if "register" in prompt.lower():
        return "I'll help you register. Please provide your name, phone number, and create a password."
    elif "harvest" in prompt.lower():
        return "For harvest timing, please check with local agricultural experts or visit our website."
    elif "plant" in prompt.lower() or "field" in prompt.lower():
        return "I've noted that information. Is there anything else about your crops you'd like to tell me?"
    else:
        return "I understand. Could you please tell me more about what you need help with?"

# Example usage in CAVA
def create_cava_error_handler() -> Tuple['CAVAFailoverManager', 'CAVAErrorRecovery']:
    """Create error handling components for CAVA"""
    failover_manager = CAVAFailoverManager()
    
    # Register fallbacks
    failover_manager.register_fallback("redis", redis_memory_fallback)
    failover_manager.register_fallback("postgresql", postgresql_fallback_query)
    failover_manager.register_fallback("openai", llm_fallback_response)
    
    error_recovery = CAVAErrorRecovery(failover_manager)
    
    # Register recovery actions
    async def reconnect_database(error, context):
        """Try to reconnect to database"""
        service = context.get("service")
        if service:
            logger.info(f"🔄 Attempting to reconnect to {service}")
            # Actual reconnection logic would go here
            await asyncio.sleep(1)  # Simulate reconnection
            return True
        return None
    
    error_recovery.register_recovery_action("ConnectionError", reconnect_database)
    error_recovery.register_recovery_action("TimeoutError", reconnect_database)
    
    return failover_manager, error_recovery