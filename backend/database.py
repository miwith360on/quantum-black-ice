"""
Database Module
Handles SQLite database operations for storing predictions and historical data
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """SQLite database handler for black ice predictions"""
    
    def __init__(self, db_path: str = '../data/black_ice.db'):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        import os
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)
    
    def initialize(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                risk_level TEXT NOT NULL,
                probability REAL NOT NULL,
                risk_score REAL,
                factors TEXT,
                temperature REAL,
                humidity REAL,
                dew_point REAL,
                wind_speed REAL,
                precipitation REAL
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                risk_level TEXT NOT NULL,
                message TEXT,
                active BOOLEAN DEFAULT 1,
                expires_at DATETIME
            )
        ''')
        
        # Monitored locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Saved routes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                waypoints TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_analyzed DATETIME,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Route analysis history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id INTEGER,
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                max_risk_probability REAL,
                safety_score REAL,
                danger_zone_count INTEGER,
                analysis_data TEXT,
                FOREIGN KEY (route_id) REFERENCES saved_routes(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_location ON predictions(latitude, longitude)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_route_analyses_route_id ON route_analyses(route_id)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def store_prediction(
        self,
        lat: float,
        lon: float,
        risk_level: str,
        probability: float,
        factors: List[Dict],
        temperature: float = None,
        humidity: float = None,
        dew_point: float = None,
        wind_speed: float = None,
        precipitation: float = None
    ):
        """Store a black ice prediction"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        risk_score = sum(f.get('score', 0) for f in factors)
        factors_json = json.dumps(factors)
        
        cursor.execute('''
            INSERT INTO predictions (
                latitude, longitude, risk_level, probability, risk_score,
                factors, temperature, humidity, dew_point, wind_speed, precipitation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lat, lon, risk_level, probability, risk_score,
            factors_json, temperature, humidity, dew_point, wind_speed, precipitation
        ))
        
        # Create alert if risk is high or extreme
        if risk_level in ['high', 'extreme']:
            self._create_alert(cursor, lat, lon, risk_level, probability)
        
        conn.commit()
        conn.close()
        logger.info(f"Stored prediction: {risk_level} at ({lat}, {lon})")
    
    def _create_alert(self, cursor, lat: float, lon: float, risk_level: str, probability: float):
        """Create an alert for high-risk conditions"""
        message = f"Black ice {risk_level.upper()} risk detected ({probability:.0f}% probability)"
        expires_at = datetime.now() + timedelta(hours=6)
        
        cursor.execute('''
            INSERT INTO alerts (latitude, longitude, risk_level, message, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (lat, lon, risk_level, message, expires_at))
    
    def get_location_history(self, lat: float, lon: float, hours: int = 24) -> List[Dict]:
        """Get prediction history for a location"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT timestamp, risk_level, probability, temperature, humidity
            FROM predictions
            WHERE latitude BETWEEN ? AND ?
              AND longitude BETWEEN ? AND ?
              AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (lat - 0.01, lat + 0.01, lon - 0.01, lon + 0.01, since))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'timestamp': row[0],
                'risk_level': row[1],
                'probability': row[2],
                'temperature': row[3],
                'humidity': row[4]
            })
        
        conn.close()
        return history
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Deactivate expired alerts
        cursor.execute('''
            UPDATE alerts
            SET active = 0
            WHERE active = 1 AND expires_at < ?
        ''', (datetime.now(),))
        
        # Fetch active alerts
        cursor.execute('''
            SELECT id, created_at, latitude, longitude, risk_level, message, expires_at
            FROM alerts
            WHERE active = 1
            ORDER BY created_at DESC
        ''')
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'id': row[0],
                'created_at': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'risk_level': row[4],
                'message': row[5],
                'expires_at': row[6]
            })
        
        conn.commit()
        conn.close()
        return alerts
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total predictions
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total_predictions = cursor.fetchone()[0]
        
        # Predictions by risk level (last 7 days)
        since = datetime.now() - timedelta(days=7)
        cursor.execute('''
            SELECT risk_level, COUNT(*) as count
            FROM predictions
            WHERE timestamp >= ?
            GROUP BY risk_level
        ''', (since,))
        
        risk_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Active alerts
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE active = 1')
        active_alerts = cursor.fetchone()[0]
        
        # Average probability (last 24 hours)
        since_24h = datetime.now() - timedelta(hours=24)
        cursor.execute('''
            SELECT AVG(probability)
            FROM predictions
            WHERE timestamp >= ?
        ''', (since_24h,))
        
        avg_probability = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_predictions': total_predictions,
            'risk_distribution_7days': risk_distribution,
            'active_alerts': active_alerts,
            'avg_probability_24h': round(avg_probability, 1),
            'last_updated': datetime.now().isoformat()
        }
    
    def add_monitored_location(self, name: str, lat: float, lon: float):
        """Add a location to monitor"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitored_locations (name, latitude, longitude)
            VALUES (?, ?, ?)
        ''', (name, lat, lon))
        
        conn.commit()
        conn.close()
        logger.info(f"Added monitored location: {name}")
    
    def get_monitored_locations(self) -> List[Dict]:
        """Get all monitored locations"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, latitude, longitude, added_at
            FROM monitored_locations
            WHERE active = 1
            ORDER BY name
        ''')
        
        locations = []
        for row in cursor.fetchall():
            locations.append({
                'id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'added_at': row[4]
            })
        
        conn.close()
        return locations
    
    def save_route(self, name: str, waypoints: List[Dict], description: str = '') -> int:
        """Save a route for quick monitoring"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        waypoints_json = json.dumps(waypoints)
        
        cursor.execute('''
            INSERT INTO saved_routes (name, description, waypoints)
            VALUES (?, ?, ?)
        ''', (name, description, waypoints_json))
        
        route_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Saved route: {name} (ID: {route_id})")
        return route_id
    
    def get_saved_routes(self) -> List[Dict]:
        """Get all saved routes"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, waypoints, created_at, last_analyzed
            FROM saved_routes
            WHERE active = 1
            ORDER BY name
        ''')
        
        routes = []
        for row in cursor.fetchall():
            routes.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'waypoints': json.loads(row[3]),
                'created_at': row[4],
                'last_analyzed': row[5]
            })
        
        conn.close()
        return routes
    
    def store_route_analysis(self, analysis: Dict, route_id: int = None):
        """Store route analysis results"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        summary = analysis.get('route_summary', {})
        analysis_json = json.dumps(analysis)
        
        cursor.execute('''
            INSERT INTO route_analyses (
                route_id, max_risk_probability, safety_score, 
                danger_zone_count, analysis_data
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            route_id,
            summary.get('max_risk_probability'),
            summary.get('safety_score'),
            summary.get('danger_zone_count'),
            analysis_json
        ))
        
        # Update last_analyzed timestamp for saved route
        if route_id:
            cursor.execute('''
                UPDATE saved_routes
                SET last_analyzed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (route_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Stored route analysis")
    
    def get_route_history(self, route_id: int, limit: int = 10) -> List[Dict]:
        """Get analysis history for a saved route"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT analyzed_at, max_risk_probability, safety_score, danger_zone_count
            FROM route_analyses
            WHERE route_id = ?
            ORDER BY analyzed_at DESC
            LIMIT ?
        ''', (route_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'analyzed_at': row[0],
                'max_risk_probability': row[1],
                'safety_score': row[2],
                'danger_zone_count': row[3]
            })
        
        conn.close()
        return history
