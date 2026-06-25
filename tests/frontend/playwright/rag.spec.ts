import { test, expect } from '@playwright/test';

test('rag page renders cited answer', async ({ page }) => {
  await page.goto('/rag');

  await page.locator('input').fill('How do I prep ginger for stir-fry?');
  await page.getByRole('button', { name: /Ask/i }).click();

  await expect(
    page.locator('[data-testid="rag-answer"]')
  ).toBeVisible({ timeout: 30_000 });

  await expect(
    page.locator('[data-testid="citation-marker"]').first()
  ).toBeVisible({ timeout: 30_000 });
});