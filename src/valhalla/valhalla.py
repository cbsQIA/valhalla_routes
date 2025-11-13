from typing import Literal
import httpx
from shapely.geometry import Point, Polygon

from valhalla.entities import Trip, Coordinate
from valhalla.settings import Settings
from logging import getLogger

settings = Settings()
logger = getLogger(__name__)
async def filter_by_location_polygon(
    center_coords: Coordinate,
    minutes: int,
    coords_to_check: list[Coordinate],
    costing: Literal['auto', 'pedestrian', 'bicycle'] = 'auto'
) -> list[Coordinate]:
    payload = {
        "locations": [{"lat": center_coords.lat, "lon": center_coords.lng}],
        "costing": costing,
        "contours": [{"time": minutes}],
        "polygons": True,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.valhalla_url}/isochrone", json=payload, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Primer polígono de la isócrona
            polygon_coords = data["features"][0]["geometry"]["coordinates"][0]
            # polygon_coords es lista de [lon, lat]
            polygon = Polygon(polygon_coords)
    except Exception as e:
        logger.error(f"Valhalla error (isochrone): {e}")
        return []

    # OJO: Point(lng, lat)
    reachable = []
    for coord in coords_to_check:
        point = Point(coord.lng, coord.lat)
        if polygon.contains(point) or polygon.touches(point):
            reachable.append(coord)

    return reachable


def _to_valhalla_coords(locs: list[Coordinate]) -> list[dict]:
    """
    Convert a list of coordinates to a list of dicts as expected by Valhalla API.

    Args:
        locs (listist[Coordinate]): List of coordinates to convert.

    Returns:
        list[dict]: List of dicts with "lat" and "lon" keys.
    """
    return [{"lat": loc.lat, "lon": loc.lng} for loc in locs]


async def _post_valhalla(path: str, payload: dict, timeout: int = 15) -> dict:
    """
    Post payload to Valhalla API at given path.

    Args:
        path (str): Relative path on Valhalla API to post to.
        payload (dict): Payload to send.
        timeout (int, optional): Timeout in seconds. Defaults to 15.

    Raises:
        httpx.HTTPStatusError: If response status code is not 200.

    Returns:
        dict: JSON response from Valhalla.
    """
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{settings.valhalla_url}{path}", json=payload, timeout=timeout
        )
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = e.response.text
            logger.error(
                "Valhalla %s %s -> %s | body=%s",
                e.request.method,
                e.request.url,
                e.response.status_code,
                body,
            )
            raise
        return res.json()


async def get_optimal_route(locations: list[Coordinate],costing: Literal['auto', 'pedestrian', 'bicycle'] = 'auto' ) -> Trip | None:
    """
    Get the optimal route between the given locations using Valhalla.

    The function first tries to get the optimal route using the /optimized_route endpoint.
    If that fails, it tries the simpler /route endpoint as a fallback.

    Args:
        locations (list[Coordinate]): List of coordinates for which to compute the route.

    Returns:
        Trip | None: The computed route as a Trip object, or None if both attempts failed.

    Notes:
        optimized_route will fail if the location exceed 400000 meters
    """
    coords = _to_valhalla_coords(locations)
    base_payload = {
        "locations": coords,
        "costing": costing,
        "units": "kilometers",
    }

    try:
        data = await _post_valhalla("/optimized_route", base_payload)
        trip_data = data.get("trip")
        if not trip_data:
            raise ValueError("No 'trip' in optimized_route response")
        return Trip(**trip_data)
    except httpx.HTTPStatusError as e:
        if e.response is None or e.response.status_code not in (400, 422, 409):
            logger.warning(
                "optimized_route failed with status %s; trying /route",
                getattr(e.response, "status_code", "unknown"),
            )
    except Exception as e:
        logger.warning("optimized_route failed; trying with /route", e)

    try:
        data = await _post_valhalla("/route", base_payload)
        trip_data = data.get("trip")
        if not trip_data:
            return None
        return Trip(**trip_data)
    except Exception as e:
        logger.error("Fallback /route failed: %s", e)
        return None
