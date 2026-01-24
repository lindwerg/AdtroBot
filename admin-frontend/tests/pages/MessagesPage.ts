import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Messages page.
 * Handles message sending (broadcast/single user) and history viewing.
 */
export class MessagesPage {
  readonly page: Page;
  readonly messageTextarea: Locator;
  readonly sendButton: Locator;
  readonly broadcastSwitch: Locator;
  readonly scheduledSwitch: Locator;
  readonly premiumFilter: Locator;
  readonly zodiacFilter: Locator;
  readonly targetUserIdInput: Locator;
  readonly scheduleDatePicker: Locator;
  readonly historyTable: Locator;
  readonly sendCard: Locator;
  readonly historyCard: Locator;

  constructor(page: Page) {
    this.page = page;
    this.messageTextarea = page.getByPlaceholder(/текст сообщения/i);
    this.sendButton = page.getByRole('button', { name: /отправить|запланировать/i });
    this.broadcastSwitch = page.locator('.ant-switch').filter({ hasText: /рассылка|одному/i }).first();
    this.scheduledSwitch = page.locator('.ant-switch').filter({ hasText: /отложить|сейчас/i }).first();
    this.premiumFilter = page.getByRole('combobox').filter({ hasText: /все|premium|free/i }).first();
    this.zodiacFilter = page.getByText('Знак зодиака').locator('..').locator('.ant-select');
    this.targetUserIdInput = page.getByPlaceholder(/user id/i);
    this.scheduleDatePicker = page.locator('.ant-picker');
    this.historyTable = page.locator('.ant-table');
    this.sendCard = page.locator('.ant-card').filter({ hasText: /отправить сообщение/i });
    this.historyCard = page.locator('.ant-card').filter({ hasText: /история сообщений/i });
  }

  /**
   * Navigate to the messages page.
   */
  async goto() {
    await this.page.goto('/messages');
    await expect(this.sendCard).toBeVisible();
  }

  /**
   * Wait for page to fully load.
   */
  async waitForLoad() {
    await expect(this.sendCard).toBeVisible();
    await expect(this.historyCard).toBeVisible();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Send a broadcast message.
   * @param text - Message text
   */
  async sendBroadcastMessage(text: string) {
    await this.messageTextarea.fill(text);
    await this.sendButton.click();
  }

  /**
   * Send a message to a specific user.
   * @param text - Message text
   * @param userId - Target user ID
   */
  async sendMessageToUser(text: string, userId: number) {
    // Switch to single user mode
    await this.broadcastSwitch.click();
    await expect(this.targetUserIdInput).toBeVisible();

    await this.messageTextarea.fill(text);
    await this.targetUserIdInput.fill(String(userId));
    await this.sendButton.click();
  }

  /**
   * Toggle scheduled mode.
   */
  async toggleScheduled() {
    await this.scheduledSwitch.click();
  }

  /**
   * Get message count from history table.
   */
  async getMessageCount(): Promise<number> {
    const rows = this.historyTable.locator('tbody tr');
    return await rows.count();
  }

  /**
   * Check if success message appears after sending.
   */
  async expectSendSuccess() {
    await expect(this.page.locator('.ant-message-success')).toBeVisible({ timeout: 10000 });
  }

  /**
   * Check if error message appears.
   */
  async expectSendError() {
    await expect(this.page.locator('.ant-message-error')).toBeVisible({ timeout: 10000 });
  }

  /**
   * Get the first message text from history.
   */
  async getFirstMessageText(): Promise<string> {
    const firstCell = this.historyTable.locator('tbody tr').first().locator('td').first();
    return await firstCell.textContent() ?? '';
  }
}
