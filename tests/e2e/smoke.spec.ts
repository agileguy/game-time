import { test, expect } from '@playwright/test';

/**
 * Smoke tests to verify basic server functionality.
 */
test.describe('API Smoke Tests', () => {
  test('health endpoint returns healthy status', async ({ request }) => {
    const response = await request.get('/health');

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('service', 'Game Time');
    expect(data).toHaveProperty('version');
  });

  test('readiness endpoint returns ready status', async ({ request }) => {
    const response = await request.get('/health/ready');

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('status', 'ready');
    expect(data).toHaveProperty('database', 'connected');
    expect(data).toHaveProperty('redis', 'connected');
  });

  test('root endpoint returns API information', async ({ request }) => {
    const response = await request.get('/');

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('name', 'Game Time');
    expect(data).toHaveProperty('version');
    expect(data).toHaveProperty('docs', '/docs');
    expect(data).toHaveProperty('health', '/health');
  });

  test('OpenAPI docs are accessible', async ({ page }) => {
    await page.goto('/docs');

    // Check that Swagger UI loads
    await expect(page.locator('.swagger-ui')).toBeVisible();

    // Check for API title
    const title = page.locator('.title');
    await expect(title).toContainText('Game Time');
  });

  test('server responds within acceptable time', async ({ request }) => {
    const start = Date.now();
    const response = await request.get('/health');
    const duration = Date.now() - start;

    expect(response.ok()).toBeTruthy();
    expect(duration).toBeLessThan(1000); // Should respond within 1 second
  });
});
