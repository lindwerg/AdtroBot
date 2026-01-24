"""
Admin API endpoint load tests.

Tests all admin API endpoints under load with authentication.

SLA Targets:
- Dashboard: <2s
- Lists (users, payments, subscriptions): <2s
- Monitoring: <2s
- Export endpoints: <5s (large data)

Usage:
    ADMIN_USERNAME=admin ADMIN_PASSWORD=password \\
    poetry run locust -f tests/load/scenarios/admin_api.py --host=http://localhost:8000
"""

import os
import random

from locust import HttpUser, between, task


class AdminDashboardUser(HttpUser):
    """Tests admin dashboard and analytics endpoints.

    Focus on high-frequency admin operations:
    - Dashboard KPIs
    - Funnel analytics
    - Monitoring data
    """

    wait_time = between(1, 3)
    weight = 3
    token: str | None = None

    def on_start(self) -> None:
        """Login and get auth token."""
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

    def _check_auth(self) -> bool:
        """Check if authenticated."""
        if not self.token:
            return False
        return True

    @task(10)
    def test_dashboard(self) -> None:
        """Dashboard KPIs (SLA: <2s)."""
        if not self._check_auth():
            return

        with self.client.get(
            "/admin/api/dashboard", catch_response=True, name="/admin/api/dashboard"
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Dashboard failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Dashboard slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()

    @task(5)
    def test_funnel(self) -> None:
        """Funnel analytics (SLA: <2s)."""
        if not self._check_auth():
            return

        days = random.choice([7, 30, 90])
        with self.client.get(
            f"/admin/api/funnel?days={days}",
            catch_response=True,
            name="/admin/api/funnel",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Funnel failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Funnel slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()

    @task(5)
    def test_monitoring(self) -> None:
        """Monitoring data (SLA: <2s)."""
        if not self._check_auth():
            return

        time_range = random.choice(["24h", "7d", "30d"])
        with self.client.get(
            f"/admin/api/monitoring?range={time_range}",
            catch_response=True,
            name="/admin/api/monitoring",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Monitoring failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Monitoring slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()


class AdminListsUser(HttpUser):
    """Tests admin list/pagination endpoints.

    Tests endpoints that return paginated lists:
    - Users
    - Payments
    - Subscriptions
    - Promo codes
    - Experiments
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
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers["Authorization"] = f"Bearer {self.token}"
        else:
            self.token = None

    def _check_auth(self) -> bool:
        if not self.token:
            return False
        return True

    @task(5)
    def test_users_list(self) -> None:
        """Users list (SLA: <2s)."""
        if not self._check_auth():
            return

        page = random.randint(1, 3)
        page_size = random.choice([20, 50])

        with self.client.get(
            f"/admin/api/users?page={page}&page_size={page_size}",
            catch_response=True,
            name="/admin/api/users",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Users list failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Users list slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()

    @task(3)
    def test_payments_list(self) -> None:
        """Payments list (SLA: <2s)."""
        if not self._check_auth():
            return

        with self.client.get(
            "/admin/api/payments?page=1&page_size=20",
            catch_response=True,
            name="/admin/api/payments",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Payments list failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Payments list slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()

    @task(3)
    def test_subscriptions_list(self) -> None:
        """Subscriptions list (SLA: <2s)."""
        if not self._check_auth():
            return

        with self.client.get(
            "/admin/api/subscriptions?page=1&page_size=20",
            catch_response=True,
            name="/admin/api/subscriptions",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Subscriptions list failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Subscriptions list slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()

    @task(2)
    def test_promo_codes_list(self) -> None:
        """Promo codes list (SLA: <2s)."""
        if not self._check_auth():
            return

        with self.client.get(
            "/admin/api/promo-codes?page=1&page_size=20",
            catch_response=True,
            name="/admin/api/promo-codes",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Promo codes list failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Promo codes list slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()

    @task(2)
    def test_experiments_list(self) -> None:
        """Experiments list (SLA: <2s)."""
        if not self._check_auth():
            return

        with self.client.get(
            "/admin/api/experiments?page=1&page_size=20",
            catch_response=True,
            name="/admin/api/experiments",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Experiments list failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Experiments list slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()

    @task(1)
    def test_tarot_spreads_list(self) -> None:
        """Tarot spreads list (SLA: <2s)."""
        if not self._check_auth():
            return

        with self.client.get(
            "/admin/api/tarot-spreads?page=1&page_size=20",
            catch_response=True,
            name="/admin/api/tarot-spreads",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Tarot spreads list failed: {response.status_code}")
            elif elapsed > 2.0:
                response.failure(f"Tarot spreads list slow: {elapsed:.3f}s > 2.0s")
            else:
                response.success()


class AdminExportUser(HttpUser):
    """Tests admin export endpoints.

    Export endpoints may be slower due to data aggregation.
    SLA: <5s for export operations.
    """

    wait_time = between(5, 15)  # Less frequent
    weight = 1
    token: str | None = None

    def on_start(self) -> None:
        """Login and get auth token."""
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

    def _check_auth(self) -> bool:
        if not self.token:
            return False
        return True

    @task(1)
    def test_export_users(self) -> None:
        """Export users CSV (SLA: <5s)."""
        if not self._check_auth():
            return

        with self.client.get(
            "/admin/api/export/users",
            catch_response=True,
            name="/admin/api/export/users",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Export users failed: {response.status_code}")
            elif elapsed > 5.0:
                response.failure(f"Export users slow: {elapsed:.3f}s > 5.0s")
            else:
                response.success()

    @task(1)
    def test_export_metrics(self) -> None:
        """Export metrics CSV (SLA: <5s)."""
        if not self._check_auth():
            return

        days = random.choice([7, 30])
        with self.client.get(
            f"/admin/api/export/metrics?days={days}",
            catch_response=True,
            name="/admin/api/export/metrics",
        ) as response:
            elapsed = response.elapsed.total_seconds()

            if response.status_code != 200:
                response.failure(f"Export metrics failed: {response.status_code}")
            elif elapsed > 5.0:
                response.failure(f"Export metrics slow: {elapsed:.3f}s > 5.0s")
            else:
                response.success()
