"""Collection of methods to calcuated paths."""


from typing import List, cast

import numpy as np
from numpy.typing import NDArray


def haversine_distance(
    point1: List[NDArray[np.float_]], point2: List[NDArray[np.float_]]
) -> NDArray[np.float_]:
    """
    Calculate the haversine distance between to points on th earth surface.
    """
    lat1, lon1 = np.radians(point1)
    lat2, lon2 = np.radians(point2)
    # Earth radius in meters
    earth_radius = 6371000.0  # Approximately 6371 km

    # Haversine formula to calculate distance
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    a = (
        np.sin(d_lat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(d_lon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return cast(NDArray[np.float_], earth_radius * c)


def calculate_wind_at_given_distance(
    max_wind: float,
    max_wind_radius: float,
    loc: List[NDArray[np.float_]],
    centre: List[NDArray[np.float_]],
) -> NDArray[np.float_]:
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
