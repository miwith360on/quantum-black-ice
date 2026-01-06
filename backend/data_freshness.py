"""
Data Freshness Tracking System
Tracks age of data sources and adjusts confidence accordingly
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataFreshnessTracker:
    """Track data freshness and calculate confidence adjustments"""
    
    # Maximum acceptable data age (in minutes) before confidence degrades
    FRESHNESS_THRESHOLDS = {
        'rwis': 5,           # Road sensors should be very fresh
        'radar': 2,          # Radar data updates frequently
        'weather_api': 15,   # Weather APIs update every 10-15 min
        'noaa': 10,          # NOAA observations
        'satellite': 30,     # Satellite imagery
        'forecast': 60,      # Forecast data is less time-critical
        'traffic': 5,        # Traffic data should be real-time
    }
    
    # Confidence penalty multipliers based on staleness
    CONFIDENCE_DECAY = {
        'fresh': 1.0,        # 0-100% of threshold: no penalty
        'recent': 0.95,      # 100-150% of threshold: 5% penalty
        'stale': 0.80,       # 150-200% of threshold: 20% penalty
        'very_stale': 0.60,  # 200-300% of threshold: 40% penalty
        'outdated': 0.30,    # >300% of threshold: 70% penalty
    }
    
    def __init__(self):
        self.data_timestamps = {}
    
    def update_timestamp(self, source: str, timestamp: Optional[datetime] = None):
        """
        Record when data was fetched from a source
        
        Args:
            source: Data source name (rwis, radar, weather_api, etc.)
            timestamp: Time data was fetched (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.data_timestamps[source] = timestamp
        logger.debug(f"Updated timestamp for {source}: {timestamp}")
    
    def get_data_age(self, source: str) -> Optional[float]:
        """
        Get age of data in minutes
        
        Args:
            source: Data source name
            
        Returns:
            Age in minutes, or None if no timestamp recorded
        """
        if source not in self.data_timestamps:
            return None
        
        age = (datetime.now() - self.data_timestamps[source]).total_seconds() / 60
        return age
    
    def get_freshness_status(self, source: str) -> Dict:
        """
        Get freshness status for a data source
        
        Args:
            source: Data source name
            
        Returns:
            Dict with age, status, confidence_multiplier, and message
        """
        age = self.get_data_age(source)
        
        if age is None:
            return {
                'source': source,
                'status': 'unknown',
                'age_minutes': None,
                'age_display': 'Unknown',
                'confidence_multiplier': 0.70,
                'message': f'No {source} data available',
                'color': '#6b7280'  # gray
            }
        
        threshold = self.FRESHNESS_THRESHOLDS.get(source, 15)
        
        # Determine freshness status
        if age <= threshold:
            status = 'fresh'
            color = '#10b981'  # green
            message = f'{source.upper()}: {self._format_age(age)} ago'
        elif age <= threshold * 1.5:
            status = 'recent'
            color = '#eab308'  # yellow
            message = f'{source.upper()}: {self._format_age(age)} ago (slightly stale)'
        elif age <= threshold * 2:
            status = 'stale'
            color = '#f59e0b'  # orange
            message = f'{source.upper()}: {self._format_age(age)} ago (stale)'
        elif age <= threshold * 3:
            status = 'very_stale'
            color = '#dc2626'  # red
            message = f'{source.upper()}: {self._format_age(age)} ago (very stale)'
        else:
            status = 'outdated'
            color = '#991b1b'  # dark red
            message = f'{source.upper()}: {self._format_age(age)} ago (outdated)'
        
        confidence_multiplier = self.CONFIDENCE_DECAY[status]
        
        return {
            'source': source,
            'status': status,
            'age_minutes': round(age, 1),
            'age_display': self._format_age(age),
            'confidence_multiplier': confidence_multiplier,
            'message': message,
            'color': color,
            'threshold_minutes': threshold
        }
    
    def calculate_overall_confidence(self, sources: list, base_confidence: float) -> Dict:
        """
        Calculate overall confidence considering all data sources
        
        Args:
            sources: List of data source names used
            base_confidence: Base confidence from prediction model (0-1)
            
        Returns:
            Dict with adjusted confidence and explanations
        """
        if not sources:
            return {
                'confidence': base_confidence * 0.70,
                'base_confidence': base_confidence,
                'freshness_penalty': 0.30,
                'explanation': 'No data sources available',
                'sources': []
            }
        
        # Get freshness status for all sources
        freshness_data = [self.get_freshness_status(src) for src in sources]
        
        # Calculate weighted average of confidence multipliers
        # Weight critical sources (rwis, radar) more heavily
        weights = {
            'rwis': 2.0,
            'radar': 1.5,
            'weather_api': 1.0,
            'noaa': 1.0,
            'satellite': 0.5,
            'forecast': 0.3,
            'traffic': 0.5
        }
        
        total_weight = 0
        weighted_multiplier = 0
        
        for f in freshness_data:
            source = f['source']
            weight = weights.get(source, 1.0)
            total_weight += weight
            weighted_multiplier += f['confidence_multiplier'] * weight
        
        avg_multiplier = weighted_multiplier / total_weight if total_weight > 0 else 0.70
        adjusted_confidence = base_confidence * avg_multiplier
        
        # Find most critical issue
        stale_sources = [f for f in freshness_data if f['status'] in ['stale', 'very_stale', 'outdated']]
        missing_sources = [f for f in freshness_data if f['status'] == 'unknown']
        
        explanation_parts = []
        if stale_sources:
            explanation_parts.append(f"{len(stale_sources)} stale data source(s)")
        if missing_sources:
            explanation_parts.append(f"{len(missing_sources)} missing data source(s)")
        if not explanation_parts:
            explanation_parts.append("All data sources fresh")
        
        explanation = ", ".join(explanation_parts)
        
        return {
            'confidence': round(adjusted_confidence, 3),
            'base_confidence': round(base_confidence, 3),
            'freshness_multiplier': round(avg_multiplier, 3),
            'freshness_penalty': round(1 - avg_multiplier, 3),
            'explanation': explanation,
            'sources': freshness_data
        }
    
    def _format_age(self, minutes: float) -> str:
        """Format age in human-readable format"""
        if minutes < 1:
            return f"{int(minutes * 60)}s"
        elif minutes < 60:
            return f"{int(minutes)}min"
        else:
            hours = int(minutes / 60)
            mins = int(minutes % 60)
            if mins == 0:
                return f"{hours}hr"
            return f"{hours}hr {mins}min"
    
    def get_all_freshness(self) -> Dict:
        """Get freshness status for all tracked sources"""
        return {
            source: self.get_freshness_status(source)
            for source in self.data_timestamps.keys()
        }
    
    def clear_old_timestamps(self, max_age_hours: int = 24):
        """Clear timestamps older than max_age_hours"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        old_sources = [
            source for source, ts in self.data_timestamps.items()
            if ts < cutoff
        ]
        for source in old_sources:
            del self.data_timestamps[source]
            logger.info(f"Cleared old timestamp for {source}")


# Global instance
freshness_tracker = DataFreshnessTracker()
