import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

/**
 * Login flow E2E tests.
 * These tests do NOT use storageState - they test the login itself.
 */
test.describe('Login', () => {
  test.use({ storageState: { cookies: [], origins: [] } }); // No auth state

  test('successful login redirects to dashboard', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const username = process.env.ADMIN_USERNAME;
    const password = process.env.ADMIN_PASSWORD;

    if (!username || !password) {
      test.skip(true, 'ADMIN_USERNAME and ADMIN_PASSWORD not set');
      return;
    }

    await loginPage.goto();
    await loginPage.loginAndExpectSuccess(username, password);
  });

  test('invalid credentials shows error', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.loginAndExpectError('wronguser', 'wrongpassword');

    const errorText = await loginPage.getErrorText();
    expect(errorText).toBeTruthy();
  });

  test('empty fields shows validation error', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.submitButton.click();

    // Should stay on login page
    await expect(page).toHaveURL(/login/);

    // Form validation should prevent submission (button may be disabled or form shows error)
    // Antd Form will show validation messages
    const validationMessage = page.locator('.ant-form-item-explain-error');
    await expect(validationMessage).toBeVisible();
  });

  test('login page is accessible', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();

    // Check basic accessibility
    await expect(loginPage.usernameInput).toBeFocused().or(expect(loginPage.usernameInput).toBeVisible());
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.submitButton).toBeEnabled();

    // Form should be visible
    await expect(page.locator('form')).toBeVisible();
  });

  test('password field is masked', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();

    // Password input should have type="password"
    const passwordType = await loginPage.passwordInput.getAttribute('type');
    expect(passwordType).toBe('password');
  });
});
