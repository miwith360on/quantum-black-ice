"""
Ground-Truth Feedback System
Collects real-world road condition reports from users to validate predictions
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FeedbackSystem:
    """Collects and analyzes user-reported actual road conditions"""
    
    def __init__(self, data_file='data/feedback_reports.json'):
        self.data_file = data_file
        self.reports = []
        self._ensure_data_dir()
        self._load_reports()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        data_dir = os.path.dirname(self.data_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"Created data directory: {data_dir}")
    
    def _load_reports(self):
        """Load existing feedback reports from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.reports = json.load(f)
                logger.info(f"Loaded {len(self.reports)} feedback reports")
            except Exception as e:
                logger.error(f"Error loading feedback reports: {e}")
                self.reports = []
        else:
            logger.info("No existing feedback reports found")
    
    def _save_reports(self):
        """Save feedback reports to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.reports, f, indent=2)
            logger.info(f"Saved {len(self.reports)} feedback reports")
        except Exception as e:
            logger.error(f"Error saving feedback reports: {e}")
    
    def submit_report(
        self,
        lat: float,
        lon: float,
        actual_condition: str,
        predicted_condition: Optional[str] = None,
        predicted_probability: Optional[float] = None,
        user_comment: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Submit a ground-truth report
        
        Args:
            lat: Latitude
            lon: Longitude
            actual_condition: User-reported actual condition ('dry', 'wet', 'icy', 'snow')
            predicted_condition: What the system predicted
            predicted_probability: Predicted ice probability (0-1)
            user_comment: Optional user comment
            metadata: Additional data (temperature, time of day, etc.)
        
        Returns:
            Report dict with ID and timestamp
        """
        report = {
            'id': len(self.reports) + 1,
            'timestamp': datetime.now().isoformat(),
            'location': {
                'lat': round(lat, 6),
                'lon': round(lon, 6)
            },
            'actual_condition': actual_condition.lower(),
            'predicted_condition': predicted_condition,
            'predicted_probability': predicted_probability,
            'user_comment': user_comment,
            'metadata': metadata or {},
            'upvotes': 0,
            'downvotes': 0
        }
        
        self.reports.append(report)
        self._save_reports()
        
        logger.info(f"New feedback report #{report['id']}: {actual_condition} at ({lat}, {lon})")
        
        return report
    
    def get_reports_nearby(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 5.0,
        max_age_hours: int = 2
    ) -> List[Dict]:
        """
        Get recent reports near a location
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius in miles
            max_age_hours: Maximum age of reports in hours
        
        Returns:
            List of nearby reports
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        nearby_reports = []
        
        for report in self.reports:
            # Check age
            report_time = datetime.fromisoformat(report['timestamp'])
            if report_time < cutoff_time:
                continue
            
            # Check distance
            distance = self._calculate_distance(
                lat, lon,
                report['location']['lat'],
                report['location']['lon']
            )
            
            if distance <= radius_miles:
                report_copy = report.copy()
                report_copy['distance_miles'] = round(distance, 2)
                nearby_reports.append(report_copy)
        
        # Sort by recency
        nearby_reports.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return nearby_reports
    
    def vote_report(self, report_id: int, vote_type: str) -> bool:
        """
        Upvote or downvote a report
        
        Args:
            report_id: Report ID
            vote_type: 'up' or 'down'
        
        Returns:
            Success boolean
        """
        for report in self.reports:
            if report['id'] == report_id:
                if vote_type == 'up':
                    report['upvotes'] = report.get('upvotes', 0) + 1
                elif vote_type == 'down':
                    report['downvotes'] = report.get('downvotes', 0) + 1
                else:
                    return False
                
                self._save_reports()
                logger.info(f"Report #{report_id} voted {vote_type}")
                return True
        
        return False
    
    def get_accuracy_stats(
        self,
        min_confidence: float = 0.5,
        max_age_days: int = 30
    ) -> Dict:
        """
        Calculate prediction accuracy from feedback
        
        Args:
            min_confidence: Minimum prediction confidence to include
            max_age_days: Maximum age of reports to include
        
        Returns:
            Accuracy statistics
        """
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        # Filter reports with predictions
        valid_reports = []
        for report in self.reports:
            if not report.get('predicted_condition'):
                continue
            
            report_time = datetime.fromisoformat(report['timestamp'])
            if report_time < cutoff_time:
                continue
            
            # Check confidence threshold
            predicted_prob = report.get('predicted_probability', 0)
            if predicted_prob < min_confidence:
                continue
            
            valid_reports.append(report)
        
        if not valid_reports:
            return {
                'total_reports': 0,
                'accuracy': 0,
                'message': 'Not enough data'
            }
        
        # Calculate accuracy metrics
        correct = 0
        by_condition = {'dry': {'total': 0, 'correct': 0},
                       'wet': {'total': 0, 'correct': 0},
                       'icy': {'total': 0, 'correct': 0}}
        
        for report in valid_reports:
            actual = report['actual_condition']
            predicted = report['predicted_condition'].lower() if report['predicted_condition'] else 'unknown'
            
            # Map prediction to condition
            if 'ice' in predicted or 'high' in predicted or 'very high' in predicted:
                predicted_cond = 'icy'
            elif 'wet' in predicted or 'medium' in predicted:
                predicted_cond = 'wet'
            else:
                predicted_cond = 'dry'
            
            if actual in by_condition:
                by_condition[actual]['total'] += 1
                if predicted_cond == actual:
                    correct += 1
                    by_condition[actual]['correct'] += 1
        
        accuracy = (correct / len(valid_reports)) * 100 if valid_reports else 0
        
        # Calculate precision/recall for ice detection
        ice_reports = [r for r in valid_reports if r['actual_condition'] == 'icy']
        predicted_ice = [r for r in valid_reports 
                        if 'ice' in (r.get('predicted_condition') or '').lower()]
        
        true_positives = len([r for r in ice_reports 
                             if 'ice' in (r.get('predicted_condition') or '').lower()])
        false_positives = len(predicted_ice) - true_positives
        false_negatives = len(ice_reports) - true_positives
        
        precision = (true_positives / len(predicted_ice) * 100) if predicted_ice else 0
        recall = (true_positives / len(ice_reports) * 100) if ice_reports else 0
        
        return {
            'total_reports': len(valid_reports),
            'correct_predictions': correct,
            'accuracy_percent': round(accuracy, 1),
            'precision_percent': round(precision, 1),
            'recall_percent': round(recall, 1),
            'by_condition': by_condition,
            'ice_detection': {
                'true_positives': true_positives,
                'false_positives': false_positives,
                'false_negatives': false_negatives
            }
        }
    
    def get_recent_stats(self, hours: int = 24) -> Dict:
        """Get statistics for recent reports"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent = [r for r in self.reports 
                 if datetime.fromisoformat(r['timestamp']) > cutoff_time]
        
        if not recent:
            return {'count': 0, 'conditions': {}}
        
        conditions = {}
        for report in recent:
            cond = report['actual_condition']
            conditions[cond] = conditions.get(cond, 0) + 1
        
        return {
            'count': len(recent),
            'conditions': conditions,
            'last_report': recent[-1]['timestamp'] if recent else None
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Returns:
            Distance in miles
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 3959  # Earth's radius in miles
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = (sin(delta_lat / 2) ** 2 +
             cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    def get_all_reports(self, limit: int = 100) -> List[Dict]:
        """Get all reports (most recent first)"""
        sorted_reports = sorted(
            self.reports,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        return sorted_reports[:limit]


# Global instance
feedback_system = FeedbackSystem()
