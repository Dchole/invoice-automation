import { test as base } from '@playwright/test';

/**
 * Fixture setup for e2e tests
 *
 * This ensures the API backend is available before running tests.
 * The backend should be running on localhost:8000
 */

export async function waitForBackend(timeout = 30000) {
  const startTime = Date.now();
  const apiUrl = 'http://localhost:8000/api/dashboard/summary';

  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(apiUrl);
      if (response.ok) {
        return;
      }
    } catch {
      // API not ready yet, retry
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  throw new Error(`Backend API not available at ${apiUrl} after ${timeout}ms`);
}

export const test = base.extend({
  async apiReady({ }, use) {
    await waitForBackend();
    await use(null);
  },
});

export { expect } from '@playwright/test';
