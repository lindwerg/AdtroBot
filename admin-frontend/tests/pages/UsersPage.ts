import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Users page.
 * Displays user list with filtering, search, and bulk actions.
 */
export class UsersPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly searchInput: Locator;
  readonly usersTable: Locator;
  readonly premiumFilter: Locator;
  readonly zodiacFilter: Locator;
  readonly exportButton: Locator;
  readonly bulkActivateButton: Locator;
  readonly bulkCancelButton: Locator;
  readonly giftButton: Locator;
  readonly paginationNext: Locator;
  readonly paginationPrev: Locator;
  readonly rowCheckbox: Locator;

  constructor(page: Page) {
    this.page = page;
    this.pageTitle = page.getByText('Пользователи');
    this.searchInput = page.getByPlaceholder(/telegram id|username/i);
    this.usersTable = page.locator('.ant-pro-table');
    this.premiumFilter = page.locator('.ant-pro-table-list-toolbar').getByText(/статус/i).locator('..').locator('.ant-select');
    this.zodiacFilter = page.locator('.ant-pro-table-list-toolbar').getByText(/знак/i).locator('..').locator('.ant-select');
    this.exportButton = page.getByRole('button', { name: /экспорт/i });
    this.bulkActivateButton = page.getByRole('button', { name: /активировать premium/i });
    this.bulkCancelButton = page.getByRole('button', { name: /отменить premium/i });
    this.giftButton = page.getByRole('button', { name: /подарить расклады/i });
    this.paginationNext = page.locator('.ant-pagination-next');
    this.paginationPrev = page.locator('.ant-pagination-prev');
    this.rowCheckbox = page.locator('.ant-table-selection-column .ant-checkbox');
  }

  /**
   * Navigate to the users page.
   */
  async goto() {
    await this.page.goto('/users');
    await this.waitForLoad();
  }

  /**
   * Wait for page to fully load with data.
   */
  async waitForLoad() {
    await expect(this.pageTitle).toBeVisible();
    await this.page.waitForLoadState('networkidle');
    // Wait for table to be visible
    await expect(this.usersTable).toBeVisible();
  }

  /**
   * Search for a user by query.
   * @param query - Search query (telegram_id or username)
   */
  async searchUser(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Clear search.
   */
  async clearSearch() {
    await this.searchInput.clear();
    await this.page.keyboard.press('Enter');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Filter by premium status using the light filter.
   * @param status - 'premium' | 'free' | 'all'
   */
  async filterPremium(status: 'premium' | 'free' | 'all') {
    const filterButton = this.page.locator('.ant-pro-table-list-toolbar-setting-item').getByText(/статус/i);
    await filterButton.click();

    if (status === 'all') {
      await this.page.getByText('Все').click();
    } else if (status === 'premium') {
      await this.page.getByRole('option', { name: 'Premium' }).click();
    } else {
      await this.page.getByRole('option', { name: 'Free' }).click();
    }

    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get the number of users displayed in the table.
   */
  async getUserCount(): Promise<number> {
    const rows = this.usersTable.locator('.ant-table-tbody tr[data-row-key]');
    return await rows.count();
  }

  /**
   * Click on a user row to navigate to details.
   * @param index - Row index (0-based)
   */
  async clickUserRow(index: number) {
    const rows = this.usersTable.locator('.ant-table-tbody tr[data-row-key]');
    await rows.nth(index).click();
  }

  /**
   * Select a user by checkbox.
   * @param index - Row index (0-based)
   */
  async selectUser(index: number) {
    const checkboxes = this.usersTable.locator('.ant-table-tbody .ant-checkbox-input');
    await checkboxes.nth(index).click();
  }

  /**
   * Go to next page.
   */
  async nextPage() {
    await this.paginationNext.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Check if next page button is enabled.
   */
  async hasNextPage(): Promise<boolean> {
    const isDisabled = await this.paginationNext.getAttribute('aria-disabled');
    return isDisabled !== 'true';
  }

  /**
   * Export users to CSV.
   */
  async exportCSV() {
    await this.exportButton.click();
  }

  /**
   * Get text from a specific column in the first row.
   * @param columnIndex - Column index (0-based)
   */
  async getFirstRowColumn(columnIndex: number): Promise<string> {
    const cell = this.usersTable.locator('.ant-table-tbody tr[data-row-key]').first().locator('td').nth(columnIndex);
    return await cell.textContent() ?? '';
  }

  /**
   * Check if user table has data.
   */
  async hasUsers(): Promise<boolean> {
    const count = await this.getUserCount();
    return count > 0;
  }
}
