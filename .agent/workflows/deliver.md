---
description: create a delivery workflow for eme features
---

// turbo-all

## Steps

1. After implementing any visual change, open the browser and navigate to `http://127.0.0.1:8000/`
2. Hard reload the page (`Ctrl+Shift+R`) to clear cache
3. Verify the following with eyes:
   - No Django `TemplateSyntaxError` or 500 error pages
   - The page loads and renders without blank/empty sections
   - New feature works as expected (click it, fill forms, etc.)
4. If any of the above fail, fix the issue BEFORE notifying the user.
5. Only after all visual checks pass, notify the user with a summary.

> **Rule**: A task is NOT complete until the browser confirms it works visually.
