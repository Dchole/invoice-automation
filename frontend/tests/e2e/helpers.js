/**
 * Playwright E2E Test Helpers
 *
 * Reusable test setup and navigation utilities
 */

/**
 * Create a test client via API
 */
export async function createTestClient(request, clientData = {}) {
  const data = {
    name: 'Test Client',
    email: 'test@example.com',
    company: 'Test Co',
    phone: '555-0000',
    currency: 'CAD',
    default_rate: 150,
    payment_terms: 30,
    notes: 'Test client',
    ...clientData,
  };

  const response = await request.post('/api/clients', { data });
  if (!response.ok()) {
    throw new Error(`Failed to create client: ${response.status()}`);
  }
  return response.json();
}

/**
 * Create a test session via API
 */
export async function createTestSession(request, clientId, sessionData = {}) {
  const data = {
    client_id: clientId,
    session_date: new Date().toISOString().split('T')[0],
    start_time: '09:00',
    end_time: '11:00',
    duration_minutes: 120,
    rate: 150,
    currency: 'CAD',
    amount: 300,
    description: 'Test session',
    ...sessionData,
  };

  const response = await request.post('/api/sessions', { data });
  if (!response.ok()) {
    throw new Error(`Failed to create session: ${response.status()}`);
  }
  return response.json();
}

/**
 * Generate invoices via API
 */
export async function generateTestInvoices(request, clientId, taxRate = 0) {
  const response = await request.post('/api/invoices/generate', {
    data: {
      client_id: clientId,
      tax_rate: taxRate,
    },
  });
  if (!response.ok()) {
    throw new Error(`Failed to generate invoices: ${response.status()}`);
  }
  return response.json();
}

/**
 * Record a payment via API
 */
export async function recordPayment(request, invoiceId, amount, method = 'other') {
  const response = await request.post('/api/payments', {
    data: {
      invoice_id: invoiceId,
      payment_date: new Date().toISOString().split('T')[0],
      amount,
      method,
      reference: `TEST-${Date.now()}`,
    },
  });
  if (!response.ok()) {
    throw new Error(`Failed to record payment: ${response.status()}`);
  }
  return response.json();
}

/**
 * Get all clients via API
 */
export async function getClients(request) {
  const response = await request.get('/api/clients');
  if (!response.ok()) {
    throw new Error(`Failed to get clients: ${response.status()}`);
  }
  return response.json();
}

/**
 * Get all invoices via API
 */
export async function getInvoices(request) {
  const response = await request.get('/api/invoices');
  if (!response.ok()) {
    throw new Error(`Failed to get invoices: ${response.status()}`);
  }
  return response.json();
}

/**
 * Get unbilled sessions via API
 */
export async function getUnbilled(request) {
  const response = await request.get('/api/sessions/unbilled');
  if (!response.ok()) {
    throw new Error(`Failed to get unbilled sessions: ${response.status()}`);
  }
  return response.json();
}

/**
 * Wait for element and interact
 */
export async function fillForm(page, formData) {
  for (const [selector, value] of Object.entries(formData)) {
    const element = page.locator(selector);
    await element.waitFor();
    await element.fill(String(value));
  }
}

/**
 * Navigate and wait for page
 */
export async function navigateTo(page, path) {
  await page.goto(path);
  await page.waitForLoadState('networkidle');
}

/**
 * Wait for element with text
 */
export async function waitForText(page, text, timeout = 5000) {
  await page.locator(`text=${text}`).waitFor({ timeout });
}

/**
 * Verify table contains data
 */
export async function verifyTableRow(page, rowData) {
  const row = page.locator('table tbody tr').filter({
    has: page.locator(`text=${rowData[0]}`),
  });
  await row.waitFor();

  for (const text of rowData) {
    await page.locator(`text=${text}`).waitFor();
  }
}

/**
 * Clear database and reset to clean state
 */
export async function resetDatabase(request) {
  // Delete all clients (cascade will delete sessions, invoices, payments)
  const clients = await getClients(request);
  for (const client of clients) {
    await request.delete(`/api/clients/${client.id}`);
  }
}

/**
 * Setup test data: creates client with N sessions
 */
export async function setupTestData(request, config = {}) {
  const {
    clientCount = 1,
    sessionsPerClient = 3,
    generateInvoices: shouldGenerateInvoices = false,
  } = config;

  const clients = [];
  for (let i = 0; i < clientCount; i++) {
    const client = await createTestClient(request, {
      name: `Client ${i + 1}`,
      email: `client${i + 1}@example.com`,
    });
    clients.push(client);

    // Create sessions for this client
    for (let j = 0; j < sessionsPerClient; j++) {
      await createTestSession(request, client.id, {
        description: `Session ${j + 1}`,
        session_date: new Date(Date.now() - j * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0],
      });
    }

    // Optionally generate invoices
    if (shouldGenerateInvoices) {
      await generateTestInvoices(request, client.id);
    }
  }

  return clients;
}

/**
 * Extract data from table for assertion
 */
export async function extractTableData(page, columnCount) {
  const rows = await page.locator('table tbody tr').all();
  const data = [];

  for (const row of rows) {
    const cells = await row.locator('td').all();
    const rowData = [];
    for (let i = 0; i < Math.min(cells.length, columnCount); i++) {
      const text = await cells[i].textContent();
      rowData.push(text.trim());
    }
    if (rowData.length > 0) data.push(rowData);
  }

  return data;
}
