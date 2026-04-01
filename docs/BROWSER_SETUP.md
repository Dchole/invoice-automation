# Playwright Browser Installation Guide

## Current Status

✓ Playwright npm package installed
✓ playwright.config.js configured  
✓ E2E tests written
✓ Test helpers created
✓ Backend & frontend running

⚠ Browser binaries not installed (system dependencies issue in WSL2)

## Browser Installation Options

### Option 1: Install System Dependencies (WSL2)

In WSL2, install required system libraries:

```bash
sudo apt-get update
sudo apt-get install -y \
  libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
  libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
  libpangocairo-1.0-0 libcairo2 libxcb-shm0 libxcb1 libxcb-dri3-0 \
  libxcb-dri2-0 libxcb-randr0 libxcb-render0 libxcb-shape0 \
  libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0 \
  libwayland-client0 libwayland-egl1 libgdk-pixbuf2.0-0 libglib2.0-0 \
  libgtk-3-0 libx11-6 libx11-xcb1 libxau6 libxdmcp6 libxext6 \
  libxrender1 libxtst6 libxinerama1 libxi6 libxrandr2 libxss1 \
  libxxf86vm1 fontconfig fonts-liberation2 fonts-freefont-ttf
```

Then install Playwright browsers:

```bash
cd frontend
npx playwright install
```

### Option 2: Use Docker

Run tests in a Docker container with all dependencies pre-installed:

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM mcr.microsoft.com/playwright:v1.58.0-jammy

WORKDIR /app
COPY . .

RUN cd frontend && npm install
RUN cd backend && pip install -r requirements.txt

EXPOSE 5173 8000

CMD ["sh", "-c", "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 &" \
                  "&& cd frontend && npm run dev"]
EOF

# Build and run
docker build -t invoiceflow .
docker run -p 5173:5173 -p 8000:8000 invoiceflow
```

### Option 3: Remote Browser Connection

Connect to a Chromium instance running on another machine:

```javascript
// playwright.config.js
import { defineConfig } from '@playwright/test';

export default defineConfig({
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
  },
  
  use: {
    // Connect to remote browser
    connectOptions: {
      wsEndpoint: 'ws://remote-machine:3000',
    },
  },
  
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

### Option 4: Headless Browsers with Minimal Dependencies

Use `chromium-only` mode (smaller footprint):

```bash
PLAYWRIGHT_ONLY_CHROMIUM=1 npx playwright install
```

Then configure:

```javascript
// playwright.config.js
projects: [
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'] },
  },
  // Remove firefox, webkit, mobile projects
]
```

### Option 5: Use CI/CD for Full Testing

Keep browsers installed in GitHub Actions, run local tests in headless-only mode:

```bash
# Local development - skip browser tests for now
npm run test:unit  # Unit tests only

# In GitHub Actions - full Playwright suite
npm run test:e2e
```

## Recommended Solution for WSL2

**Option 1** (Install dependencies) is recommended if you want local development:

```bash
# One-time setup
sudo apt-get update
sudo apt-get install -y $(cat > /tmp/playwright-deps.txt << 'EOF'
libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
libpangocairo-1.0-0 libcairo2 libxcb-shm0 libxcb1 libxcb-dri3-0 \
libxcb-dri2-0 libxcb-randr0 libxcb-render0 libxcb-shape0 \
libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0 \
libwayland-client0 libwayland-egl1 libgdk-pixbuf2.0-0 \
libglib2.0-0 libgtk-3-0 libx11-6
EOF
cat /tmp/playwright-deps.txt)

cd frontend
npx playwright install
```

**Option 2** (Docker) is easier if you're comfortable with containers.

## Verify Installation

```bash
cd frontend
npx playwright install --with-deps  # Install browsers + system deps
npx playwright install-deps         # Install only system deps

# Check if installed
npx playwright install --list

# Run a test
npm run test:e2e
```

## Troubleshooting

### Error: "Failed to launch browser"

```bash
# Check what's missing
npx playwright install-deps

# Or install all dependencies at once
npx playwright install --with-deps
```

### "Could not find browser binaries"

```bash
# Reinstall browsers
rm -rf ~/.cache/ms-playwright
npx playwright install
```

### WebKit/Firefox won't install on WSL2

Chromium-only mode:

```javascript
// playwright.config.js - remove firefox/webkit from projects
projects: [
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'] },
  }
]
```

## Next Steps

1. **Choose an installation method** based on your setup
2. **Install Playwright browsers**
3. **Run tests**: `npm run test:e2e`
4. **View results**: `npx playwright show-report`

Once browsers are installed, all the E2E tests are ready to run!

## Current Test Status

✓ Tests written and configured
✓ Helper functions created  
✓ Test data setup working
✓ Backend API running
✓ Frontend dev server running

Just need: Browser binaries installed

```bash
# This will work once you choose an installation method:
cd frontend && npx playwright install
npm run test:e2e
```
