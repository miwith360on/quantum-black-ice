"""
Centralized Logging Configuration for Quantum Black Ice System
Structured JSON logging with Sentry integration for production monitoring
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from pythonjsonlogger import jsonlogger

# Configure Sentry (if DSN provided)
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FlaskIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        environment=os.getenv('RAILWAY_ENVIRONMENT', 'development'),
        release=os.getenv('GIT_COMMIT', 'dev')
    )


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add service context
        log_record['service'] = 'quantum-black-ice'
        
        # Add environment
        log_record['environment'] = os.getenv('RAILWAY_ENVIRONMENT', 'development')
        
        # Add file and line number for debugging
        if record.pathname:
            log_record['file'] = Path(record.pathname).name
            log_record['line'] = record.lineno


def setup_logging(name=None, level=None):
    """
    Setup structured logging with JSON format
    
    Args:
        name: Logger name (defaults to root)
        level: Logging level (defaults to INFO in production, DEBUG in development)
    
    Returns:
        Configured logger instance
    """
    # Determine log level
    if level is None:
        is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
        level = logging.INFO if is_production else logging.DEBUG
    
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Use JSON formatter in production, simple format in development
    is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    if is_production:
        # JSON formatter for structured logging
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Simple format for local development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def log_api_request(logger, endpoint, params=None, duration_ms=None):
    """
    Log API request with structured data
    
    Args:
        logger: Logger instance
        endpoint: API endpoint path
        params: Request parameters (dict)
        duration_ms: Request duration in milliseconds
    """
    logger.info(
        "API request",
        extra={
            'endpoint': endpoint,
            'params': params or {},
            'duration_ms': duration_ms,
            'type': 'api_request'
        }
    )


def log_prediction(logger, prediction_type, input_data, result, confidence=None):
    """
    Log prediction with structured data
    
    Args:
        logger: Logger instance
        prediction_type: Type of prediction (quantum, ml, bifi, etc.)
        input_data: Input parameters
        result: Prediction result
        confidence: Confidence score (0-100)
    """
    logger.info(
        f"{prediction_type} prediction",
        extra={
            'prediction_type': prediction_type,
            'input': input_data,
            'result': result,
            'confidence': confidence,
            'type': 'prediction'
        }
    )


def log_error(logger, error, context=None):
    """
    Log error with context and send to Sentry
    
    Args:
        logger: Logger instance
        error: Exception or error message
        context: Additional context (dict)
    """
    logger.error(
        str(error),
        extra={
            'error_type': type(error).__name__ if isinstance(error, Exception) else 'Error',
            'context': context or {},
            'type': 'error'
        },
        exc_info=isinstance(error, Exception)
    )


def log_performance(logger, operation, duration_ms, metadata=None):
    """
    Log performance metric
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        metadata: Additional metadata
    """
    logger.info(
        f"Performance: {operation}",
        extra={
            'operation': operation,
            'duration_ms': duration_ms,
            'metadata': metadata or {},
            'type': 'performance'
        }
    )


# Create default logger
default_logger = setup_logging('quantum-black-ice')


# Example usage:
if __name__ == '__main__':
    logger = setup_logging()
    
    logger.info("Logging system initialized")
    log_api_request(logger, "/api/weather/current", {"lat": 42.3, "lon": -83.0}, 150)
    log_prediction(logger, "quantum", {"temp": 32}, "high_risk", 85)
    log_performance(logger, "weather_api_call", 234, {"source": "openmeteo"})
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error(logger, e, {"test": "context"})
