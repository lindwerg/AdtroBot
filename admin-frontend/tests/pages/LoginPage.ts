import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Login page.
 * Encapsulates login form interactions and error handling.
 */
export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByPlaceholder(/username|логин/i);
    this.passwordInput = page.getByPlaceholder(/password|пароль/i);
    this.submitButton = page.getByRole('button', { name: /войти|login|sign in/i });
    this.errorMessage = page.getByRole('alert');
  }

  /**
   * Navigate to the login page.
   */
  async goto() {
    await this.page.goto('/login');
    await expect(this.usernameInput).toBeVisible();
  }

  /**
   * Perform login with given credentials.
   * @param username - Admin username
   * @param password - Admin password
   */
  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  /**
   * Login and expect success (redirect to dashboard).
   */
  async loginAndExpectSuccess(username: string, password: string) {
    await this.login(username, password);
    await expect(this.page).toHaveURL(/\/(dashboard)?$/);
  }

  /**
   * Login and expect failure (error message shown).
   */
  async loginAndExpectError(username: string, password: string) {
    await this.login(username, password);
    await expect(this.errorMessage).toBeVisible();
  }

  /**
   * Get the error message text.
   */
  async getErrorText(): Promise<string> {
    return await this.errorMessage.textContent() ?? '';
  }
}
