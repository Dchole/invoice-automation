# Playwright Setup for InvoiceFlow

This document summarizes the Playwright E2E testing setup for the InvoiceFlow invoice automation system.

## What Was Set Up

### Files Created

```
frontend/
├── playwright.config.js                 # Playwright configuration
├── package.json                         # Updated with test scripts
├── tests/e2e/
│   ├── invoicing-flow.spec.js          # Main E2E test suite
│   ├── helpers.js                      # Reusable test helpers
│   ├── setup.ts                        # Test fixture setup
│   └── README.md                       # E2E test documentation

root/
├── TESTING.md                          # Comprehensive testing guide
├── PLAYWRIGHT_SETUP.md                 # This file
├── run-tests.sh                        # Helper script to run tests
└── verify-setup.sh                     # Setup verification script
```

## Quick Start

### 1. Install Playwright Browsers

```bash
cd frontend
npx playwright install --with-deps
```

This downloads Chrome, Firefox, Safari, and mobile browser engines (~500MB).

### 2. Start Services

**Terminal 1 — Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload
# Running on http://localhost:8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# Running on http://localhost:5173
```

### 3. Run Tests

**Terminal 3 — Tests:**
```bash
cd frontend
npm run test:e2e
```

Or use the automated script:
```bash
./run-tests.sh
```

## Test Scripts

Added to `frontend/package.json`:

```json
"test:e2e": "playwright test",
"test:e2e:ui": "playwright test --ui",
"test:e2e:debug": "playwright test --debug",
"test:e2e:headed": "playwright test --headed"
```

### Usage

```bash
npm run test:e2e          # Run all tests (headless, fastest)
npm run test:e2e:ui       # Interactive test picker UI
npm run test:e2e:debug    # Step through tests in debugger
npm run test:e2e:headed   # Watch browser during tests
```

## Test Structure

### invoicing-flow.spec.js — Main Test Suite

Tests the complete user workflow:

1. **Create a client** — Verify client appears in list
2. **Log a work session** — Quick-log a session
3. **Generate invoices** — Batch create from unbilled sessions
4. **Record payments** — Update invoice status
5. **Dashboard summary** — Verify all cards visible
6. **Mobile navigation** — Test responsive hamburger menu

Each test:
- Sets up test data via API helpers
- Navigates the UI
- Asserts expected outcomes
- Works with clean data (no cross-test pollution)

### helpers.js — Reusable Utilities

API helpers for test data setup:
- `createTestClient(request, data)` — Create client
- `createTestSession(request, clientId, data)` — Create session
- `generateTestInvoices(request, clientId, taxRate)` — Generate invoices
- `recordPayment(request, invoiceId, amount, method)` — Record payment
- `getClients(request)` — Fetch all clients
- `getInvoices(request)` — Fetch all invoices
- `getUnbilled(request)` — Fetch unbilled sessions

UI helpers for interactions:
- `fillForm(page, formData)` — Fill form fields
- `navigateTo(page, path)` — Navigate to page
- `waitForText(page, text)` — Wait for text to appear
- `verifyTableRow(page, rowData)` — Verify table row
- `setupTestData(request, config)` — Create complete test dataset

### Playwright Configuration

**playwright.config.js** includes:

- **Test directory:** `tests/e2e`
- **Browsers:** Chromium, Firefox, WebKit
- **Mobile:** Pixel 5, iPhone 12
- **Base URL:** `http://localhost:5173`
- **Web server:** Starts `npm run dev` before tests
- **Reports:** HTML report generation
- **Retries:** 2 on CI, 0 locally
- **Timeout:** 30 seconds per test (configurable)

## Browser Coverage

Tests run against:
- ✓ Chrome (Desktop)
- ✓ Firefox (Desktop)
- ✓ Safari (WebKit)
- ✓ Chrome Mobile (Pixel 5)
- ✓ Safari Mobile (iPhone 12)

Customize in `playwright.config.js`:

```javascript
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
]
```

## Running Tests

### Headless (CI-like, fastest)

```bash
npm run test:e2e
```

Output:
```
✓ invoicing-flow.spec.js (6 tests)
6 passed [45s]
```

### Interactive UI

```bash
npm run test:e2e:ui
```

Opens a visual test picker where you can:
- Run individual tests
- Filter by name
- See live test execution
- Review results with screenshots

### Watch Mode (during development)

```bash
npm run test:e2e -- --watch
```

Re-runs tests as you save files.

### Debug Mode

```bash
npm run test:e2e:debug
```

