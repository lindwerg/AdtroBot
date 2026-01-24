import { test, expect } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';

/**
 * Dashboard E2E tests.
 * Uses authenticated state from auth.setup.ts.
 */
test.describe('Dashboard', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
  });

  test('dashboard loads with navigation', async ({ page }) => {
    await dashboardPage.waitForLoad();

    // Navigation should be visible
    await expect(dashboardPage.navigation).toBeVisible();
  });

  test('dashboard displays metrics cards', async ({ page }) => {
    await dashboardPage.waitForLoad();

    // Check for KPI cards (should have at least some cards)
    const metricsLoaded = await dashboardPage.hasMetricsLoaded();
    expect(metricsLoaded).toBeTruthy();

    // Check for Dashboard title
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('dashboard has growth section', async ({ page }) => {
    await dashboardPage.waitForLoad();

    // Check for "Рост и активность" section
    await expect(page.getByText('Рост и активность')).toBeVisible();
  });

  test('dashboard has revenue section', async ({ page }) => {
    await dashboardPage.waitForLoad();

    // Check for "Доход" section
    await expect(page.getByText('Доход')).toBeVisible();
  });

  test('dashboard has funnel with period selector', async ({ page }) => {
    await dashboardPage.waitForLoad();

    // Check for period selector
    await expect(page.getByText('Период:')).toBeVisible();
    await expect(page.getByText('7 дней')).toBeVisible();
    await expect(page.getByText('30 дней')).toBeVisible();
    await expect(page.getByText('90 дней')).toBeVisible();
  });

  test('navigation to messages works', async ({ page }) => {
    await dashboardPage.waitForLoad();
    await dashboardPage.goToMessages();

    await expect(page).toHaveURL(/messages/);
  });

  test('navigation to payments works', async ({ page }) => {
    await dashboardPage.waitForLoad();
    await dashboardPage.goToPayments();

    await expect(page).toHaveURL(/payments/);
  });

  test('navigation to monitoring works', async ({ page }) => {
    await dashboardPage.waitForLoad();
    await dashboardPage.goToMonitoring();

    await expect(page).toHaveURL(/monitoring/);
  });

  test('export metrics button is visible', async ({ page }) => {
    await dashboardPage.waitForLoad();

    const exportButton = page.getByRole('button', { name: /экспорт метрик/i });
    await expect(exportButton).toBeVisible();
  });

  test('dashboard handles loading state', async ({ page }) => {
    // Go to dashboard and check that loading eventually resolves
    await page.goto('/');

    // Should not stay in loading state forever
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Should have content
    await expect(page.locator('body')).not.toBeEmpty();
  });
});
