import { test, expect } from '@playwright/test';
import { MessagesPage } from '../pages/MessagesPage';

/**
 * Messaging E2E tests.
 * Uses authenticated state from auth.setup.ts.
 */
test.describe('Messaging', () => {
  let messagesPage: MessagesPage;

  test.beforeEach(async ({ page }) => {
    messagesPage = new MessagesPage(page);
    await messagesPage.goto();
  });

  test('messaging page loads', async () => {
    await messagesPage.waitForLoad();

    // Both cards should be visible
    await expect(messagesPage.sendCard).toBeVisible();
    await expect(messagesPage.historyCard).toBeVisible();
  });

  test('can type message in textarea', async () => {
    await messagesPage.waitForLoad();

    const testMessage = 'Test message for E2E testing';
    await messagesPage.messageTextarea.fill(testMessage);

    await expect(messagesPage.messageTextarea).toHaveValue(testMessage);
  });

  test('send button is visible', async () => {
    await messagesPage.waitForLoad();

    await expect(messagesPage.sendButton).toBeVisible();
    await expect(messagesPage.sendButton).toBeEnabled();
  });

  test('broadcast/single user switch works', async ({ page }) => {
    await messagesPage.waitForLoad();

    // Initially in broadcast mode - target user input should not be visible
    await expect(messagesPage.targetUserIdInput).not.toBeVisible();

    // Switch to single user mode
    await messagesPage.broadcastSwitch.click();

    // Now target user input should be visible
    await expect(messagesPage.targetUserIdInput).toBeVisible();
  });

  test('scheduled mode toggle shows date picker', async ({ page }) => {
    await messagesPage.waitForLoad();

    // Initially date picker should not be visible
    await expect(messagesPage.scheduleDatePicker).not.toBeVisible();

    // Toggle scheduled mode
    await messagesPage.toggleScheduled();

    // Date picker should appear
    await expect(messagesPage.scheduleDatePicker).toBeVisible();
  });

  test('history table is visible', async () => {
    await messagesPage.waitForLoad();

    await expect(messagesPage.historyTable).toBeVisible();
  });

  test('form validation prevents empty message send', async ({ page }) => {
    await messagesPage.waitForLoad();

    // Try to send without text
    await messagesPage.sendButton.click();

    // Should show validation error
    const validationError = page.locator('.ant-form-item-explain-error');
    await expect(validationError).toBeVisible();

    // Should contain error text about required field
    await expect(validationError).toContainText(/введите|текст|required/i);
  });

  test('premium filter is available in broadcast mode', async ({ page }) => {
    await messagesPage.waitForLoad();

    // Check that premium filter (Статус) is visible
    await expect(page.getByText('Статус')).toBeVisible();
  });

  test('zodiac filter is available in broadcast mode', async ({ page }) => {
    await messagesPage.waitForLoad();

    // Check that zodiac filter is visible
    await expect(page.getByText('Знак зодиака')).toBeVisible();
  });

  test('history shows message columns', async ({ page }) => {
    await messagesPage.waitForLoad();

    // Check for table column headers
    await expect(page.getByRole('columnheader', { name: /текст/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /получатели/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /статус/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /дата/i })).toBeVisible();
  });
});
