"""
Bridge Finder
Looks up REAL bridges near a location from OpenStreetMap (Overpass API).

Only bridges that cars drive on are returned (no footbridges, bike paths or
rail bridges). Each bridge comes back with its name, road, distance from the
user, length measured from its geometry, and deck material when OSM has it.

Bridges don't move, so results are cached by area: the first lookup fetches a
whole ~11 km block (plus a margin) and keeps it for a week, in memory and on
disk. Later lookups anywhere in that block are instant, and if OpenStreetMap is
slow or down, an older saved copy is used instead of showing nothing.
"""

import json
import logging
import math
import os
import threading
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# Roads that cars use. Anything else (footway, cycleway, path, railway...) is skipped.
DRIVABLE_HIGHWAYS = (
    "motorway|motorway_link|trunk|trunk_link|primary|primary_link|"
    "secondary|secondary_link|tertiary|tertiary_link|unclassified|residential|service|living_street"
)

# OSM material tags -> the material names the freeze calculator understands
MATERIAL_MAP = {
    "steel": "steel", "metal": "steel", "iron": "steel",
    "concrete": "concrete", "reinforced_concrete": "concrete", "prestressed_concrete": "concrete",
    "stone": "concrete", "brick": "concrete",
    "wood": "wood", "timber": "wood",
    "composite": "composite",
}

CACHE_TTL_SECONDS = 7 * 24 * 3600          # bridges rarely change
TILE_DEG = 0.1                             # cache blocks of ~11 km x 8 km
MARGIN_M = 9000                            # each block also covers 9 km around it
CACHE_PATH = os.getenv('BRIDGE_CACHE_PATH', '/tmp/black_ice_bridge_cache.json')
MAX_POINTS_PER_BRIDGE = 25
FEET_PER_METER = 3.28084
METERS_PER_MILE = 1609.344


