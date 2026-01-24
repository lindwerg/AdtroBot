"""
Load tests for AdtroBot using Locust.

Modules:
- locustfile.py: Main load test configuration with HealthCheckUser and AdminAPIUser
- scenarios/: Detailed scenario files for specific API areas

Usage:
    # Web UI mode (localhost:8089):
    poetry run locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Headless mode (CI/automated):
    poetry run locust -f tests/load/locustfile.py --host=http://localhost:8000 \\
        --headless -u 10 -r 2 --run-time 1m

Environment variables:
    ADMIN_USERNAME: Admin username for API auth (default: admin)
    ADMIN_PASSWORD: Admin password for API auth (default: password)

SLA Targets:
    - /health: <1s (P0 if violated)
    - Admin API endpoints: <2s
"""
