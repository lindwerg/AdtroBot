import { test, expect } from '@playwright/test';

test('debug production admin', async ({ page }) => {
  const errors: string[] = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  page.on('pageerror', error => {
    errors.push(`Page error: ${error.message}`);
  });

  await page.goto('https://adtrobot-production.up.railway.app/admin/');
  
  // Wait a bit for page to load
  await page.waitForTimeout(5000);
  
  const bodyText = await page.locator('body').textContent();
  console.log('Body text:', bodyText?.slice(0, 200));
  console.log('Console errors:', errors);
  
  await page.screenshot({ path: 'test-results/debug-prod.png', fullPage: true });
});
