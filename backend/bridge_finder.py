"""
Bridge Finder
Looks up REAL bridges near a location from OpenStreetMap (Overpass API).

Only bridges that cars drive on are returned (no footbridges, bike paths or
rail bridges). Each bridge comes back with its name, road, distance from the
user, length measured from its geometry, and deck material when OSM has it.

Bridges don't move, so results are cached in memory for a day per ~1 km cell
to keep the app fast and stay well under Overpass rate limits.
"""

import logging
import math
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
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

CACHE_TTL_SECONDS = 24 * 3600
FEET_PER_METER = 3.28084
METERS_PER_MILE = 1609.344


class BridgeFinder:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self._cache: Dict[tuple, tuple] = {}

    # ---------- public ----------

    def find_bridges(self, lat: float, lon: float, radius_m: float = 8000, limit: int = 10) -> Dict:
        """
        Return the nearest real drivable bridges around (lat, lon).

        Returns {'bridges': [...], 'source': 'OpenStreetMap', 'cached': bool}
        or {'bridges': [], 'error': '...'} if every Overpass server failed.
        """
        radius_m = max(500, min(float(radius_m), 25000))
        key = (round(lat, 2), round(lon, 2), int(radius_m))

        cached = self._cache.get(key)
        if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
            all_bridges = cached[1]
            from_cache = True
        else:
            data = self._query_overpass(lat, lon, radius_m)
            if data is None:
                return {'bridges': [], 'source': 'OpenStreetMap', 'cached': False,
                        'error': 'Bridge lookup is temporarily unavailable'}
            all_bridges = self._parse(data)
            self._cache[key] = (time.time(), all_bridges)
            from_cache = False

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
                'source': 'OpenStreetMap', 'cached': from_cache}

    # ---------- Overpass ----------

    def _build_query(self, lat: float, lon: float, radius_m: float) -> str:
        return f"""
        [out:json][timeout:15];
        way["bridge"~"^(yes|viaduct|movable|cantilever|trestle)$"]
           ["highway"~"^({DRIVABLE_HIGHWAYS})$"]
           (around:{int(radius_m)},{lat},{lon});
        out tags geom;
        """

    def _query_overpass(self, lat: float, lon: float, radius_m: float) -> Optional[Dict]:
        query = self._build_query(lat, lon, radius_m)
        for url in OVERPASS_URLS:
            try:
                resp = self.session.post(url, data={"data": query}, timeout=12,
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
