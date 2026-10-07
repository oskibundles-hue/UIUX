// playwright.js: load Playwright on whatever machine the build runs on.
// Order: $PLAYWRIGHT_MODULE (the Mac setup points it at 10-vlog-locked-on/.node), a normal require, then the global
// install in the cloud container. The browser itself comes from Playwright's own cache (npx playwright install chromium).
const tries = [process.env.PLAYWRIGHT_MODULE, 'playwright', '/opt/node22/lib/node_modules/playwright'].filter(Boolean);
let pw = null;
for (const t of tries) {
  try { pw = require(t); break; } catch (e) { /* next */ }
}
if (!pw) throw new Error('Playwright not found: run 10-vlog-locked-on/setup-mac.sh, or set PLAYWRIGHT_MODULE');
module.exports = pw;
