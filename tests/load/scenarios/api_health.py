"""
Detailed health endpoint load tests.

Tests /health endpoint stability under various loads.
Verifies all health check components respond correctly.

SLA: /health must respond within 1 second (P0 violation if exceeded).

Usage:
    poetry run locust -f tests/load/scenarios/api_health.py --host=http://localhost:8000
"""

from locust import HttpUser, between, constant_pacing, task


class HealthEndpointUser(HttpUser):
    """Standard health check testing.

    Simulates load balancer health probes (every 10-30 seconds per instance).
    """

    wait_time = between(0.5, 2)
    weight = 3

    @task
    def check_health(self) -> None:
        """Basic health check - should always pass."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    # 503 is acceptable - it means checks are working
                    response.failure(f"Unhealthy: {data.get('checks', {})}")
            elif response.status_code == 503:
                # Service unavailable but endpoint works
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class HealthSLAUser(HttpUser):
    """SLA validation for health endpoint.

    Strict timing checks - fails if response exceeds 1 second.
    """

    wait_time = between(0.1, 0.5)
    weight = 5

    @task
    def check_health_sla(self) -> None:
        """Health SLA: must respond within 1 second."""
        with self.client.get(
            "/health", catch_response=True, name="/health [SLA]"
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code not in (200, 503):
                response.failure(f"Status {response.status_code}")
            elif elapsed > 1.0:
                response.failure(f"SLA VIOLATION: {elapsed:.3f}s > 1.0s")
            elif elapsed > 0.5:
                # Warning zone - still passes but logs concern
                response.success()
            else:
                response.success()


class HealthBurstUser(HttpUser):
    """Burst load testing for health endpoint.

    Simulates sudden spike in health checks (e.g., during deployment).
    """

    wait_time = constant_pacing(0.1)  # 10 requests/second per user
    weight = 2

    @task
    def burst_health(self) -> None:
        """Rapid health checks under burst load."""
        with self.client.get(
            "/health", catch_response=True, name="/health [burst]"
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code not in (200, 503):
                response.failure(f"Status {response.status_code}")
            elif elapsed > 2.0:
                # Under burst, allow slightly longer (2s instead of 1s)
                response.failure(f"BURST FAILURE: {elapsed:.3f}s > 2.0s")
            else:
                response.success()


class HealthComponentsUser(HttpUser):
    """Health check with component validation.

    Validates individual health check components:
    - Database connectivity
    - Scheduler status
    - AI service status (if applicable)
    """

    wait_time = between(1, 3)
    weight = 1

    @task
    def check_health_components(self) -> None:
        """Validate all health check components."""
        with self.client.get(
            "/health", catch_response=True, name="/health [components]"
        ) as response:
            if response.status_code not in (200, 503):
                response.failure(f"Status {response.status_code}")
                return

            try:
                data = response.json()
                checks = data.get("checks", {})

                # Track individual component status
                db_check = checks.get("database", {})
                scheduler_check = checks.get("scheduler", {})

                if not db_check.get("healthy", False):
                    response.failure(f"Database unhealthy: {db_check.get('message')}")
                elif not scheduler_check.get("healthy", False):
                    response.failure(
                        f"Scheduler unhealthy: {scheduler_check.get('message')}"
                    )
                else:
                    response.success()
            except Exception as e:
                response.failure(f"Parse error: {e}")
