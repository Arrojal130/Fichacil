"""
FichaFacil MVP - Geolocation Utilities
Distance calculation and validation.
"""
from math import radians, cos, sin, asin, sqrt
from typing import Optional, Tuple
from app.config import get_settings

settings = get_settings()


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the great circle distance in meters between two points 
    on the earth (specified in decimal degrees).
    
    Uses the Haversine formula.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Earth's radius in meters
    r = 6371000
    
    return c * r


def calculate_distance_to_business(
    empleado_lat: Optional[float],
    empleado_lon: Optional[float],
    negocio_lat: Optional[float],
    negocio_lon: Optional[float]
) -> Optional[float]:
    """
    Calculate distance from employee to business center.
    Returns None if any coordinate is missing.
    """
    if None in (empleado_lat, empleado_lon, negocio_lat, negocio_lon):
        return None
    
    return haversine_distance(
        empleado_lat,
        empleado_lon,
        negocio_lat,
        negocio_lon
    )


def check_distance_alert(
    distance_meters: Optional[float],
    max_distance: int = None
) -> Tuple[bool, str]:
    """
    Check if distance exceeds threshold.
    Returns (is_alert, message).
    
    Note: Does NOT block clock-in, only alerts.
    """
    if max_distance is None:
        max_distance = settings.max_distance_meters
    
    if distance_meters is None:
        return True, "Sin ubicación disponible"
    
    if distance_meters > max_distance:
        return True, f"Distancia: {distance_meters:.0f}m (>{max_distance}m)"
    
    return False, f"Distancia: {distance_meters:.0f}m ✓"


def format_distance(distance_meters: Optional[float]) -> str:
    """Format distance for display."""
    if distance_meters is None:
        return "Sin ubicación"
    
    if distance_meters < 1000:
        return f"{distance_meters:.0f}m"
    else:
        return f"{distance_meters/1000:.1f}km"
