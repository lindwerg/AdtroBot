"""
Load testing scenarios for AdtroBot API.

Usage:
    # Web UI mode (interactive):
    poetry run locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Headless mode (CI):
    poetry run locust -f tests/load/locustfile.py --host=http://localhost:8000 \
        --headless -u 10 -r 2 --run-time 1m

SLA Targets:
    - /health: <1s (P0 if violated)
    - Admin API dashboard: <2s
    - Admin API lists: <2s
"""

import os
import random

from locust import HttpUser, between, events, task


class HealthCheckUser(HttpUser):
    """Tests health endpoint stability.

    SLA: /health must respond within 1 second.
    Weight: 5 (most frequent - load balancer probes)
    """

    wait_time = between(0.1, 0.5)
    weight = 5

    @task
    def test_health(self) -> None:
        """Health should always respond quickly (<1s)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code not in (200, 503):
                response.failure(f"Health check failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 1.0:
                response.failure(
                    f"Health too slow: {response.elapsed.total_seconds():.2f}s (SLA: <1s)"
                )
            else:
                response.success()


class AdminAPIUser(HttpUser):
    """Tests admin API under load.

    SLA: All admin endpoints should respond within 2 seconds.
    Weight: 2 (admin panel is less frequent than health checks)

    Requires ADMIN_USERNAME and ADMIN_PASSWORD environment variables.
    """

    wait_time = between(1, 3)
    weight = 2
    token: str | None = None

    def on_start(self) -> None:
        """Login and get auth token."""
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "password")

        response = self.client.post(
            "/admin/api/token",
            data={
                "username": username,
                "password": password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers["Authorization"] = f"Bearer {self.token}"
        else:
            self.token = None

    @task(5)
    def test_dashboard(self) -> None:
        """Dashboard should load in <2s."""
        if not self.token:
            return

        with self.client.get("/admin/api/dashboard", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Dashboard failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 2.0:
                response.failure(
                    f"Dashboard too slow: {response.elapsed.total_seconds():.2f}s (SLA: <2s)"
                )
            else:
                response.success()

    @task(3)
    def test_users_list(self) -> None:
        """Users list pagination (SLA: <2s)."""
        if not self.token:
            return

        page = random.randint(1, 5)
        with self.client.get(
            f"/admin/api/users?page={page}&page_size=20", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Users list failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 2.0:
                response.failure(
                    f"Users list too slow: {response.elapsed.total_seconds():.2f}s"
                )
            else:
                response.success()

    @task(2)
    def test_monitoring(self) -> None:
        """Monitoring API performance (SLA: <2s)."""
        if not self.token:
            return

        ranges = ["24h", "7d", "30d"]
        time_range = random.choice(ranges)

        with self.client.get(
            f"/admin/api/monitoring?range={time_range}", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Monitoring failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 2.0:
                response.failure(
                    f"Monitoring too slow: {response.elapsed.total_seconds():.2f}s"
                )
            else:
                response.success()

    @task(2)
    def test_funnel(self) -> None:
        """Funnel data (SLA: <2s)."""
        if not self.token:
            return

        with self.client.get(
            "/admin/api/funnel?days=30", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Funnel failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 2.0:
                response.failure(
                    f"Funnel too slow: {response.elapsed.total_seconds():.2f}s"
                )
            else:
                response.success()

    @task(1)
    def test_payments_list(self) -> None:
        """Payments list (SLA: <2s)."""
        if not self.token:
            return

        with self.client.get(
            "/admin/api/payments?page=1&page_size=20", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Payments list failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 2.0:
                response.failure(
                    f"Payments too slow: {response.elapsed.total_seconds():.2f}s"
                )
            else:
                response.success()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    print("\n=== AdtroBot Load Test Started ===")
    print(f"Target host: {environment.host}")
    print("SLA Targets:")
    print("  - /health: <1s")
    print("  - Admin API: <2s")
    print("================================\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test summary."""
    stats = environment.stats
    print("\n=== Load Test Summary ===")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Failure rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Median response time: {stats.total.median_response_time}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95)}ms")
    print("=========================\n")
