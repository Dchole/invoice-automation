import { test, expect } from '@playwright/test';
import { createTestClient, createTestSession, generateTestInvoices, recordPayment } from './helpers';
import { getInvoices } from './helpers';

test.describe('Invoice Automation Flow', () => {
  test('should create a client', async ({ page, request }) => {
    const client = await createTestClient(request, { name: 'Acme Corp' });

    await page.goto('/clients');
    await page.waitForLoadState('networkidle');

    // Verify client appears in list
    await expect(page.locator('text=Acme Corp')).toBeVisible();
  });

  test('should log a work session', async ({ page, request }) => {
    const client = await createTestClient(request, { name: 'Test Client for Sessions' });

    await page.goto('/sessions');
    await page.waitForLoadState('networkidle');

    // Click "Quick Log Session"
    await page.click('button:has-text("Log Session")');

    // Fill form
    await page.selectOption('select[aria-label*="Client"]', String(client.id));
    await page.fill('input[placeholder*="Description"]', 'Consulting work');
    await page.fill('input[type="number"][placeholder*="Hours"]', '2');

    // Submit
    await page.click('button:has-text("Log")');

    // Wait for success and verify session appears
    await expect(page.locator('text=Consulting work')).toBeVisible();
  });

  test('should generate an invoice from unbilled sessions', async ({ page, request }) => {
    // Setup: create client + session
    const client = await createTestClient(request, { name: 'Invoice Test Client' });
    const session = await createTestSession(request, client.id, {
      description: 'Invoice test work',
    });

    await page.goto('/invoices');
    await page.waitForLoadState('networkidle');

    // Click "Generate All" button
    await page.click('button:has-text("Generate All")');

    // Confirm in modal
    await page.click('button:has-text("Generate All Invoices")');

    // Wait for invoice to appear
    await expect(page.locator('text=Invoice Test Client')).toBeVisible();
    await expect(page.locator('text=Invoice test work')).toBeVisible({ timeout: 5000 });
  });

  test('should record a payment and update invoice status', async ({ page, request }) => {
    // Setup: create client + session + invoice
    const client = await createTestClient(request);
    const session = await createTestSession(request, client.id);

    // Generate invoices via helper
    const invoices = await generateTestInvoices(request, client.id);
    const invoice = Array.isArray(invoices) ? invoices[0] : invoices;

    // Record payment via helper
    await recordPayment(request, invoice.id, invoice.total, 'e-transfer');

    // Navigate to invoices and verify status
    await page.goto('/invoices');
    await page.waitForLoadState('networkidle');

    // Verify status changed to "paid"
    await expect(page.locator('text=Paid')).toBeVisible({ timeout: 5000 });
  });

  test('should display dashboard with summary cards', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Verify summary cards are visible
    await expect(page.locator('text=Outstanding')).toBeVisible();
    await expect(page.locator('text=Overdue')).toBeVisible();
    await expect(page.locator('text=Unbilled')).toBeVisible();
    await expect(page.locator('text=Revenue This Month')).toBeVisible();
  });

  test('should handle mobile navigation', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Hamburger menu should be visible on mobile
    const hamburger = page.locator('button[aria-label="Toggle navigation"]');
    await expect(hamburger).toBeVisible();

    // Click to open sidebar
    await hamburger.click();

    // Navigation links should be visible
    await expect(page.locator('text=Clients')).toBeVisible();
    await expect(page.locator('text=Invoices')).toBeVisible();
    await expect(page.locator('text=Payments')).toBeVisible();

    // Click Clients link
    await page.click('text=Clients');

    // Sidebar should close and navigate to /clients
    await expect(page).toHaveURL('/clients');
  });
});
