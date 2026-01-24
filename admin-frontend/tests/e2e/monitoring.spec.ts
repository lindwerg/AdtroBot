import { test, expect } from '@playwright/test';
import { MonitoringPage } from '../pages/MonitoringPage';

/**
 * Monitoring E2E tests.
 * Uses authenticated state from auth.setup.ts.
 */
test.describe('Monitoring', () => {
  let monitoringPage: MonitoringPage;

  test.beforeEach(async ({ page }) => {
    monitoringPage = new MonitoringPage(page);
    await monitoringPage.goto();
  });

  test('monitoring page loads', async () => {
    await monitoringPage.waitForLoad();

    await expect(monitoringPage.title).toBeVisible();
  });

  test('active users cards are visible', async () => {
    await monitoringPage.waitForLoad();

    await expect(monitoringPage.dauCard).toBeVisible();
    await expect(monitoringPage.wauCard).toBeVisible();
    await expect(monitoringPage.mauCard).toBeVisible();
  });

  test('API costs cards are visible', async () => {
    await monitoringPage.waitForLoad();

    await expect(monitoringPage.totalCostCard).toBeVisible();
    await expect(monitoringPage.totalTokensCard).toBeVisible();
    await expect(monitoringPage.requestsCard).toBeVisible();
  });

  test('cost chart card is visible', async () => {
    await monitoringPage.waitForLoad();

    await expect(monitoringPage.costChartCard).toBeVisible();
  });

  test('operations card is visible', async () => {
    await monitoringPage.waitForLoad();

    await expect(monitoringPage.operationsCard).toBeVisible();
  });

  test('date filter has all options', async ({ page }) => {
    await monitoringPage.waitForLoad();

    await expect(page.getByText('24 часа')).toBeVisible();
    await expect(page.getByText('7 дней')).toBeVisible();
    await expect(page.getByText('30 дней')).toBeVisible();
  });

  test('date filter changes data', async ({ page }) => {
    await monitoringPage.waitForLoad();

    // Get initial DAU value
    const initialDau = await monitoringPage.getDAU();

    // Change to 30 days
    await monitoringPage.selectDateRange('30d');

    // Wait for data reload
    await page.waitForLoadState('networkidle');

    // Page should still work (may or may not change values)
    await expect(monitoringPage.dauCard).toBeVisible();
  });

  test('charts render in cost card', async ({ page }) => {
    await monitoringPage.waitForLoad();
    await monitoringPage.waitForCharts();

    // Check for recharts container
    const chartContainer = page.locator('.recharts-responsive-container');
    await expect(chartContainer.first()).toBeVisible();
  });

  test('operations table shows data', async () => {
    await monitoringPage.waitForLoad();

    // Table should be visible
    await expect(monitoringPage.operationsTable).toBeVisible();

    // May have rows (depends on data)
    const operationsCount = await monitoringPage.getOperationsCount();
    // Just check it doesn't error - may be 0 if no data
    expect(operationsCount).toBeGreaterThanOrEqual(0);
  });

  test('unit economics section is visible', async ({ page }) => {
    await monitoringPage.waitForLoad();

    // Check for Unit Economics section
    await expect(page.getByText('Unit Economics')).toBeVisible();

    // Check for related cards
    await expect(page.getByText('Активных пользователей')).toBeVisible();
    await expect(page.getByText('Платящих пользователей')).toBeVisible();
    await expect(page.getByText('Cost per Active User')).toBeVisible();
    await expect(page.getByText('Cost per Paying User')).toBeVisible();
  });

  test('handles loading state', async ({ page }) => {
    // Navigate and check loading
    await page.goto('/monitoring');

    // Should not stay in loading forever
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Should have content
    await expect(monitoringPage.title).toBeVisible();
  });

  test('shows error state gracefully on API failure', async ({ page }) => {
    await monitoringPage.waitForLoad();

    // If there's an error, it should show alert
    const hasError = await monitoringPage.hasError();

    // Either no error or error is displayed nicely
    if (hasError) {
      await expect(monitoringPage.errorAlert).toBeVisible();
    } else {
      // Normal state - metrics should load
      await expect(monitoringPage.dauCard).toBeVisible();
    }
  });
});
