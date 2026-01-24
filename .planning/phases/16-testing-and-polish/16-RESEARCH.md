# Phase 16: Testing & Polish - Research

**Researched:** 2026-01-24
**Domain:** E2E Testing (Playwright, Telethon), Load Testing (Locust), Test Data Generation (Faker)
**Confidence:** HIGH

## Summary

Phase 16 требует два типа E2E тестирования: **Playwright** для React админки и **Telethon** для Telegram бота. Исследование подтвердило, что это стандартный стек для данных задач. Playwright v1.57 — индустриальный стандарт для браузерного тестирования React приложений, Telethon v1.42 — основная библиотека для программного взаимодействия с Telegram API. Для load testing используется Locust v2.43 — де-факто стандарт для Python/FastAPI.

Ключевые решения из CONTEXT.md:
- Real API calls для OpenRouter (не mock)
- Production bot с cleanup тестовых данных
- StringSession для CI-ready тестов
- Faker + SQL seed для test data
- Все баги в BUGS.md, фиксы в следующей фазе

**Primary recommendation:** Использовать Page Object Model для Playwright, pytest fixtures с StringSession для Telethon, Locust для load testing, Faker для генерации тестовых данных.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @playwright/test | ^1.57.0 | Browser E2E testing | Microsoft-backed, best-in-class selectors, trace viewer |
| Telethon | ^1.42.0 | Telegram MTProto client | Official MTProto implementation, StringSession for CI |
| locust | ^2.43.1 | Load testing | Python-native, web UI, FastAPI-proven |
| Faker | ^40.1.2 | Test data generation | Localization, deterministic seeding |
| pytest-asyncio | ^1.3.0 | Async test support | Required for Telethon async tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| factory_boy | ^3.3.0 | Model factories | Database seed с Faker интеграцией |
| pytest-cov | ^5.0.0 | Coverage reports | Метрика покрытия тестами |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Playwright | Cypress | Playwright лучше для multi-browser, trace viewer |
| Telethon | Pyrogram | Telethon более mature, лучше документация |
| Locust | k6 | Locust Python-native, проще интеграция |

**Installation:**

Admin frontend (playwright):
```bash
cd admin-frontend
npm install -D @playwright/test@^1.57.0
npx playwright install
```

Python (telethon, locust, faker):
```bash
poetry add --group dev telethon@^1.42.0 locust@^2.43.1 Faker@^40.1.2 factory_boy@^3.3.0 pytest-cov@^5.0.0
```

## Architecture Patterns

### Recommended Project Structure

```
admin-frontend/
├── playwright.config.ts      # Playwright configuration
├── tests/
│   ├── auth.setup.ts         # Authentication setup
│   ├── pages/                # Page Object Models
│   │   ├── LoginPage.ts
│   │   ├── DashboardPage.ts
│   │   ├── MessagesPage.ts
│   │   ├── MonitoringPage.ts
│   │   └── ...
│   ├── e2e/                  # E2E test specs
│   │   ├── login.spec.ts
│   │   ├── dashboard.spec.ts
│   │   ├── messaging.spec.ts
│   │   ├── monitoring.spec.ts
│   │   └── ...
│   └── fixtures/             # Test fixtures
└── playwright/.auth/         # Auth state (gitignored)

tests/
├── e2e/                      # Telethon E2E tests
│   ├── conftest.py           # Shared fixtures
│   ├── test_start.py         # /start flow
│   ├── test_horoscope.py     # Horoscope flows (12 signs)
│   ├── test_tarot.py         # Tarot spreads
│   ├── test_subscription.py  # Payment flows (mocked webhooks)
│   ├── test_natal.py         # Natal chart flows
│   └── test_profile.py       # Profile settings
├── load/                     # Locust load tests
│   ├── locustfile.py         # Main load test scenarios
│   └── scenarios/
│       ├── api_health.py
│       ├── horoscope_cache.py
│       └── bot_start.py
├── fixtures/                 # Test data factories
│   ├── factories.py          # Faker-based factories
│   └── seed.sql              # Base seed data
└── BUGS.md                   # Bug tracking (created during testing)
```

### Pattern 1: Page Object Model (Playwright)

**What:** Encapsulate page interactions в отдельных классах
**When to use:** Для всех страниц админки
**Example:**
```typescript
// Source: https://playwright.dev/docs/pom
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByLabel('Username');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/admin/login');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}
```

### Pattern 2: Telethon Conversation Pattern

