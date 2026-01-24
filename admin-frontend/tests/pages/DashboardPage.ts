import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Dashboard page.
 * Main admin panel landing page with navigation and metrics.
 */
export class DashboardPage {
  readonly page: Page;
  readonly navigation: Locator;
  readonly userStats: Locator;
  readonly revenueCard: Locator;
  readonly activeUsersCard: Locator;
  readonly messagesLink: Locator;
  readonly paymentsLink: Locator;
  readonly monitoringLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.navigation = page.getByRole('navigation');
    this.userStats = page.locator('[data-testid="user-stats"]').or(page.getByText(/пользовател|users/i).first());
    this.revenueCard = page.locator('[data-testid="revenue-card"]').or(page.getByText(/доход|revenue/i).first());
    this.activeUsersCard = page.locator('[data-testid="active-users"]').or(page.getByText(/активн|active/i).first());
    this.messagesLink = page.getByRole('link', { name: /сообщения|messages/i });
    this.paymentsLink = page.getByRole('link', { name: /платежи|payments/i });
    this.monitoringLink = page.getByRole('link', { name: /мониторинг|monitoring/i });
  }

  /**
   * Navigate to the dashboard.
   */
  async goto() {
    await this.page.goto('/');
  }

  /**
   * Wait for dashboard to fully load.
   */
  async waitForLoad() {
    await expect(this.navigation).toBeVisible();
    // Wait for any loading states to complete
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to messages section.
   */
  async goToMessages() {
    await this.messagesLink.click();
    await expect(this.page).toHaveURL(/messages/);
  }

  /**
   * Navigate to payments section.
   */
  async goToPayments() {
    await this.paymentsLink.click();
    await expect(this.page).toHaveURL(/payments/);
  }

  /**
   * Navigate to monitoring section.
   */
  async goToMonitoring() {
    await this.monitoringLink.click();
    await expect(this.page).toHaveURL(/monitoring/);
  }

  /**
   * Check if dashboard is displaying metrics.
   */
  async hasMetricsLoaded(): Promise<boolean> {
    try {
      // Wait for at least one metric card to have content
      await this.page.waitForFunction(
        () => {
          const cards = document.querySelectorAll('[class*="card"], [class*="stat"]');
          return cards.length > 0;
        },
        { timeout: 5000 }
      );
      return true;
    } catch {
      return false;
    }
  }
}
