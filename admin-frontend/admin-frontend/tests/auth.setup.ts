import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/admin.json';

setup('authenticate', async ({ page }) => {
  const username = process.env.ADMIN_USERNAME;
  const password = process.env.ADMIN_PASSWORD;

  if (!username || !password) {
    throw new Error(
      'ADMIN_USERNAME and ADMIN_PASSWORD environment variables must be set. ' +
      'Create a .env.test file or export them in your shell.'
    );
  }

  await page.goto('/login');

  // ProFormText renders as input with name attribute
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[name="password"]').fill(password);

  await page.getByRole('button', { name: /войти|login|sign in|вход/i }).click();

  await expect(page).toHaveURL(/\/(dashboard)?$/);
  await expect(page.getByRole('navigation')).toBeVisible();

  await page.context().storageState({ path: authFile });
});
