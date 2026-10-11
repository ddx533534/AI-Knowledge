// Optional visual QA using the Codex bundled Playwright runtime; no web assets.
const { chromium } = require('playwright');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const graph = JSON.parse(fs.readFileSync('99-System/graph.json', 'utf8'));

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(path.resolve('99-System/知识图谱.html')).href);
    const count = await page.locator('#nodes .node').count();
    assert.equal(count, graph.nodes.length, 'Graph should show all current knowledge nodes and source documents');
    await page.locator('#list').selectOption('node:strands-box');
    await page.locator('#detail-title').filter({ hasText: 'Strands Box' }).waitFor();
    const strands = graph.nodes.find(n => n.id === 'node:strands-box');
    assert.equal(await page.locator('#links a').count(), 1 + new Set(strands.sources.map(s => s.document_id)).size);
    assert.equal(await page.locator('#relations button').count(), graph.edges.filter(e => e.source === strands.id || e.target === strands.id).length);
    await page.locator('#mode').selectOption('knowledge');
    assert.equal(await page.locator('#nodes .node').count(), graph.nodes.filter(n => n.kind === 'knowledge').length);
    assert.equal(await page.locator('#edges line').count(), graph.edges.filter(e => e.type !== 'evidence').length);
    await page.locator('#search').fill('Strands Box');
    assert.equal(await page.locator('#nodes .node').count(), 1);
    await page.locator('#search').fill('没有这个节点');
    assert.equal(await page.locator('#empty').isVisible(), true);
    await page.locator('#search').fill('');
    await page.locator('#mode').selectOption('all');
    await page.locator('#reset').click();
    await page.screenshot({ path: '99-System/Maintenance/验收截图.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
    assert.deepEqual(errors, []);
    console.log('Graph UI: selection, evidence links, typed edges, filtering, empty state and mobile layout passed.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
