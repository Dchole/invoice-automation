# Testing Guide for InvoiceFlow

This document covers testing setup and best practices for the InvoiceFlow application.

## Test Architecture

```
├── Backend Tests (pytest) — Unit & integration tests
│   └── tests/test_*.py
│
└── Frontend Tests (Playwright) — E2E browser tests
    └── frontend/tests/e2e/
```

## Backend Tests (Python)

### Running Backend Tests

```bash
cd backend
pytest -v
```

### Coverage

- **35 passing tests** covering:
  - Client CRUD operations
  - Session logging and status tracking
  - Invoice generation and linking
  - Payment tracking and status updates
  - Reminder scheduling
  - Dashboard analytics (aging, cash flow, client scores)

### Test Structure

```python
# tests/conftest.py — Fixtures
fixtures:
  - test_db: In-memory SQLite database
  - test_client: FastAPI TestClient
  - sample_client: Pre-created test client
  - sample_session: Pre-created unbilled session
  - sample_invoice: Pre-created draft invoice

# tests/test_clients.py
test_create_client()
test_update_client()
test_list_clients()
test_delete_client()

# tests/test_sessions.py
test_log_session()
test_get_unbilled_sessions()
test_link_session_to_invoice()

# tests/test_invoices.py
test_generate_invoices()
test_create_invoice()
test_void_invoice()
test_send_invoice()

# tests/test_payments.py
test_record_payment()
test_partial_payment()
test_full_payment_marks_paid()
test_payment_updates_status()

# tests/test_dashboard.py
test_dashboard_summary()
test_aging_analysis()
test_cash_flow_forecast()
test_client_scores()

# tests/test_reminders.py
test_schedule_reminders()
test_skip_paid_invoices()
test_escalation_sequence()
```

### Writing New Backend Tests

```python
def test_my_feature(test_client):
    """Test description"""
    # Setup
    client_data = {"name": "Acme", "email": "acme@example.com", ...}
    
    # Execute
    response = test_client.post("/api/clients", json=client_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "Acme"
```

## Frontend Tests (Playwright)

### Prerequisites

```bash
cd frontend
npm install
npx playwright install  # Install browser binaries
```

### Quick Start — Option 1: Manual Service Management

Terminal 1 — Backend:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

Terminal 2 — Frontend:
```bash
cd frontend
npm run dev
```

Terminal 3 — Tests:
```bash
cd frontend
npm run test:e2e
```

### Quick Start — Option 2: Automated Script

```bash
chmod +x run-tests.sh
./run-tests.sh
```

The script will:
- Check if backend (port 8000) and frontend (port 5173) are running
- Start missing services
- Run Playwright tests
- Clean up on exit

### Test Commands

```bash
# Run all tests (headless, fast)
npm run test:e2e

# Interactive UI — visually select and run tests
npm run test:e2e:ui

# Watch mode — re-run tests as you edit them
npm run test:e2e:watch

# Headed mode — watch tests in browser as they run
npm run test:e2e:headed

# Debug mode — step through tests line-by-line
npm run test:e2e:debug

# Run specific test file
npx playwright test tests/e2e/invoicing-flow.spec.js

# Run tests matching a pattern
npx playwright test --grep "invoice"
```

### Test Coverage

**invoicing-flow.spec.js** — Full application workflow
1. **Create a client** — Verify client appears in list
2. **Log a work session** — Quick-log via modal
3. **Generate invoices** — Batch create from unbilled sessions
4. **Record payments** — Update invoice status to paid
5. **Dashboard summary** — Verify all cards visible
6. **Mobile navigation** — Responsive hamburger menu and drawer

### Writing New E2E Tests

```javascript
import { test, expect } from '@playwright/test';

test('should accomplish a user goal', async ({ page, request }) => {
  // 1. Setup data via API
  const response = await request.post('/api/clients', {
    data: { name: 'Test Client', email: 'test@example.com' }
  });
  const client = await response.json();

  // 2. Navigate and interact with UI
  await page.goto('/clients');
  await expect(page.locator('text=Test Client')).toBeVisible();

  // 3. Assert expected outcomes
  await page.click('button:has-text("Edit")');
  await page.fill('input[aria-label="Name"]', 'Updated Name');
  await page.click('button:has-text("Update")');
  await expect(page.locator('text=Updated Name')).toBeVisible();
});
```

