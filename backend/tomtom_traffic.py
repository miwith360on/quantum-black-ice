"""
TomTom Traffic
Real crashes, hazards and slowdowns near the user, from TomTom's Traffic API.

Why TomTom: free tier with no credit card (2,500 data requests + 50,000 map tiles a day),
real incident data (accidents, ice, closures), and when the free limit is reached it
returns HTTP 429 instead of charging. The API key stays on the server: the map tiles
are proxied through our backend so the key is never in the app's page or URLs.

Set TOMTOM_API_KEY in the environment (Railway → Variables).
"""

import logging
import math
import os
import threading
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

BASE = "https://api.tomtom.com"

# TomTom iconCategory codes (Traffic API v5, Incident Details)
CATEGORY_NAMES = {
    0: 'Unknown', 1: 'Accident', 2: 'Fog', 3: 'Dangerous conditions', 4: 'Rain',
    5: 'Ice', 6: 'Traffic jam', 7: 'Lane closed', 8: 'Road closed', 9: 'Road works',
    10: 'Wind', 11: 'Flooding', 14: 'Broken down vehicle',
}
CATEGORY_ICONS = {
    1: '💥', 2: '🌫️', 3: '⚠️', 4: '🌧️', 5: '🧊', 6: '🚗', 7: '🚧', 8: '⛔',
    9: '🚧', 10: '💨', 11: '🌊', 14: '🚙',
}
DELAY_NAMES = {0: 'Unknown', 1: 'Minor', 2: 'Moderate', 3: 'Major', 4: 'Closure'}

INCIDENT_FIELDS = (
    "{incidents{type,geometry{type,coordinates},"
    "properties{id,iconCategory,magnitudeOfDelay,events{description,code,iconCategory},"
    "startTime,from,to,length,delay,roadNumbers,timeValidity}}}"
)

DATA_CACHE_SECONDS = 120      # incidents/flow: refresh at most every 2 minutes per area
TILE_CACHE_SECONDS = 60
TILE_CACHE_MAX = 500


