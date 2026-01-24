import { test } from '@playwright/test';

test('diagnose production admin', async ({ page }) => {
  console.log('Opening production admin...');

  await page.goto('https://adtrobot-production.up.railway.app/admin/login');

  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  const bodyText = await page.locator('body').textContent();
  console.log('Body content:', bodyText);

  const html = await page.content();
  console.log('Full HTML length:', html.length);
  console.log('HTML preview:', html.slice(0, 500));

  await page.screenshot({ path: '/tmp/prod-admin.png', fullPage: true });
  console.log('Screenshot saved');
});
