import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/admin.json';

/**
 * Authentication setup - runs before all tests to create authenticated state.
 * Uses ADMIN_USERNAME and ADMIN_PASSWORD from environment variables.
 */
setup('authenticate', async ({ page }) => {
  const username = process.env.ADMIN_USERNAME;
  const password = process.env.ADMIN_PASSWORD;

  if (!username || !password) {
    throw new Error(
      'ADMIN_USERNAME and ADMIN_PASSWORD environment variables must be set. ' +
      'Create a .env.test file or export them in your shell.'
    );
  }

  // Navigate to login page
  await page.goto('/login');

  // ProFormText renders as input with name attribute
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[name="password"]').fill(password);

  // Submit login form
  await page.getByRole('button', { name: /войти|login|sign in/i }).click();

  // Wait for successful login - should redirect to dashboard
  await expect(page).toHaveURL(/\/(dashboard)?$/);

  // Verify we're logged in by checking for dashboard elements
  await expect(page.getByRole('navigation')).toBeVisible();

  // Save authentication state
  await page.context().storageState({ path: authFile });
});