class TomTomTraffic:
    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.getenv('TOMTOM_API_KEY')
        self.session = session or requests.Session()
        self._cache: Dict[tuple, tuple] = {}
        self._tiles: Dict[tuple, tuple] = {}
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    # ---------------- incidents ----------------

    def get_incidents(self, lat: float, lon: float, radius_km: float = 10) -> Dict:
        """Current incidents (crashes, ice, closures...) within radius_km of the point."""
        if not self.available:
            return {'available': False, 'incidents': []}
        radius_km = max(1.0, min(float(radius_km), 45.0))  # TomTom allows up to 10,000 km² bbox
        key = ('inc', round(lat, 2), round(lon, 2), int(radius_km))
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        dlat = radius_km / 111.0
        dlon = radius_km / (111.0 * max(0.2, math.cos(math.radians(lat))))
        bbox = f"{lon - dlon:.5f},{lat - dlat:.5f},{lon + dlon:.5f},{lat + dlat:.5f}"
        try:
            r = self.session.get(
                f"{BASE}/traffic/services/5/incidentDetails",
                params={'key': self.api_key, 'bbox': bbox, 'fields': INCIDENT_FIELDS,
                        'language': 'en-US', 'timeValidityFilter': 'present'},
                timeout=10)
            if r.status_code == 429:
                return {'available': True, 'incidents': [], 'error': 'Daily free limit reached'}
            r.raise_for_status()
            raw = r.json().get('incidents', [])
        except Exception as e:
            logger.warning(f"TomTom incidents failed: {e}")
            return {'available': True, 'incidents': [], 'error': 'Traffic data temporarily unavailable'}

        incidents = []
        for inc in raw:
            p = inc.get('properties', {})
            pt = self._first_point(inc.get('geometry'))
            if not pt:
                continue
            cat = p.get('iconCategory', 0)
            events = p.get('events') or []
            desc = ', '.join(e.get('description', '') for e in events if e.get('description')) or CATEGORY_NAMES.get(cat, 'Incident')
            event_cats = {e.get('iconCategory') for e in events} | {cat}
            dist_km = self._km(lat, lon, pt[1], pt[0])
            if dist_km > radius_km:
                continue
            incidents.append({
                'id': p.get('id'),
                'category': CATEGORY_NAMES.get(cat, 'Incident'),
                'category_code': cat,
                'icon': CATEGORY_ICONS.get(cat, '⚠️'),
                'description': desc,
                'from': p.get('from'),
                'to': p.get('to'),
                'roads': p.get('roadNumbers') or [],
                'delay_min': round((p.get('delay') or 0) / 60),
                'severity': DELAY_NAMES.get(p.get('magnitudeOfDelay', 0), 'Unknown'),
                'start_time': p.get('startTime'),
                'lat': pt[1], 'lon': pt[0],
                'distance_mi': round(dist_km * 0.621371, 1),
                'is_crash': 1 in event_cats,
                'is_ice': 5 in event_cats,
                'is_hazard': bool(event_cats & {2, 3, 5, 11}),
            })

        # Most relevant first: ice, crashes, other hazards, then everything else; closest first within each
        incidents.sort(key=lambda i: (not i['is_ice'], not i['is_crash'], not i['is_hazard'], i['distance_mi']))
        result = {'available': True, 'incidents': incidents, 'source': 'TomTom'}
        self._put_cached(key, result)
        return result

    # ---------------- flow ----------------

    def get_flow(self, lat: float, lon: float) -> Dict:
        """Speed on the nearest road vs. its normal free-flow speed."""
        if not self.available:
            return {'available': False}
        key = ('flow', round(lat, 3), round(lon, 3))
        cached = self._get_cached(key)
        if cached is not None:
            return cached
        try:
            r = self.session.get(
                f"{BASE}/traffic/services/4/flowSegmentData/relative0/10/json",
                params={'key': self.api_key, 'point': f"{lat},{lon}", 'unit': 'mph'},
                timeout=10)
            if r.status_code == 429:
                return {'available': True, 'error': 'Daily free limit reached'}
            r.raise_for_status()
            d = r.json().get('flowSegmentData', {})
        except Exception as e:
            logger.warning(f"TomTom flow failed: {e}")
            return {'available': True, 'error': 'Traffic data temporarily unavailable'}

        cur, free = d.get('currentSpeed'), d.get('freeFlowSpeed')
        slowdown = None
        if cur is not None and free:
            slowdown = max(0, round((1 - cur / free) * 100))
        result = {
            'available': True,
            'current_speed_mph': cur,
            'normal_speed_mph': free,
            'slowdown_percent': slowdown,
            'road_closed': bool(d.get('roadClosure')),
            'confidence': d.get('confidence'),
            'source': 'TomTom',
        }
        self._put_cached(key, result)
        return result

    # ---------------- map tiles (proxied so the key stays private) ----------------

    def get_flow_tile(self, z: int, x: int, y: int) -> Optional[bytes]:
        if not self.available or not (0 <= z <= 22):
            return None
        key = (z, x, y)
        now = time.time()
        with self._lock:
            hit = self._tiles.get(key)
            if hit and now - hit[0] < TILE_CACHE_SECONDS:
                return hit[1]
        try:
            r = self.session.get(
                f"{BASE}/traffic/map/4/tile/flow/relative0/{z}/{x}/{y}.png",
                params={'key': self.api_key, 'tileSize': 256}, timeout=10)
            if r.status_code != 200:
                return None
            data = r.content
        except Exception as e:
            logger.warning(f"TomTom tile failed: {e}")
            return None
        with self._lock:
            if len(self._tiles) >= TILE_CACHE_MAX:
                self._tiles.pop(next(iter(self._tiles)))
            self._tiles[key] = (now, data)
        return data

    # ---------------- helpers ----------------

    def _get_cached(self, key):
        with self._lock:
            hit = self._cache.get(key)
        if hit and time.time() - hit[0] < DATA_CACHE_SECONDS:
            return hit[1]
        return None

    def _put_cached(self, key, value):
        with self._lock:
            if len(self._cache) > 2000:
                self._cache.clear()
            self._cache[key] = (time.time(), value)

    @staticmethod
    def _first_point(geom) -> Optional[List[float]]:
        """[lon, lat] of an incident: the point itself, or the start of its line."""
        if not geom:
            return None
        c = geom.get('coordinates')
        if geom.get('type') == 'Point' and c:
            return c
        if geom.get('type') == 'LineString' and c:
            return c[0]
        return None

    @staticmethod
    def _km(lat1, lon1, lat2, lon2) -> float:
        r = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))


def ice_crash_signal(incidents: List[Dict], temperature_f: Optional[float]) -> Optional[Dict]:
    """
    Turn incidents + temperature into a plain-language warning.
    TomTom 'Ice' reports are direct evidence. Several crashes in freezing weather are a strong hint.
    """
    ice = [i for i in incidents if i['is_ice']]
    crashes = [i for i in incidents if i['is_crash']]
    if ice:
        nearest = min(ice, key=lambda i: i['distance_mi'])
        return {'level': 'high',
                'message': f"🧊 Ice reported on the road {nearest['distance_mi']} mi from you"
                           + (f" ({nearest['from']})" if nearest.get('from') else '') + '.'}
    if temperature_f is not None and temperature_f <= 34 and len(crashes) >= 2:
        return {'level': 'high',
                'message': f"💥 {len(crashes)} crashes near you while it's {round(temperature_f)}°F. Roads may be icy."}
    if temperature_f is not None and temperature_f <= 34 and len(crashes) == 1:
        return {'level': 'moderate',
                'message': f"💥 A crash {crashes[0]['distance_mi']} mi away in freezing weather. Drive carefully."}
    return None
