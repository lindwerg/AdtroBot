"""City geocoding service using GeoNames."""

import asyncio
from dataclasses import dataclass

import structlog
from geopy.geocoders import GeoNames
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from src.config import settings

logger = structlog.get_logger()


@dataclass
class CityResult:
    """Geocoding result for a city."""

    name: str  # Full name with country (e.g., "Moscow, Russia")
    latitude: float
    longitude: float
    timezone: str  # IANA timezone (e.g., "Europe/Moscow")


class GeocodingService:
    """Service for geocoding birth cities."""

    def __init__(self, username: str | None = None):
        self.geolocator = GeoNames(
            username=username or settings.geonames_username,
            timeout=10,
        )

    async def search_city(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[CityResult]:
        """Search for cities matching query.

        Args:
            query: City name to search
            max_results: Maximum results to return

        Returns:
            List of CityResult with coordinates and timezone
        """
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.geolocator.geocode(
                    query,
                    exactly_one=False,
                    timeout=10,
                ),
            )

            if not results:
                return []

            cities = []
            for loc in results[:max_results]:
                # Extract timezone from raw GeoNames response
                tz = loc.raw.get("timezone", {})
                timezone_id = tz.get("timezoneId", "UTC") if isinstance(tz, dict) else "UTC"

                cities.append(
                    CityResult(
                        name=loc.address,
                        latitude=loc.latitude,
                        longitude=loc.longitude,
                        timezone=timezone_id,
                    )
                )

            logger.debug("geocoding_search", query=query, results=len(cities))
            return cities

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error("geocoding_failed", error=str(e), query=query)
            return []
        except Exception as e:
            logger.error("geocoding_unexpected_error", error=str(e), query=query)
            return []


# Singleton instance
_geocoding_service: GeocodingService | None = None


def get_geocoding_service() -> GeocodingService:
    """Get geocoding service singleton."""
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service


async def search_city(query: str, max_results: int = 5) -> list[CityResult]:
    """Convenience function for city search."""
    service = get_geocoding_service()
    return await service.search_city(query, max_results)
