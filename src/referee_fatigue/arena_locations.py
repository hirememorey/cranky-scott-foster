"""NBA arena location metadata for referee travel estimates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArenaLocation:
    team_id: int
    team_abbreviation: str
    city: str
    latitude: float
    longitude: float
    utc_offset: int


ARENA_LOCATIONS_BY_TEAM_ID = {
    1610612737: ArenaLocation(1610612737, "ATL", "Atlanta", 33.7573, -84.3963, -5),
    1610612738: ArenaLocation(1610612738, "BOS", "Boston", 42.3662, -71.0621, -5),
    1610612751: ArenaLocation(1610612751, "BKN", "Brooklyn", 40.6826, -73.9754, -5),
    1610612766: ArenaLocation(1610612766, "CHA", "Charlotte", 35.2251, -80.8392, -5),
    1610612741: ArenaLocation(1610612741, "CHI", "Chicago", 41.8807, -87.6742, -6),
    1610612739: ArenaLocation(1610612739, "CLE", "Cleveland", 41.4965, -81.6882, -5),
    1610612742: ArenaLocation(1610612742, "DAL", "Dallas", 32.7905, -96.8103, -6),
    1610612743: ArenaLocation(1610612743, "DEN", "Denver", 39.7487, -105.0077, -7),
    1610612765: ArenaLocation(1610612765, "DET", "Detroit", 42.3410, -83.0550, -5),
    1610612744: ArenaLocation(1610612744, "GSW", "San Francisco", 37.7680, -122.3877, -8),
    1610612745: ArenaLocation(1610612745, "HOU", "Houston", 29.7508, -95.3621, -6),
    1610612754: ArenaLocation(1610612754, "IND", "Indianapolis", 39.7640, -86.1555, -5),
    1610612746: ArenaLocation(1610612746, "LAC", "Los Angeles", 34.0430, -118.2673, -8),
    1610612747: ArenaLocation(1610612747, "LAL", "Los Angeles", 34.0430, -118.2673, -8),
    1610612763: ArenaLocation(1610612763, "MEM", "Memphis", 35.1383, -90.0505, -6),
    1610612748: ArenaLocation(1610612748, "MIA", "Miami", 25.7814, -80.1870, -5),
    1610612749: ArenaLocation(1610612749, "MIL", "Milwaukee", 43.0451, -87.9172, -6),
    1610612750: ArenaLocation(1610612750, "MIN", "Minneapolis", 44.9795, -93.2761, -6),
    1610612740: ArenaLocation(1610612740, "NOP", "New Orleans", 29.9490, -90.0821, -6),
    1610612752: ArenaLocation(1610612752, "NYK", "New York", 40.7505, -73.9934, -5),
    1610612760: ArenaLocation(1610612760, "OKC", "Oklahoma City", 35.4634, -97.5151, -6),
    1610612753: ArenaLocation(1610612753, "ORL", "Orlando", 28.5392, -81.3839, -5),
    1610612755: ArenaLocation(1610612755, "PHI", "Philadelphia", 39.9012, -75.1720, -5),
    1610612756: ArenaLocation(1610612756, "PHX", "Phoenix", 33.4457, -112.0712, -7),
    1610612757: ArenaLocation(1610612757, "POR", "Portland", 45.5316, -122.6668, -8),
    1610612758: ArenaLocation(1610612758, "SAC", "Sacramento", 38.5802, -121.4997, -8),
    1610612759: ArenaLocation(1610612759, "SAS", "San Antonio", 29.4269, -98.4375, -6),
    1610612761: ArenaLocation(1610612761, "TOR", "Toronto", 43.6435, -79.3791, -5),
    1610612762: ArenaLocation(1610612762, "UTA", "Salt Lake City", 40.7683, -111.9011, -7),
    1610612764: ArenaLocation(1610612764, "WAS", "Washington", 38.8981, -77.0209, -5),
}

