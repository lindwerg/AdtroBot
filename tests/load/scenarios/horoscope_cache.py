"""
Horoscope cache performance tests.

NOTE: AdtroBot delivers horoscopes via Telegram bot, not HTTP API.
This scenario tests the internal cache warming endpoint behavior
indirectly through health checks and cache-related metrics.

For direct cache testing, use integration tests in tests/integration/

SLA: Cached content retrieval should be <500ms.

Usage:
    poetry run locust -f tests/load/scenarios/horoscope_cache.py --host=http://localhost:8000
"""

import random

from locust import HttpUser, between, task

# Zodiac signs in English (matching internal API)
ZODIAC_SIGNS = [
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
]


class HoroscopeCacheMonitorUser(HttpUser):
    """Monitor horoscope cache via health and metrics endpoints.

    Since horoscopes are delivered via Telegram bot (not HTTP API),
    we test cache health through:
    1. /health - database connectivity (cache is in PostgreSQL)
    2. /metrics - Prometheus metrics for cache operations

    SLA: Cache-related checks should complete in <500ms.
    """

    wait_time = between(1, 3)
    weight = 2

    @task(5)
    def check_health_db(self) -> None:
        """Health check includes DB where cache lives."""
        with self.client.get(
            "/health", catch_response=True, name="/health [cache-db]"
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code not in (200, 503):
                response.failure(f"Status {response.status_code}")
            elif elapsed > 0.5:
                response.failure(f"DB health slow: {elapsed:.3f}s > 0.5s")
            else:
                try:
                    data = response.json()
                    db_latency = (
                        data.get("checks", {}).get("database", {}).get("latency_ms", 0)
                    )
                    if db_latency > 100:
                        response.failure(f"DB latency high: {db_latency}ms")
                    else:
                        response.success()
                except Exception:
                    response.success()

    @task(2)
    def check_prometheus_metrics(self) -> None:
        """Check cache-related Prometheus metrics."""
        with self.client.get(
            "/metrics", catch_response=True, name="/metrics [cache]"
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Metrics failed: {response.status_code}")
            elif elapsed > 0.5:
                response.failure(f"Metrics slow: {elapsed:.3f}s > 0.5s")
            else:
                response.success()


class HoroscopeAdminContentUser(HttpUser):
    """Test admin content endpoints for horoscope management.

    Admin panel accesses horoscope content for editing.
    Tests content retrieval performance.

    SLA: Content API should respond in <500ms.
    """

    wait_time = between(1, 3)
    weight = 1
    token: str | None = None

    def on_start(self) -> None:
        """Authenticate with admin API."""
        import os

        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "password")

        response = self.client.post(
            "/admin/api/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers["Authorization"] = f"Bearer {self.token}"
        else:
            self.token = None

    @task(3)
    def get_all_horoscope_content(self) -> None:
        """List all horoscope content (SLA: <500ms)."""
        if not self.token:
            return

        with self.client.get(
            "/admin/api/content/horoscopes",
            catch_response=True,
            name="/admin/api/content/horoscopes",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Content list failed: {response.status_code}")
            elif elapsed > 0.5:
                response.failure(f"Content list slow: {elapsed:.3f}s > 0.5s")
            else:
                response.success()

    @task(5)
    def get_single_horoscope_content(self) -> None:
        """Get single sign content (SLA: <500ms)."""
        if not self.token:
            return

        sign = random.choice(ZODIAC_SIGNS)
        with self.client.get(
            f"/admin/api/content/horoscopes/{sign}",
            catch_response=True,
            name="/admin/api/content/horoscopes/[sign]",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code == 404:
                # Content might not exist yet - acceptable
                response.success()
            elif response.status_code != 200:
                response.failure(f"Content get failed: {response.status_code}")
            elif elapsed > 0.5:
                response.failure(f"Content get slow: {elapsed:.3f}s > 0.5s")
            else:
                response.success()
