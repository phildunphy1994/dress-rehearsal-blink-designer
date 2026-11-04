#!/usr/bin/env node
// svg2png.js — rasterise SVGs with the pre-installed Chromium for judge packs and visual checks.
// Usage: node scripts/svg2png.js <outDir> <in.svg> [more.svg ...]
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
(async () => {
  const [outDir, ...svgs] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  for (const svg of svgs) {
    const html = `<html><body style="margin:0;background:white">${fs.readFileSync(svg, 'utf8')}</body></html>`;
    await page.setContent(html);
    const el = await page.$('svg');
    const target = path.join(outDir, path.basename(svg, '.svg') + '.png');
    await el.screenshot({ path: target });
    console.log('wrote', target);
  }
  await browser.close();
})();