**What:** Использование conversation context для bot interaction
**When to use:** Для всех E2E тестов бота
**Example:**
```python
# Source: https://dev.to/blueset/how-to-write-integration-tests-for-a-telegram-bot-4c0e
import pytest
from telethon import TelegramClient
from telethon.sessions import StringSession

@pytest.fixture(scope="session")
async def client():
    session_str = os.environ["TELETHON_SESSION"]
    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]

    client = TelegramClient(
        StringSession(session_str),
        api_id,
        api_hash,
        sequential_updates=True
    )
    await client.connect()
    await client.get_me()
    yield client
    await client.disconnect()

@pytest.mark.asyncio
async def test_start_command(client: TelegramClient, bot_username: str):
    async with client.conversation(bot_username, timeout=10) as conv:
        await conv.send_message("/start")
        response = await conv.get_response()
        assert "Добро пожаловать" in response.raw_text
```

### Pattern 3: Auth State Reuse (Playwright)

**What:** Сохранение auth state для быстрых тестов
**When to use:** Для всех тестов, требующих авторизации
**Example:**
```typescript
// Source: https://playwright.dev/docs/auth
// auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/admin.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/admin/login');
  await page.getByLabel('Username').fill(process.env.ADMIN_USERNAME!);
  await page.getByLabel('Password').fill(process.env.ADMIN_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL('/admin/dashboard');
  await page.context().storageState({ path: authFile });
});
```

### Pattern 4: Locust Load Test Scenario

**What:** Сценарий нагрузочного тестирования
**When to use:** Для проверки SLA endpoints
**Example:**
```python
# Source: https://www.kdnuggets.com/stress-testing-fastapi-application
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def test_health(self):
        self.client.get("/health")

    @task(1)
    def test_cached_horoscope(self):
        # SLA: <500ms
        with self.client.get("/api/horoscope/aries", catch_response=True) as response:
            if response.elapsed.total_seconds() > 0.5:
                response.failure("Response too slow")
```

### Anti-Patterns to Avoid

- **CSS/XPath selectors:** Используйте `getByRole`, `getByLabel`, `getByTestId` вместо CSS/XPath
- **Shared state между тестами:** Каждый тест должен быть изолирован
- **Hardcoded waits:** Используйте `expect` с auto-waiting вместо `sleep`
- **Mocking в E2E:** CONTEXT.md требует real API calls для OpenRouter
- **Тестирование на test server:** Production bot используется (cleanup обязателен)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test data generation | Custom random functions | Faker | Localization, reproducibility, edge cases |
| Browser automation | Selenium/Puppeteer | Playwright | Auto-wait, trace viewer, better DX |
| Telegram interaction | HTTP Bot API calls | Telethon | MTProto, conversation context, reliability |
| Load testing | Custom concurrent requests | Locust | Statistics, web UI, distributed mode |
| Auth state management | Manual cookie handling | Playwright storageState | Built-in, reliable, cross-test |

**Key insight:** Playwright и Telethon имеют встроенные паттерны для всех типичных сценариев. Любая custom реализация будет хуже.

## Common Pitfalls

### Pitfall 1: Flaky Tests от Race Conditions
**What goes wrong:** Тесты случайно падают из-за timing issues
**Why it happens:** Не используются built-in wait mechanisms
**How to avoid:**
- Playwright: используйте `expect` assertions (auto-wait)
- Telethon: используйте `conversation` context с timeout
**Warning signs:** Тесты проходят локально, падают на CI

### Pitfall 2: StringSession Security Leak
**What goes wrong:** StringSession попадает в git
**Why it happens:** Случайный commit .env файла
**How to avoid:**
- `.env.test` в .gitignore
- Использовать GitHub Secrets для CI
- Создать отдельный Telegram аккаунт для тестов
**Warning signs:** Warning от git pre-commit hooks

### Pitfall 3: Production Data Pollution
**What goes wrong:** Тестовые данные остаются в production DB
**Why it happens:** Отсутствие cleanup в tearDown
**How to avoid:**
- Explicit cleanup после каждого теста
- Уникальные test user identifiers (prefix/suffix)
- Transaction rollback где возможно
**Warning signs:** Рост количества "test_*" записей в DB

### Pitfall 4: Slow Test Suite
**What goes wrong:** Тесты занимают >10 минут
**Why it happens:** Каждый тест делает полный login
**How to avoid:**
- Playwright: storageState reuse
- Telethon: session-scoped client fixture
- Parallel execution где возможно
**Warning signs:** CI pipeline timeout