class BridgeFinder:
    def __init__(self, session: Optional[requests.Session] = None, cache_path: Optional[str] = CACHE_PATH):
        self.session = session or requests.Session()
        self.cache_path = cache_path
        self._lock = threading.Lock()
        self._cache: Dict[str, list] = self._load_disk_cache()

    # ---------- public ----------

    def find_bridges(self, lat: float, lon: float, radius_m: float = 8000, limit: int = 10) -> Dict:
        """
        Return the nearest real drivable bridges around (lat, lon).

        Returns {'bridges': [...], 'source': 'OpenStreetMap', 'cached': bool}
        or {'bridges': [], 'error': '...'} if every Overpass server failed and nothing is saved.
        """
        radius_m = max(500, min(float(radius_m), MARGIN_M))
        key = self._tile_key(lat, lon)

        with self._lock:
            entry = self._cache.get(key)
        fresh = entry is not None and time.time() - entry[0] < CACHE_TTL_SECONDS

        if fresh:
            all_bridges, from_cache, stale = entry[1], True, False
        else:
            data = self._query_overpass_bbox(self._tile_bbox(key))
            if data is not None:
                all_bridges, from_cache, stale = self._parse(data), False, False
                with self._lock:
                    self._cache[key] = [time.time(), all_bridges]
                self._save_disk_cache()
            elif entry is not None:
                # OpenStreetMap is down or slow: an older copy is far better than nothing
                all_bridges, from_cache, stale = entry[1], True, True
            else:
                return {'bridges': [], 'source': 'OpenStreetMap', 'cached': False,
                        'error': 'Bridge lookup is temporarily unavailable'}

        # Distances depend on where the user is right now, so compute after caching
        results = []
        for b in all_bridges:
            d = self._nearest_point_distance(lat, lon, b['geometry'])
            if d <= radius_m:
                item = {k: v for k, v in b.items() if k != 'geometry'}
                item['distance_m'] = round(d)
                item['distance_mi'] = round(d / METERS_PER_MILE, 2)
                results.append(item)

        results.sort(key=lambda x: x['distance_m'])
        return {'bridges': results[:limit], 'total_found': len(results),
                'source': 'OpenStreetMap', 'cached': from_cache, 'stale': stale}

    # ---------- area cache ----------

    @staticmethod
    def _tile_key(lat: float, lon: float) -> str:
        return f"{math.floor(lat / TILE_DEG)}:{math.floor(lon / TILE_DEG)}"

    @staticmethod
    def _tile_bbox(key: str):
        """(south, west, north, east) of the block plus a MARGIN_M border."""
        ty, tx = (int(v) for v in key.split(':'))
        south, west = ty * TILE_DEG, tx * TILE_DEG
        north, east = south + TILE_DEG, west + TILE_DEG
        dlat = MARGIN_M / 111000.0
        dlon = MARGIN_M / (111000.0 * max(0.2, math.cos(math.radians((south + north) / 2))))
        return (south - dlat, west - dlon, north + dlat, east + dlon)

    def _load_disk_cache(self) -> Dict[str, list]:
        if not self.cache_path:
            return {}
        try:
            with open(self.cache_path) as f:
                data = json.load(f)
            for entry in data.values():          # JSON stores points as lists
                for b in entry[1]:
                    b['geometry'] = [tuple(p) for p in b['geometry']]
            return data
        except Exception:
            return {}

    def _save_disk_cache(self):
        if not self.cache_path:
            return
        try:
            with self._lock:
                snapshot = json.dumps(self._cache)
            tmp = self.cache_path + '.tmp'
            with open(tmp, 'w') as f:
                f.write(snapshot)
            os.replace(tmp, self.cache_path)
        except Exception as e:
            logger.warning(f"Could not save bridge cache: {e}")

    # ---------- Overpass ----------

    def _build_query(self, bbox) -> str:
        south, west, north, east = bbox
        return f"""
        [out:json][timeout:25];
        way["bridge"~"^(yes|viaduct|movable|cantilever|trestle)$"]
           ["highway"~"^({DRIVABLE_HIGHWAYS})$"]
           ({south:.5f},{west:.5f},{north:.5f},{east:.5f});
        out tags geom;
        """

    def _query_overpass_bbox(self, bbox) -> Optional[Dict]:
        query = self._build_query(bbox)
        for url in OVERPASS_URLS:
            try:
                resp = self.session.post(url, data={'data': query}, timeout=20,
                                         headers={'User-Agent': 'QuantumBlackIce/1.0'})
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"Overpass {url} returned {resp.status_code}")
            except Exception as e:
                logger.warning(f"Overpass {url} failed: {e}")
        return None

    # ---------- parsing ----------

    def _parse(self, data: Dict) -> List[Dict]:
        raw = []
        for el in data.get('elements', []):
            if el.get('type') != 'way' or not el.get('geometry'):
                continue
            tags = el.get('tags', {})
            geom = [(p['lat'], p['lon']) for p in el['geometry']]
            length_m = sum(self._haversine(*geom[i], *geom[i + 1]) for i in range(len(geom) - 1))
            if len(geom) > MAX_POINTS_PER_BRIDGE:      # keep the file small; enough for distances
                step = math.ceil(len(geom) / MAX_POINTS_PER_BRIDGE)
                geom = geom[::step] + [geom[-1]]
            if length_m < 5:  # mapping noise, not a real span
                continue

            raw_material = (tags.get('bridge:material') or tags.get('material') or '').lower()
            material = MATERIAL_MAP.get(raw_material)

            road = tags.get('ref') or tags.get('name')
            name = tags.get('bridge:name') or tags.get('name')
            if not name:
                name = f"Bridge on {tags['ref']}" if tags.get('ref') else 'Unnamed bridge'

            raw.append({
                'osm_id': el['id'],
                'name': name,
                'road': road,
                'road_type': tags.get('highway'),
                'length_ft': round(length_m * FEET_PER_METER),
                'material': material or 'concrete',
                'material_known': material is not None,
                'lat': round(sum(p[0] for p in geom) / len(geom), 6),
                'lon': round(sum(p[1] for p in geom) / len(geom), 6),
                'geometry': geom,
            })

        return self._merge_carriageways(raw)

    def _merge_carriageways(self, bridges: List[Dict]) -> List[Dict]:
        """
        Divided highways are mapped as two separate ways (one per direction),
        which would show the same bridge twice. Merge same-named bridges whose
        centers are within 60 m of each other.
        """
        merged: List[Dict] = []
        for b in sorted(bridges, key=lambda x: -x['length_ft']):
            dup = next((m for m in merged
                        if m['name'] == b['name']
                        and self._haversine(m['lat'], m['lon'], b['lat'], b['lon']) < 60), None)
            if dup:
                dup['geometry'] = dup['geometry'] + b['geometry']
                if not dup['material_known'] and b['material_known']:
                    dup['material'], dup['material_known'] = b['material'], True
            else:
                merged.append(dict(b))
        return merged

    # ---------- geometry ----------

    def _nearest_point_distance(self, lat: float, lon: float, geom: List[tuple]) -> float:
        return min(self._haversine(lat, lon, p[0], p[1]) for p in geom)

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2) -> float:
        r = 6371000
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))
