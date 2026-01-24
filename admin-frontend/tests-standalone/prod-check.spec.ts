import { test, expect } from '@playwright/test';

test('check production admin loads', async ({ page }) => {
  console.log('🔍 Opening production admin...');

  await page.goto('https://adtrobot-production.up.railway.app/admin/login');

  // Wait for page to fully load
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(5000);

  // Get body content
  const bodyText = await page.locator('body').innerText();
  console.log('📄 Body text:', bodyText.slice(0, 300));

  // Take screenshot
  await page.screenshot({ path: 'test-results/production-admin.png', fullPage: true });
  console.log('📸 Screenshot saved to test-results/production-admin.png');

  // Check if React app loaded
  const rootDiv = await page.locator('#root').count();
  console.log('✅ #root div found:', rootDiv > 0);

  // Check for login form
  const hasLoginForm = await page.locator('form').count() > 0;
  console.log('🔐 Login form present:', hasLoginForm);

  // Check for error
  const hasError = bodyText.includes('Not Found') || bodyText.includes('detail');
  console.log('❌ Error found:', hasError);

  if (hasError) {
    console.log('🚨 ERROR: Page shows error instead of app!');
    console.log('Body:', bodyText);
  }

  // Expect no error
  expect(hasError).toBe(false);
  expect(hasLoginForm).toBe(true);
});
