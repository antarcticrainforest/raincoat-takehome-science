"""Collection of methods to calcuated paths."""


from typing import Tuple

import numpy as np


def haversine_distance(point1: np.ndarray, point2: np.ndarray) -> np.ndarray:
    lat1, lon1 = np.radians(point1)
    lat2, lon2 = np.radians(point2)
    # Earth radius in meters
    earth_radius = 6371000  # Approximately 6371 km

    # Haversine formula to calculate distance
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    a = (
        np.sin(d_lat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(d_lon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = earth_radius * c
    return distance


def calculate_wind_at_given_distance(
    max_wind: float,
    max_wind_radius: float,
    loc: np.ndarray,
    centre: np.ndarray,
) -> float:
    """Calculate the windspeed at a given location."""
    radius = haversine_distance(loc, centre)
    mask_radius_leq = radius <= max_wind_radius
    mask_radius_gt = ~mask_radius_leq
    result = np.empty_like(radius)
    result[mask_radius_leq] = max_wind * (
        radius[mask_radius_leq] / max_wind_radius
    ) ** (3 / 2)
    result[mask_radius_gt] = max_wind * (
        max_wind_radius / radius[mask_radius_gt]
    ) ** (1 / 2)
    return result