### Pitfall 5: Antd Form Testing Issues
**What goes wrong:** Не удается найти form elements
**Why it happens:** Antd генерирует сложную DOM структуру
**How to avoid:**
- Использовать `data-testid` на критичных элементах
- `getByRole('textbox')` для inputs
- `getByRole('button', { name: 'Отправить' })` для buttons
**Warning signs:** Locator timeout errors на form pages

### Pitfall 6: Load Test False Positives
**What goes wrong:** Load test показывает хорошие результаты, но production падает
**Why it happens:** Тест не учитывает real-world conditions
**How to avoid:**
- Тестировать с realistic data volumes
- Включать DB операции в тесты
- Использовать production-like infrastructure
**Warning signs:** Latency резко отличается от production metrics

## Code Examples

### Playwright Configuration
```typescript
// playwright.config.ts
// Source: https://playwright.dev/docs/test-configuration
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    // Auth setup project
    { name: 'setup', testMatch: /.*\.setup\.ts/ },

    // Main tests depend on setup
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/admin.json',
      },
      dependencies: ['setup'],
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Dashboard Page Object
```typescript
// tests/pages/DashboardPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly userCountCard: Locator;
  readonly revenueCard: Locator;
  readonly dauChart: Locator;
  readonly refreshButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.userCountCard = page.getByTestId('metric-users');
    this.revenueCard = page.getByTestId('metric-revenue');
    this.dauChart = page.getByTestId('chart-dau');
    this.refreshButton = page.getByRole('button', { name: 'Refresh' });
  }

  async goto() {
    await this.page.goto('/admin/dashboard');
  }

  async waitForCharts() {
    await expect(this.dauChart).toBeVisible();
  }

  async getMetricValue(metric: 'users' | 'revenue'): Promise<string> {
    const card = metric === 'users' ? this.userCountCard : this.revenueCard;
    return await card.locator('.ant-statistic-content-value').textContent() ?? '';
  }
}
```

### Telethon Test with All 12 Zodiac Signs
```python
# tests/e2e/test_horoscope.py
import pytest
from telethon import TelegramClient

