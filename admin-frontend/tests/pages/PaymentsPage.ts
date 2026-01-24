import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Payments page.
 * Displays payment history with filtering and export.
 */
export class PaymentsPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly paymentsTable: Locator;
  readonly statusFilter: Locator;
  readonly userSearchInput: Locator;
  readonly exportButton: Locator;
  readonly totalStatCard: Locator;
  readonly paginationNext: Locator;
  readonly paginationPrev: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.getByText('Платежи').first();
    this.paymentsTable = page.locator('.ant-pro-table');
    this.statusFilter = page.locator('.ant-pro-table-list-toolbar').getByText(/статус/i).locator('..').locator('.ant-select');
    this.userSearchInput = page.getByPlaceholder(/пользователь/i);
    this.exportButton = page.getByRole('button', { name: /экспорт/i });
    this.totalStatCard = page.locator('.ant-statistic').filter({ hasText: /успешные платежи/i });
    this.paginationNext = page.locator('.ant-pagination-next');
    this.paginationPrev = page.locator('.ant-pagination-prev');
  }

  /**
   * Navigate to the payments page.
   */
  async goto() {
    await this.page.goto('/payments');
    await this.waitForLoad();
  }

  /**
   * Wait for page to fully load with data.
   */
  async waitForLoad() {
    await expect(this.pageTitle).toBeVisible();
    await this.page.waitForLoadState('networkidle');
    await expect(this.paymentsTable).toBeVisible();
  }

  /**
   * Filter payments by status.
   * @param status - 'pending' | 'succeeded' | 'canceled' | 'all'
   */
  async filterByStatus(status: 'pending' | 'succeeded' | 'canceled' | 'all') {
    const filterButton = this.page.locator('.ant-pro-table-list-toolbar-setting-item').getByText(/статус/i);
    await filterButton.click();

    const labels: Record<string, string> = {
      pending: 'Ожидает',
      succeeded: 'Успешно',
      canceled: 'Отменен',
      all: 'Все',
    };

    await this.page.getByRole('option', { name: labels[status] }).click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Search by user.
   * @param query - User telegram ID or username
   */
  async searchUser(query: string) {
    await this.userSearchInput.fill(query);
    await this.page.keyboard.press('Enter');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get the number of payments displayed in the table.
   */
  async getPaymentCount(): Promise<number> {
    const rows = this.paymentsTable.locator('.ant-table-tbody tr[data-row-key]');
    return await rows.count();
  }

  /**
   * Get total successful payments amount from stat card.
   */
  async getTotalAmount(): Promise<string> {
    const value = this.totalStatCard.locator('.ant-statistic-content-value');
    return await value.textContent() ?? '0';
  }

  /**
   * Export payments to CSV.
   */
  async exportCSV() {
    await this.exportButton.click();
  }

  /**
   * Go to next page.
   */
  async nextPage() {
    await this.paginationNext.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Check if payments exist.
   */
  async hasPayments(): Promise<boolean> {
    const count = await this.getPaymentCount();
    return count > 0;
  }

  /**
   * Get status of first payment row.
   */
  async getFirstPaymentStatus(): Promise<string> {
    const statusTag = this.paymentsTable.locator('.ant-table-tbody tr[data-row-key]').first().locator('.ant-tag');
    return await statusTag.textContent() ?? '';
  }

  /**
   * Check if table shows empty state.
   */
  async isEmpty(): Promise<boolean> {
    const emptyText = this.page.locator('.ant-empty');
    return await emptyText.isVisible();
  }
}
