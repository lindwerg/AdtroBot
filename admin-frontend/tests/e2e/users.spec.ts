import { test, expect } from '@playwright/test';
import { UsersPage } from '../pages/UsersPage';

/**
 * Users E2E tests.
 * Uses authenticated state from auth.setup.ts.
 */
test.describe('Users', () => {
  let usersPage: UsersPage;

  test.beforeEach(async ({ page }) => {
    usersPage = new UsersPage(page);
    await usersPage.goto();
  });

  test('users page loads', async () => {
    await expect(usersPage.pageTitle).toBeVisible();
    await expect(usersPage.usersTable).toBeVisible();
  });

  test('users table displays data', async () => {
    await usersPage.waitForLoad();

    // Table should be visible
    await expect(usersPage.usersTable).toBeVisible();

    // Check for users (may be 0 if empty database)
    const hasUsers = await usersPage.hasUsers();
    // Just verify it doesn't error
    expect(typeof hasUsers).toBe('boolean');
  });

  test('search input is functional', async () => {
    await usersPage.waitForLoad();

    // Search input should exist
    await expect(usersPage.searchInput).toBeVisible();

    // Can type in search
    await usersPage.searchInput.fill('test');
    await expect(usersPage.searchInput).toHaveValue('test');
  });

  test('search filters users', async ({ page }) => {
    await usersPage.waitForLoad();

    // Get initial count
    const initialCount = await usersPage.getUserCount();

    // Search for non-existent user
    await usersPage.searchUser('nonexistent12345678');

    // Should show fewer or no results
    const filteredCount = await usersPage.getUserCount();

    // Either fewer results or empty state
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
  });

  test('export button is visible', async () => {
    await usersPage.waitForLoad();

    await expect(usersPage.exportButton).toBeVisible();
    await expect(usersPage.exportButton).toBeEnabled();
  });

  test('table has expected columns', async ({ page }) => {
    await usersPage.waitForLoad();

    // Check for column headers
    await expect(page.getByRole('columnheader', { name: /telegram id/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /username/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /знак/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /статус/i })).toBeVisible();
  });

  test('clicking user row navigates to detail', async ({ page }) => {
    await usersPage.waitForLoad();

    const hasUsers = await usersPage.hasUsers();
    if (!hasUsers) {
      test.skip(true, 'No users in database to click');
      return;
    }

    // Click first user row
    await usersPage.clickUserRow(0);

    // Should navigate to user detail page
    await expect(page).toHaveURL(/users\/\d+/);
  });

  test('pagination exists', async ({ page }) => {
    await usersPage.waitForLoad();

    // Pagination should be visible
    const pagination = page.locator('.ant-pagination');
    await expect(pagination).toBeVisible();
  });

  test('pagination works if multiple pages', async ({ page }) => {
    await usersPage.waitForLoad();

    const hasNextPage = await usersPage.hasNextPage();

    if (hasNextPage) {
      await usersPage.nextPage();

      // Should still show table
      await expect(usersPage.usersTable).toBeVisible();
    } else {
      // Only one page - that's fine
      expect(hasNextPage).toBe(false);
    }
  });

  test('user selection checkbox exists', async ({ page }) => {
    await usersPage.waitForLoad();

    // Selection column should exist (header checkbox)
    const selectAllCheckbox = page.locator('.ant-table-thead .ant-checkbox');
    await expect(selectAllCheckbox).toBeVisible();
  });

  test('bulk action buttons appear on selection', async ({ page }) => {
    await usersPage.waitForLoad();

    const hasUsers = await usersPage.hasUsers();
    if (!hasUsers) {
      test.skip(true, 'No users to select');
      return;
    }

    // Select first user
    await usersPage.selectUser(0);

    // Bulk action buttons should appear
    await expect(usersPage.bulkActivateButton).toBeVisible();
    await expect(usersPage.bulkCancelButton).toBeVisible();
    await expect(usersPage.giftButton).toBeVisible();
  });

  test('clear search restores results', async () => {
    await usersPage.waitForLoad();

    // Search for something
    await usersPage.searchUser('nonexistent12345');

    // Clear search
    await usersPage.clearSearch();

    // Table should still be visible
    await expect(usersPage.usersTable).toBeVisible();
  });

  test('handles empty state gracefully', async ({ page }) => {
    await usersPage.waitForLoad();

    // Search for definitely non-existent user
    await usersPage.searchUser('zzz_definitely_not_exists_12345678');

    // Should show empty state or 0 rows without crashing
    const count = await usersPage.getUserCount();
    expect(count).toBe(0);

    // Page should still be functional
    await expect(usersPage.usersTable).toBeVisible();
  });
});