ZODIAC_SIGNS = [
    ("aries", "Овен"), ("taurus", "Телец"), ("gemini", "Близнецы"),
    ("cancer", "Рак"), ("leo", "Лев"), ("virgo", "Дева"),
    ("libra", "Весы"), ("scorpio", "Скорпион"), ("sagittarius", "Стрелец"),
    ("capricorn", "Козерог"), ("aquarius", "Водолей"), ("pisces", "Рыбы"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("sign_id,sign_name", ZODIAC_SIGNS)
async def test_daily_horoscope(client: TelegramClient, bot_username: str, sign_id: str, sign_name: str):
    """Test daily horoscope for all 12 zodiac signs."""
    async with client.conversation(bot_username, timeout=30) as conv:
        # Navigate to horoscope menu
        await conv.send_message("/menu")
        menu_response = await conv.get_response()

        # Click horoscope button
        await menu_response.click(text="Гороскоп")
        horoscope_menu = await conv.get_edit()

        # Select zodiac sign
        await horoscope_menu.click(text=sign_name)
        sign_response = await conv.get_edit()

        # Select daily horoscope
        await sign_response.click(text="На сегодня")
        horoscope = await conv.get_edit()

        # Verify horoscope content
        assert sign_name in horoscope.raw_text or sign_id in horoscope.raw_text.lower()
        assert len(horoscope.raw_text) > 100  # Real content, not error
```

### Faker Factory for Test Data
```python
# tests/fixtures/factories.py
import factory
from faker import Faker
from datetime import date
from src.db.models import User

fake = Faker('ru_RU')

class UserFactory(factory.Factory):
    class Meta:
        model = dict

    telegram_id = factory.LazyFunction(lambda: fake.random_int(min=100000000, max=999999999))
    username = factory.LazyFunction(lambda: f"test_{fake.user_name()}")
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    birth_date = factory.LazyFunction(lambda: fake.date_of_birth(minimum_age=18, maximum_age=80))
    zodiac_sign = factory.LazyFunction(lambda: fake.random_element([
        'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
        'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
    ]))
    is_premium = False
    created_at = factory.LazyFunction(fake.date_time_this_year)

# Usage
def test_with_factory():
    user_data = UserFactory()
    # Creates: {'telegram_id': 123456789, 'username': 'test_ivan', ...}
```

### Locust SLA Verification
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import time

class AdminAPIUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        # Login and get token
        response = self.client.post("/admin/api/auth/login", json={
            "username": "admin",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.client.headers = {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def test_dashboard_metrics(self):
        """Dashboard should load in <2s"""
        with self.client.get("/admin/api/analytics/metrics", catch_response=True) as response:
            if response.elapsed.total_seconds() > 2:
                response.failure(f"Dashboard too slow: {response.elapsed.total_seconds()}s")

    @task(3)
    def test_users_list(self):
        """Users list should paginate efficiently"""
        self.client.get("/admin/api/users?page=1&limit=50")

    @task(1)
    def test_health(self):
        """Health check baseline"""
        self.client.get("/health")


class BotAPIUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(10)
    def test_cached_horoscope(self):
        """SLA: Cached horoscope <500ms"""
        with self.client.get("/api/horoscope/aries/daily", catch_response=True) as response:
            if response.elapsed.total_seconds() > 0.5:
                response.failure(f"Cache miss or slow: {response.elapsed.total_seconds()}s")
```

### BUGS.md Template
```markdown
# BUGS.md - Phase 16 Bug Tracking

| ID | Category | Severity | Status | Component | Description | Steps to Reproduce |
|----|----------|----------|--------|-----------|-------------|-------------------|
| B001 | Admin | P1 | Open | Dashboard | Chart не отображается при пустых данных | 1. Login 2. Go to Dashboard 3. No data → blank area |
| B002 | Bot | P2 | Open | Horoscope | Timeout при первом запросе гороскопа | 1. /start 2. Menu → Horoscope → Aries → Today → wait >10s |
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Selenium WebDriver | Playwright | 2023-2024 | Auto-wait, better traces, multi-browser |
| SQLite session files | StringSession | 2020 | CI-ready, env vars, no file management |
| Custom HTTP load tests | Locust | 2022 | Web UI, statistics, distributed |
| JSON fixtures | Faker + Factory Boy | 2021 | Dynamic data, edge cases, localization |

**Deprecated/outdated:**
- `pytest-playwright` (standalone): Используйте `@playwright/test` native
- Телеthon `sync` module: Используйте `async` everywhere с pytest-asyncio
- Manual cookie auth: Используйте Playwright `storageState`

## Open Questions

1. **Test Account Security**
   - What we know: StringSession позволяет CI тестирование без 2FA
   - What's unclear: Как безопасно хранить session для GitHub Actions
   - Recommendation: Использовать GitHub Secrets, создать dedicated test account

2. **Production Bot Cleanup Strategy**
   - What we know: CONTEXT.md требует cleanup после тестов
   - What's unclear: Как идентифицировать тестовые данные среди реальных
   - Recommendation: Prefix `test_` для всех test usernames, cleanup по prefix

3. **Real OpenRouter API Costs**
   - What we know: CONTEXT.md требует real API calls (не mock)
   - What's unclear: Сколько будут стоить E2E тесты при полном покрытии
   - Recommendation: Ограничить parametrized tests (2-3 signs вместо 12 для CI)

## Sources

### Primary (HIGH confidence)
- [Playwright Official Docs](https://playwright.dev/docs/intro) - Setup, POM, Auth, Locators
- [Playwright Trace Viewer](https://playwright.dev/docs/trace-viewer) - Debugging
- [Telethon Documentation](https://docs.telethon.dev/) - StringSession, API
- [Telethon Sessions](https://docs.telethon.dev/en/stable/concepts/sessions.html) - StringSession details

### Secondary (MEDIUM confidence)
- [Integration Testing Telegram Bots](https://dev.to/blueset/how-to-write-integration-tests-for-a-telegram-bot-4c0e) - Conversation pattern
- [pytest-asyncio Concepts](https://pytest-asyncio.readthedocs.io/en/latest/concepts.html) - Async fixtures
- [Locust Documentation](https://docs.locust.io/) - Load testing

### Tertiary (LOW confidence)
- [BrowserStack Best Practices 2026](https://www.browserstack.com/guide/playwright-best-practices) - General recommendations
- [KDnuggets FastAPI Stress Testing](https://www.kdnuggets.com/stress-testing-fastapi-application) - Locust patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified via PyPI, npm, official docs
- Architecture patterns: HIGH - Official documentation examples
- Pitfalls: MEDIUM - Community sources + official docs
- Code examples: HIGH - Adapted from official docs

**Research date:** 2026-01-24
**Valid until:** 2026-02-24 (30 days - stable libraries)
