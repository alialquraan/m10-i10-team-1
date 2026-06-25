import { test, expect } from '@playwright/test';

test('extract page renders and returns entities', async ({ page }) => {
  await page.goto('/extract');


  await page
    .locator('textarea')
    .fill('Chef Fuchsia Dunlop studied Sichuan cooking in Chengdu in 1994.');

  await page.getByRole('button', { name: /Extract/i }).click();

  await expect(
    page.locator('[data-testid="entity-span"]').first()
  ).toBeVisible({ timeout: 10_000 });
});