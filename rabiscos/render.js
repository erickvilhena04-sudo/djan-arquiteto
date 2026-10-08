// Renderiza as sequencias de rabiscos (PNG com transparencia) usando o Chromium/Playwright.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const SPECS = [
  { name: 'inkA',  kind: 'ink',   frames: 19, o: { seed: 11, angle: -8,  dir: 1 } },
  { name: 'inkB',  kind: 'ink',   frames: 24, o: { seed: 23, angle: 10,  dir: -1 } },
  { name: 'inkC',  kind: 'ink',   frames: 12, o: { seed: 37, angle: -14, dir: 1 } },
  { name: 'inkD',  kind: 'ink',   frames: 22, o: { seed: 41, angle: 6,   dir: -1 } },
  { name: 'ring',  kind: 'ring',  frames: 17, o: { cx: 540, cy: 520, rx: 185, ry: 235, seed: 5 } },
  { name: 'arrow', kind: 'arrow', frames: 13, o: { x0: 380, y0: 300, x1: 1020, y1: 215, bend: 0.25, seed: 9 } },
];
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'rabisco.html'));
  const outDir = path.resolve(__dirname, 'out'); fs.mkdirSync(outDir, { recursive: true });
  for (const s of SPECS) {
    for (let i = 0; i < s.frames; i++) {
      const t = s.frames > 1 ? i / (s.frames - 1) : 1;
      await page.evaluate(([k, t, o]) => window.renderFrame(k, t, o), [s.kind, t, s.o]);
      await page.screenshot({ path: path.join(outDir, `${s.name}_${String(i).padStart(3, '0')}.png`), omitBackground: true });
    }
    console.log('ok', s.name, s.frames);
  }
  await browser.close();
})();
