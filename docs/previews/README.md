# Static design previews

These screenshots were rendered in Chromium from the converted section templates, supplied content, and project CSS using a small offline fixture renderer. They are **not screenshots of a running Django or React application**. Dynamic template context and archive results were supplied as test fixtures, and the React tools were not mounted.

Eight page layouts were checked at 1440px and 390px widths. Each had one H1, no duplicate HTML IDs, no unresolved local fragment links, and no horizontal document overflow in those fixtures. This is a layout check, not a complete accessibility, application, Wagtail preview or browser-behavior test.

- home-desktop.png: complete desktop homepage.
- standards-allocation.png: the scope section and percentage table.
- article-mobile.png: historical 0.3.0 mobile fixture, before the artwork upload. It is not a screenshot of 0.3.1. See the 0.3.1 branding evidence for the current figure checks.

The numeric checks are retained in ../evidence/visual-checks.json. Run the supplied Playwright and Django integration tests against the actual built application before deployment.