### Debugging Tests

#### Visual Debugging — Watch it Run

```bash
npm run test:e2e:headed  # See browser during test execution
```

#### Interactive Debugging — Step Through

```bash
npm run test:e2e:debug
# Playwright Inspector opens, step through with controls
```

#### Pause Execution

```javascript
test('debug example', async ({ page }) => {
  await page.goto('/');
  
  // Pause here, inspect page state, resume from inspector
  await page.pause();
  
  await page.click('button');
});
```

#### View Test Report

```bash
npm run test:e2e
# After tests complete:
npx playwright show-report
```

Opens an HTML report with:
- Test results (pass/fail)
- Screenshots for each step
- Video recordings (if enabled)
- Trace files for time-travel debugging

#### Enable Video Recording

Edit `playwright.config.js`:

```javascript
use: {
  video: 'on-first-retry',  // or 'retain-on-failure'
},
```

### API Request Helpers

Tests have access to the `request` fixture for direct API testing:

```javascript
test('api direct call', async ({ request }) => {
  // GET
  const getResp = await request.get('/api/clients/1');
  const client = await getResp.json();

  // POST
  const postResp = await request.post('/api/invoices/generate', {
    data: { client_id: client.id, tax_rate: 0 }
  });

  // PUT
  await request.put('/api/clients/1', {
    data: { name: 'Updated' }
  });

  // DELETE
  await request.delete('/api/clients/1');
});
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: cd backend && pip install -r requirements.txt && pytest

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci && npx playwright install
      - run: cd backend && pip install -r requirements.txt && python -m uvicorn app.main:app &
      - run: cd frontend && npm run dev &
      - run: cd frontend && npm run test:e2e
```

## Performance Benchmarks

### Backend Test Suite
- **Time:** ~5-8 seconds
- **Tests:** 35 passing
- **Coverage:** 80%+ code coverage

### Frontend Test Suite
- **Time:** ~45-60 seconds (headless, no retries)
- **Tests:** 6 key user workflows
- **Browsers:** Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000 (backend)
lsof -i :8000 | grep -v PID | awk '{print $2}' | xargs kill -9

# Kill process on port 5173 (frontend)
lsof -i :5173 | grep -v PID | awk '{print $2}' | xargs kill -9
```

### Playwright Browsers Not Found

```bash
npx playwright install
```

### Tests Hang Waiting for Backend

```bash
# Check backend is running
curl http://localhost:8000/api/dashboard/summary

# Or use the helper script
./run-tests.sh
```

### Flaky Tests

- Add explicit waits: `await page.waitForLoadState('networkidle')`
- Increase timeout: `test.setTimeout(30000)`
- Check network tab in trace viewer for slow endpoints

### Database Not Reset Between Tests

Each test uses the full app with the same SQLite database. Between test runs:

```bash
# The database is recreated in setup_test_db() in conftest.py
# Delete manually if needed:
rm -f app.db
rm -f test.db

# Then re-run tests
```

## Best Practices

### Backend Testing

- ✅ Use fixtures for common setup
- ✅ Test happy path AND error conditions
- ✅ Verify database state after operations
- ✅ Test with real in-memory database (not mocks)

### Frontend Testing

- ✅ Start with critical user journeys
- ✅ Use data-testid for reliable element selection
- ✅ Wait for network activity: `page.waitForLoadState('networkidle')`
- ✅ Test mobile viewport separately
- ✅ Avoid testing implementation details (CSS, internal state)

### General

- ✅ Test at multiple levels:
  - Unit: individual functions
  - Integration: components working together
  - E2E: full user journeys
  
- ✅ Keep tests isolated (no test order dependency)
- ✅ Use meaningful test names that describe behavior
- ✅ Maintain test data factories for consistent setup

## Resources

- [Playwright Documentation](https://playwright.dev)
- [pytest Documentation](https://docs.pytest.org)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [React Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
