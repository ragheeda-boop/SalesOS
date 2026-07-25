# Visual Regression Testing

## Overview

Visual regression tests use Playwright's screenshot comparison to catch unintended visual changes.

## Running

### Update Baseline Screenshots

```bash
npx playwright test --config playwright.config.ts --project=chromium tests/visual/ --update-snapshots
```

### Run Tests (Compare Against Baseline)

```bash
npx playwright test --config playwright.config.ts --project=chromium tests/visual/
```

### Run with Report

```bash
npx playwright test --config playwright.config.ts --project=chromium tests/visual/ --reporter=html
```

## Adding New Tests

1. Add a new `test()` block in `visual-regression.spec.ts`
2. Navigate to the page and call `expect(page).toHaveScreenshot()`
3. Run with `--update-snapshots` to generate the baseline
4. Commit the baseline images to the repository

## Best Practices

- Use `maxDiffPixels: 100` to allow minor anti-aliasing differences
- Use `fullPage: true` to capture the entire page
- Test both light and dark modes
- Test responsive layouts at different breakpoints (640px, 768px, 1024px, 1280px)
- Run tests in CI to catch regressions before deployment
