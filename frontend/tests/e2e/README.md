# E2E Tests with Playwright

End-to-end tests for InvoiceFlow using Playwright.

## Setup

### Prerequisites

- Node.js 18+
- Python 3.10+ (for backend)
- Backend and frontend dev servers running

### Installation

Playwright is already installed as a dev dependency. Install browsers:

```bash
npx playwright install
```

## Running Tests

### Start Services

In one terminal, start the backend:

```bash
cd ../..
cd backend
python -m uvicorn app.main:app --reload
```

In another terminal, start the frontend dev server:

```bash
cd frontend
npm run dev
```

### Run Tests

```bash
# Run all tests in headless mode
npm run test:e2e

# Run tests with UI (interactive mode)
npm run test:e2e:ui

# Run tests in headed mode (watch browser)
npm run test:e2e:headed

# Debug specific test file
npx playwright test tests/e2e/invoicing-flow.spec.js --debug
```

## Test Coverage

- **invoicing-flow.spec.js** — Full invoicing workflow
  - Client creation
  - Session logging
  - Invoice generation
  - Payment recording
  - Dashboard display
  - Mobile navigation

## Writing New Tests

Tests are in [invoicing-flow.spec.js](./invoicing-flow.spec.js). Each test:

1. Sets up test data via the API (using the `request` fixture)
2. Navigates the UI and performs user actions
3. Asserts expected outcomes

Helper functions available:

- `createTestClient(request, clientData)` — Create a test client
- `createTestSession(request, clientId, sessionData)` — Create a test session

Example:

```javascript
test('should do something', async ({ page, request }) => {
  // Setup via API
  const client = await createTestClient(request, { name: 'Test Client' });

  // Interact with UI
  await page.goto('/clients');
  await expect(page.locator('text=Test Client')).toBeVisible();
});
```

## Debugging

- Use `--debug` flag to step through tests
- Use `--headed` to watch the browser during execution
- Check `playwright-report/` directory for HTML test reports after runs
- Use `page.pause()` in tests to pause execution at a specific point

## CI/CD

For CI environments, tests run with:
- 2 retries on failure
- Single worker (no parallelization)
- HTML report generation

Set the `CI` environment variable to enable CI mode.
