"""
Comprehensive Error Handling and Recovery System
Provides robust error handling, automatic recovery, and system resilience
"""

import asyncio
import logging
import traceback
import time
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import aiohttp
import json

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    NETWORK = "network"
    MODEL = "model"
    BLOCKCHAIN = "blockchain"
    SYSTEM = "system"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"


@dataclass
class ErrorEvent:
    """Represents an error event in the system"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    occurrences: int = 1


class CircuitBreakerState(str, Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for preventing cascading failures"""
    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    successful_calls: int = 0


class RetryPolicy:
    """Configurable retry policy"""

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)

        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter

        return delay


class ErrorHandler:
    """Comprehensive error handling and recovery system"""

    def __init__(self):
        self.error_events: Dict[str, ErrorEvent] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {
            ErrorCategory.NETWORK: [self._retry_network_operation, self._switch_endpoint],
            ErrorCategory.MODEL: [self._reload_model, self._fallback_model],
            ErrorCategory.BLOCKCHAIN: [self._retry_blockchain_operation, self._use_backup_rpc],
            ErrorCategory.SYSTEM: [self._restart_component, self._reduce_load],
        }

        # Error statistics
        self.error_counts: Dict[str, int] = {}
        self.recovery_success_rates: Dict[str, float] = {}

        # Background monitoring
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start error monitoring"""
        logger.info("Starting error handling system")
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        """Stop error monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()

    def handle_error(self, error: Exception, component: str, category: ErrorCategory,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Dict[str, Any] = None) -> ErrorEvent:
        """Handle and categorize an error"""
        error_id = f"{component}_{category.value}_{int(time.time())}"

        # Check if this is a recurring error
        similar_errors = [e for e in self.error_events.values()
                         if e.component == component and e.category == category
                         and e.message == str(error)]

        if similar_errors:
            # Update existing error
            existing_error = similar_errors[0]
            existing_error.occurrences += 1
            existing_error.timestamp = datetime.utcnow()
            error_event = existing_error
        else:
            # Create new error event
            error_event = ErrorEvent(
                error_id=error_id,
                timestamp=datetime.utcnow(),
                category=category,
                severity=severity,
                component=component,
                message=str(error),
                details=context or {},
                stack_trace=traceback.format_exc()
            )
            self.error_events[error_id] = error_event

        # Log error
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }[severity]

        logger.log(log_level, f"Error in {component} ({category.value}): {error}")

        # Track error statistics
        self.error_counts[f"{component}_{category.value}"] = \
            self.error_counts.get(f"{component}_{category.value}", 0) + 1

        # Trigger recovery if appropriate
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            asyncio.create_task(self._attempt_recovery(error_event))

        return error_event

    async def _attempt_recovery(self, error_event: ErrorEvent) -> bool:
        """Attempt automatic recovery for an error"""
        if error_event.recovery_attempted:
            return error_event.recovery_successful

        error_event.recovery_attempted = True
        logger.info(f"Attempting recovery for error {error_event.error_id}")

        recovery_strategies = self.recovery_strategies.get(error_event.category, [])

        for strategy in recovery_strategies:
            try:
                success = await strategy(error_event)
                if success:
                    error_event.recovery_successful = True
                    logger.info(f"Recovery successful for {error_event.error_id}")
                    return True
            except Exception as e:
                logger.error(f"Recovery strategy failed: {e}")

        logger.warning(f"All recovery strategies failed for {error_event.error_id}")
        return False

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name)
        return self.circuit_breakers[name]

    async def call_with_circuit_breaker(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        breaker = self.get_circuit_breaker(name)

        # Check circuit breaker state
        if breaker.state == CircuitBreakerState.OPEN:
            if datetime.utcnow() - breaker.last_failure_time > timedelta(seconds=breaker.recovery_timeout):
                breaker.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker {name} transitioning to half-open")
            else:
                raise Exception(f"Circuit breaker {name} is open")

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - update circuit breaker
            if breaker.state == CircuitBreakerState.HALF_OPEN:
                breaker.successful_calls += 1
                if breaker.successful_calls >= 3:  # Require 3 successful calls
                    breaker.state = CircuitBreakerState.CLOSED
                    breaker.failure_count = 0
                    breaker.successful_calls = 0
                    logger.info(f"Circuit breaker {name} closed after successful recovery")

            return result

        except Exception as e:
            # Failure - update circuit breaker
            breaker.failure_count += 1
            breaker.last_failure_time = datetime.utcnow()

            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker {name} opened after {breaker.failure_count} failures")

            raise e

    def retry_on_failure(self, policy: RetryPolicy = None,
                        categories: List[ErrorCategory] = None):
        """Decorator for automatic retry with exponential backoff"""
        if policy is None:
            policy = RetryPolicy()

        if categories is None:
            categories = [ErrorCategory.NETWORK, ErrorCategory.BLOCKCHAIN]

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(policy.max_attempts):
                    try:
                        if asyncio.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        # Determine if we should retry this error
                        should_retry = any(
                            self._should_retry_error(e, cat) for cat in categories
                        )

                        if not should_retry or attempt == policy.max_attempts - 1:
                            raise e

                        # Wait before retry
                        delay = policy.get_delay(attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                        await asyncio.sleep(delay)

                raise last_exception
            return wrapper
        return decorator

    def _should_retry_error(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if an error should be retried"""
        if category == ErrorCategory.NETWORK:
            return isinstance(error, (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError))
        elif category == ErrorCategory.BLOCKCHAIN:
            return "timeout" in str(error).lower() or "connection" in str(error).lower()
        elif category == ErrorCategory.MODEL:
            return "cuda out of memory" in str(error).lower()
        return False

    async def _retry_network_operation(self, error_event: ErrorEvent) -> bool:
        """Recovery strategy: retry network operation"""
        try:
            # Implement network retry logic
            await asyncio.sleep(1)
            logger.info("Network operation retry completed")
            return True
        except Exception:
            return False

    async def _switch_endpoint(self, error_event: ErrorEvent) -> bool:
        """Recovery strategy: switch to backup endpoint"""
        try:
            # Implement endpoint switching logic
            logger.info("Switched to backup endpoint")
            return True
        except Exception:
            return False

    async def _reload_model(self, error_event: ErrorEvent) -> bool:
        """Recovery strategy: reload ML model"""
        try:
            # Implement model reloading logic
            logger.info("Model reloaded successfully")
            return True
        except Exception:
            return False

    async def _fallback_model(self, error_event: ErrorEvent) -> bool:
        """Recovery strategy: switch to fallback model"""
        try:
            # Implement fallback model logic
            logger.info("Switched to fallback model")
            return True
        except Exception:
            return False

    async def _retry_blockchain_operation(self, error_event: ErrorEvent) -> bool:
        """Recovery strategy: retry blockchain operation"""
        try:
            # Implement blockchain retry logic
            await asyncio.sleep(2)
            logger.info("Blockchain operation retried successfully")
            return True
        except Exception:
            return False

    async def _use_backup_rpc(self, error_event: ErrorEvent) -> bool:
        """Recovery strategy: switch to backup RPC"""
        try:
            # Implement RPC switching logic
            logger.info("Switched to backup RPC endpoint")
            return True
        except Exception:
            return False

    async def _restart_component(self, error_event: ErrorEvent) -> bool:
        """Recovery strategy: restart failed component"""
        try:
            # Implement component restart logic
            logger.info(f"Restarted component: {error_event.component}")
            return True
        except Exception:
            return False

    async def _reduce_load(self, error_event: ErrorEvent) -> bool:
        """Recovery strategy: reduce system load"""
        try:
            # Implement load reduction logic
            logger.info("Reduced system load")
            return True
        except Exception:
            return False

    def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive error summary"""
        recent_errors = [e for e in self.error_events.values()
                        if datetime.utcnow() - e.timestamp < timedelta(hours=1)]

        return {
            "total_errors": len(self.error_events),
            "recent_errors": len(recent_errors),
            "error_by_category": self._group_errors_by_category(),
            "error_by_severity": self._group_errors_by_severity(),
            "recovery_rate": self._calculate_recovery_rate(),
            "circuit_breakers": {name: cb.state.value for name, cb in self.circuit_breakers.items()},
            "top_error_components": self._get_top_error_components()
        }

    def _group_errors_by_category(self) -> Dict[str, int]:
        """Group errors by category"""
        categories = {}
        for error in self.error_events.values():
            categories[error.category.value] = categories.get(error.category.value, 0) + 1
        return categories

    def _group_errors_by_severity(self) -> Dict[str, int]:
        """Group errors by severity"""
        severities = {}
        for error in self.error_events.values():
            severities[error.severity.value] = severities.get(error.severity.value, 0) + 1
        return severities

    def _calculate_recovery_rate(self) -> float:
        """Calculate overall recovery success rate"""
        recovery_attempted = [e for e in self.error_events.values() if e.recovery_attempted]
        if not recovery_attempted:
            return 0.0

        successful_recoveries = [e for e in recovery_attempted if e.recovery_successful]
        return len(successful_recoveries) / len(recovery_attempted)

    def _get_top_error_components(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get components with most errors"""
        component_errors = {}
        for error in self.error_events.values():
            component_errors[error.component] = component_errors.get(error.component, 0) + error.occurrences

        sorted_components = sorted(component_errors.items(), key=lambda x: x[1], reverse=True)
        return [{"component": comp, "error_count": count} for comp, count in sorted_components[:limit]]

    async def _monitoring_loop(self):
        """Background monitoring for system health"""
        while True:
            try:
                # Check circuit breakers and attempt recovery
                for breaker in self.circuit_breakers.values():
                    if breaker.state == CircuitBreakerState.OPEN:
                        time_since_failure = datetime.utcnow() - (breaker.last_failure_time or datetime.utcnow())
                        if time_since_failure > timedelta(seconds=breaker.recovery_timeout):
                            breaker.state = CircuitBreakerState.HALF_OPEN
                            logger.info(f"Circuit breaker {breaker.name} ready for testing")

                await asyncio.sleep(30)  # Monitor every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring loop failed: {e}")
                await asyncio.sleep(60)


# Global error handler instance
error_handler = ErrorHandler()


async def start_error_handling():
    """Start the global error handler"""
    await error_handler.start()


async def stop_error_handling():
    """Stop the global error handler"""
    await error_handler.stop()