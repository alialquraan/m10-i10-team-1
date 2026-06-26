import { test, expect } from '@playwright/test';

test('kg page renders and returns rows', async ({ page }) => {
  await page.goto('/kg');


  await page.locator('input').fill('Find Sichuan recipes');
  await page.getByRole('button', { name: /Ask/i }).click();

  await expect(
    page.locator('[data-testid="kg-row"]').first()
  ).toBeVisible({ timeout: 10_000 });
});