Opens Playwright Inspector where you can:
- Step through test code line-by-line
- Inspect DOM at each step
- Evaluate expressions in console
- Resume execution

### Headed Mode (watch browser)

```bash
npm run test:e2e:headed
```

Tests run with visible browser window, useful for:
- Understanding what tests do
- Debugging UI interactions
- Visual verification

## Test Reports

After running tests, view the HTML report:

```bash
npx playwright show-report
```

Report includes:
- ✓/✗ status for each test
- Screenshots at each step
- Video recordings (if enabled)
- Trace files for debugging
- Execution timeline

## Debugging Techniques

### 1. Visual Inspection — Headed Mode

```bash
npm run test:e2e:headed
```

Watch the browser during test execution.

### 2. Step-by-Step — Debug Mode

```bash
npm run test:e2e:debug
```

Use the Playwright Inspector to step through code.

### 3. Pause Execution

```javascript
test('debug this', async ({ page }) => {
  await page.goto('/');
  await page.pause();  // Pauses here, resume from Inspector UI
  await page.click('button');
});
```

### 4. Log Values

```javascript
const text = await page.locator('h1').textContent();
console.log('Found text:', text);
```

### 5. Extract Data

```javascript
const tableData = await extractTableData(page, 4);
console.log('Table contents:', tableData);
```

### 6. Traces for Time-Travel Debugging

Enable in `playwright.config.js`:

```javascript
use: {
  trace: 'on-first-retry',  // Record trace on failed tests
},
```

Then view:

```bash
npx playwright show-trace trace.zip
```

Time-travel back through the test, inspect DOM at each moment.

## Continuous Integration

For GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - run: cd frontend && npm ci
      - run: cd frontend && npx playwright install --with-deps
      
      # Start backend
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && python -m uvicorn app.main:app &
      - run: sleep 3
      
      # Run tests
      - run: cd frontend && npm run test:e2e
      
      # Upload reports on failure
      - if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Performance Tips

### 1. Reduce Browser Count for CI

Edit `playwright.config.js`:

```javascript
projects: process.env.CI
  ? [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]
  : [
      { name: 'chromium', ... },
      { name: 'firefox', ... },
      { name: 'webkit', ... },
    ]
```

### 2. Parallel Test Files

By default, test files run in parallel:

```javascript
fullyParallel: true  // Run tests in parallel within files too
```

Set `fullyParallel: false` to serialize tests.

### 3. Reuse Existing Server

```javascript
webServer: {
  ...
  reuseExistingServer: !process.env.CI  // Reuse dev server
}
```

## Troubleshooting

### Tests Can't Connect to Backend

```bash
# Check backend is running
curl http://localhost:8000/api/dashboard/summary

# If not running:
cd backend
python -m uvicorn app.main:app --reload
```

### Playwright Browsers Not Installed

```bash
npx playwright install --with-deps
```

### Port Conflicts

```bash
# Find and kill process on port 8000
lsof -i :8000 | grep -v PID | awk '{print $2}' | xargs kill -9

# Find and kill process on port 5173
lsof -i :5173 | grep -v PID | awk '{print $2}' | xargs kill -9
```

### Flaky Tests

Common causes:
- Missing waits: `await page.waitForLoadState('networkidle')`
- Timeout too short: `test.setTimeout(60000)`
- Element not visible: Use `waitFor()` with explicit timeout

Solution:
```javascript
// Add explicit waits
await page.waitForLoadState('networkidle');
await page.locator('text=Invoice').waitFor({ timeout: 10000 });
```

### Network Requests Blocked

Playwright config has API proxy configured. If tests fail:

```javascript
// In playwright.config.js
use: {
  baseURL: 'http://localhost:5173',
  // Ensure baseURL matches your dev server
}
```

## Next Steps

1. **Expand test coverage** — Add tests for edge cases
2. **Add visual regression testing** — Use `toHaveScreenshot()`
3. **Monitor test metrics** — Track performance over time
4. **Integrate with CI/CD** — Add to GitHub Actions
5. **Load testing** — Use Playwright for performance testing

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Testing Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [CI/CD Integration](https://playwright.dev/docs/ci)

## Summary

✓ Playwright installed and configured
✓ 6 core E2E tests written
✓ Helper utilities for test data setup
✓ Test scripts in package.json
✓ Documentation and verification tools
✓ Ready for CI/CD integration

Both backend and frontend are currently running. Next step: Run the tests!

```bash
cd frontend && npm run test:e2e
```
