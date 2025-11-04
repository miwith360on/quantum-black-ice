"""
Real-Time WebSocket Server for Live Data Streaming
Provides instant updates for weather, predictions, and radar data
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Optional
import traceback

try:
    from flask_socketio import SocketIO, emit, join_room, leave_room
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    logging.warning("flask-socketio not installed - WebSocket features disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and real-time data streaming
    Supports rooms for location-specific updates
    """
    
    def __init__(self, socketio: Optional[object] = None):
        self.socketio = socketio
        self.active_connections: Set[str] = set()
        self.location_subscriptions: Dict[str, Set[str]] = {}
        self.update_intervals: Dict[str, int] = {
            'weather': 60,      # Update every 60 seconds
            'prediction': 30,   # Update every 30 seconds
            'radar': 120,       # Update every 2 minutes
            'alerts': 10        # Check alerts every 10 seconds
        }
        self.streaming_tasks: Dict[str, asyncio.Task] = {}
        
    def initialize(self, app, socketio):
        """Initialize WebSocket with Flask app"""
        if not SOCKETIO_AVAILABLE:
            logger.warning("SocketIO not available - skipping initialization")
            return
        
        self.socketio = socketio
        self._register_handlers()
        logger.info("WebSocket server initialized")
    
    def _register_handlers(self):
        """Register all WebSocket event handlers"""
        if not self.socketio:
            return
        
        @self.socketio.on('connect')
        def handle_connect():
            client_id = self._get_client_id()
            self.active_connections.add(client_id)
            logger.info(f"Client connected: {client_id}")
            emit('connection_status', {
                'connected': True,
                'client_id': client_id,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            client_id = self._get_client_id()
            self.active_connections.discard(client_id)
            
            # Remove from all location subscriptions
            for location_id, subscribers in self.location_subscriptions.items():
                subscribers.discard(client_id)
            
            logger.info(f"Client disconnected: {client_id}")
        
        @self.socketio.on('subscribe_location')
        def handle_subscribe(data):
            """Subscribe to updates for a specific location"""
            client_id = self._get_client_id()
            lat = data.get('lat')
            lon = data.get('lon')
            
            if lat is None or lon is None:
                emit('error', {'message': 'Invalid location coordinates'})
                return
            
            location_id = f"{lat:.4f},{lon:.4f}"
            room_name = f"location_{location_id}"
            
            # Join the room
            join_room(room_name)
            
            # Track subscription
            if location_id not in self.location_subscriptions:
                self.location_subscriptions[location_id] = set()
            self.location_subscriptions[location_id].add(client_id)
            
            logger.info(f"Client {client_id} subscribed to location {location_id}")
            emit('subscription_confirmed', {
                'location': location_id,
                'room': room_name,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('unsubscribe_location')
        def handle_unsubscribe(data):
            """Unsubscribe from location updates"""
            client_id = self._get_client_id()
            lat = data.get('lat')
            lon = data.get('lon')
            
            if lat is None or lon is None:
                return
            
            location_id = f"{lat:.4f},{lon:.4f}"
            room_name = f"location_{location_id}"
            
            # Leave the room
            leave_room(room_name)
            
            # Remove from subscriptions
            if location_id in self.location_subscriptions:
                self.location_subscriptions[location_id].discard(client_id)
            
            logger.info(f"Client {client_id} unsubscribed from location {location_id}")
        
        @self.socketio.on('request_update')
        def handle_update_request(data):
            """Handle manual update request from client"""
            update_type = data.get('type', 'all')
            location = data.get('location')
            
            logger.info(f"Update requested: {update_type} for {location}")
            emit('update_received', {
                'type': update_type,
                'processing': True,
                'timestamp': datetime.now().isoformat()
            })
    
    def _get_client_id(self) -> str:
        """Get the current client's ID"""
        try:
            from flask import request
            return request.sid
        except:
            return 'unknown'
    
    def broadcast_weather_update(self, location_id: str, weather_data: Dict):
        """
        Broadcast weather update to all subscribers of a location
        
        Args:
            location_id: Location identifier (e.g., "lat,lon")
            weather_data: Weather information dictionary
        """
        if not self.socketio:
            return
        
        try:
            room_name = f"location_{location_id}"
            self.socketio.emit('weather_update', {
                'location': location_id,
                'data': weather_data,
                'timestamp': datetime.now().isoformat()
            }, room=room_name)
            
            logger.debug(f"Weather update broadcast to {room_name}")
        except Exception as e:
            logger.error(f"Error broadcasting weather update: {e}")
    
    def broadcast_prediction_update(self, location_id: str, prediction_data: Dict):
        """
        Broadcast black ice prediction update
        
        Args:
            location_id: Location identifier
            prediction_data: Prediction information dictionary
        """
        if not self.socketio:
            return
        
        try:
            room_name = f"location_{location_id}"
            self.socketio.emit('prediction_update', {
                'location': location_id,
                'data': prediction_data,
                'timestamp': datetime.now().isoformat()
            }, room=room_name)
            
            logger.debug(f"Prediction update broadcast to {room_name}")
        except Exception as e:
            logger.error(f"Error broadcasting prediction update: {e}")
    
    def broadcast_radar_update(self, location_id: str, radar_data: Dict):
        """
        Broadcast radar data update
        
        Args:
            location_id: Location identifier
            radar_data: Radar information dictionary
        """
        if not self.socketio:
            return
        
        try:
            room_name = f"location_{location_id}"
            self.socketio.emit('radar_update', {
                'location': location_id,
                'data': radar_data,
                'timestamp': datetime.now().isoformat()
            }, room=room_name)
            
            logger.debug(f"Radar update broadcast to {room_name}")
        except Exception as e:
            logger.error(f"Error broadcasting radar update: {e}")
    
    def broadcast_alert(self, alert_data: Dict, location_id: Optional[str] = None):
        """
        Broadcast weather alert
        
        Args:
            alert_data: Alert information dictionary
            location_id: Optional location identifier (broadcasts to all if None)
        """
        if not self.socketio:
            return
        
        try:
            if location_id:
                room_name = f"location_{location_id}"
                self.socketio.emit('weather_alert', {
                    'alert': alert_data,
                    'timestamp': datetime.now().isoformat()
                }, room=room_name)
            else:
                # Broadcast to all connected clients
                self.socketio.emit('weather_alert', {
                    'alert': alert_data,
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"Alert broadcast: {alert_data.get('headline', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error broadcasting alert: {e}")
    
    def get_connection_stats(self) -> Dict:
        """Get statistics about active connections"""
        return {
            'active_connections': len(self.active_connections),
            'subscribed_locations': len(self.location_subscriptions),
            'location_details': {
                location_id: len(subscribers)
                for location_id, subscribers in self.location_subscriptions.items()
            },
            'socketio_available': SOCKETIO_AVAILABLE,
            'timestamp': datetime.now().isoformat()
        }
    
    async def start_background_streaming(self, weather_service, predictor, radar_service):
        """
        Start background task for streaming updates to subscribed locations
        
        Args:
            weather_service: WeatherService instance
            predictor: BlackIcePredictor instance
            radar_service: RadarService instance
        """
        if not self.socketio:
            logger.warning("Cannot start background streaming - SocketIO not initialized")
            return
        
        logger.info("Starting background streaming service...")
        
        while True:
            try:
                # Update each subscribed location
                for location_id in list(self.location_subscriptions.keys()):
                    if not self.location_subscriptions[location_id]:
                        continue
                    
                    # Parse location
                    try:
                        lat, lon = map(float, location_id.split(','))
                    except:
                        continue
                    
                    # Fetch and broadcast weather data
                    weather_data = weather_service.get_current_weather(lat, lon)
                    if weather_data:
                        self.broadcast_weather_update(location_id, weather_data)
                        
                        # Get and broadcast prediction
                        prediction = predictor.predict(weather_data)
                        self.broadcast_prediction_update(location_id, prediction)
                    
                    # Fetch and broadcast radar data (less frequently)
                    radar_data = radar_service.get_radar_layers(lat, lon)
                    if radar_data.get('success'):
                        self.broadcast_radar_update(location_id, radar_data)
                        
                        # Broadcast any alerts
                        for alert in radar_data.get('alerts', []):
                            self.broadcast_alert(alert, location_id)
                
                # Wait before next update cycle
                await asyncio.sleep(self.update_intervals['weather'])
                
            except Exception as e:
                logger.error(f"Error in background streaming: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(10)
