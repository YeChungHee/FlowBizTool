#!/usr/bin/env node
/**
 * v2 미리보기 vs Standalone 시각 비교 — v2 (반응형 보강)
 *
 * 문서번호: FBU-CMP-V2-PREVIEW-v2-20260501
 * 작성자:   [claude]
 *
 * C1 — 미리보기 HTML 시각 검증
 *  1. standalone (file://) + v2_preview (http://8011) 동시 렌더
 *  2. **3 viewport 반응형** (1200×900 desktop / 768×1024 tablet / 390×844 mobile)
 *     ← P2-2 [codex] B1 검증 정정: 1200px 데스크톱만 검증 → 3종 반응형 보강
 *  3. 동일 selector(body)의 computed style 추출
 *  4. 토큰 정합성 비교 (10 computed style 항목 — body/card/header)
 *     ← P2-1 [codex] B1 검증 정정: "100% 검증" 표현 범위 명시
 *  5. 결과를 outputs/reference/comparison/ + 보고서 .md
 *
 * 검증 범위 명시:
 *  - 본 스크립트는 body/card/header 중심 10개 computed style만 비교
 *  - 22개 전체 컴포넌트 / 픽셀 단위 / 인터랙션은 검증 범위 밖
 *  - "100% 일치"는 항상 "핵심 10개 computed style 기준 100%"로 표현
 */

const path = require('path');
const fs = require('fs');

const STANDALONE_URL = 'file://' + path.resolve(__dirname, '..', 'docs', 'reference', 'dual_engine_v2_standalone.html');
const PREVIEW_URL = 'http://127.0.0.1:8011/web/v2_preview.html';

const OUT_DIR = path.resolve(__dirname, '..', 'outputs', 'reference', 'comparison');
const REPORT_PATH = path.join(OUT_DIR, 'v2_preview_comparison_report.md');

// P2-2 [codex] B1 검증 정정: 3 viewport 반응형
// F1 [codex] B1-P2-fix 정정: 태블릿 768→820 (1024px 이하 미디어쿼리 검증, 768은 모바일 경계와 충돌)
const VIEWPORTS = [
  { name: 'desktop', width: 1200, height: 900,  device: '데스크톱' },
  { name: 'tablet',  width: 820,  height: 1180, device: '태블릿 (iPad Air)' },   // ← 820 (1024px 미디어쿼리만 적용)
  { name: 'mobile',  width: 390,  height: 844,  device: '모바일 (iPhone 14 Pro)' },
];

async function main() {
  let chromium;
  try {
    ({ chromium } = require('@playwright/test'));
  } catch (err) {
    console.error('[FAIL] @playwright/test 미설치 — `npm install` 후 재시도');
    process.exit(1);
  }

  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });

  // P2-2 정정: 3 viewport 반복 결과를 누적
  const allViewportResults = [];

  try {
    for (const VP of VIEWPORTS) {
      console.log('');
      console.log(`=== ${VP.device} (${VP.width}×${VP.height}) ===`);

      const screenshotStandalone = path.join(OUT_DIR, `standalone_${VP.name}.png`);
      const screenshotPreview = path.join(OUT_DIR, `v2_preview_${VP.name}.png`);

      // ----------------------------------------------------------
      // 1. Standalone
      // ----------------------------------------------------------
      console.log(`[1/2] Standalone 렌더 (${VP.name})...`);
      const standalonePage = await browser.newPage({ viewport: { width: VP.width, height: VP.height } });
      await standalonePage.goto(STANDALONE_URL);

      try {
        await standalonePage.waitForFunction(
          () => !document.getElementById('__bundler_loading'),
          { timeout: 30000 }
        );
      } catch (err) {
        console.warn('[WARN] bundler_loading timeout — 5초 추가');
        await standalonePage.waitForTimeout(5000);
      }
      await standalonePage.waitForTimeout(2000);

      await standalonePage.screenshot({ path: screenshotStandalone, fullPage: false });
      console.log(`  └ screenshot: ${path.basename(screenshotStandalone)}`);

      const standaloneTokens = await standalonePage.evaluate(() => {
        function rgbToHex(rgb) {
          if (!rgb || rgb === 'rgba(0, 0, 0, 0)') return null;
          const m = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
          if (!m) return rgb;
          return '#' + [m[1], m[2], m[3]].map(n => parseInt(n).toString(16).padStart(2, '0').toUpperCase()).join('');
        }
        const body = getComputedStyle(document.body);
        const card = document.querySelector('.card');
        const cardCs = card ? getComputedStyle(card) : null;
        const header = document.querySelector('header, .topbar');
        const headerCs = header ? getComputedStyle(header) : null;
        return {
          body: {
            bg: rgbToHex(body.backgroundColor),
            color: rgbToHex(body.color),
            fontFamily: body.fontFamily,
            fontSize: body.fontSize,
          },
          card: cardCs ? {
            bg: rgbToHex(cardCs.backgroundColor),
            borderRadius: cardCs.borderRadius,
            padding: cardCs.padding,
          } : null,
          header: headerCs ? {
            bg: rgbToHex(headerCs.backgroundColor),
            color: rgbToHex(headerCs.color),
            height: headerCs.height,
          } : null,
          documentTitle: document.title,
        };
      });
      await standalonePage.close();

      // ----------------------------------------------------------
      // 2. v2_preview
      // ----------------------------------------------------------
      console.log(`[2/2] v2_preview 렌더 (${VP.name})...`);
      const previewPage = await browser.newPage({ viewport: { width: VP.width, height: VP.height } });
      await previewPage.goto(PREVIEW_URL, { waitUntil: 'networkidle' });
      await previewPage.waitForTimeout(1000);

      await previewPage.screenshot({ path: screenshotPreview, fullPage: false });
      console.log(`  └ screenshot: ${path.basename(screenshotPreview)}`);

      const previewTokens = await previewPage.evaluate(() => {
        function rgbToHex(rgb) {
          if (!rgb || rgb === 'rgba(0, 0, 0, 0)') return null;
          const m = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
          if (!m) return rgb;
          return '#' + [m[1], m[2], m[3]].map(n => parseInt(n).toString(16).padStart(2, '0').toUpperCase()).join('');
        }
        const body = getComputedStyle(document.body);
        const card = document.querySelector('.fbu-card');
        const cardCs = card ? getComputedStyle(card) : null;
        const header = document.querySelector('.fbu-header');
        const headerCs = header ? getComputedStyle(header) : null;
        const root = getComputedStyle(document.documentElement);
        return {
          body: {
            bg: rgbToHex(body.backgroundColor),
            color: rgbToHex(body.color),
            fontFamily: body.fontFamily,
            fontSize: body.fontSize,
          },
          card: cardCs ? {
            bg: rgbToHex(cardCs.backgroundColor),
            borderRadius: cardCs.borderRadius,
            padding: cardCs.padding,
          } : null,
          header: headerCs ? {
            bg: rgbToHex(headerCs.backgroundColor),
            color: rgbToHex(headerCs.color),
            height: headerCs.height,
          } : null,
          cssVariables: {
            bgPrimary: root.getPropertyValue('--fbu-color-bg-primary').trim(),
            bgCard: root.getPropertyValue('--fbu-color-bg-card').trim(),
            bgHeader: root.getPropertyValue('--fbu-color-bg-header').trim(),
            textPrimary: root.getPropertyValue('--fbu-color-text-primary').trim(),
            fontFamily: root.getPropertyValue('--fbu-font-family').trim(),
            headerHeight: root.getPropertyValue('--fbu-header-height').trim(),
            radiusXl: root.getPropertyValue('--fbu-radius-xl').trim(),
          },
          // F3 [codex] B1-P2-fix: horizontal overflow assertion
          overflow: {
            bodyScrollWidth: document.body.scrollWidth,
            docScrollWidth: document.documentElement.scrollWidth,
            viewportWidth: window.innerWidth,
            hasOverflow: document.documentElement.scrollWidth > window.innerWidth,
          },
          documentTitle: document.title,
        };
      });
      await previewPage.close();

      // F2 [codex] B1-P2-fix P1: viewport별 토큰 비교 자동화
      function viewportCmp(a, b) {
        if (a === null || a === undefined || b === null || b === undefined) return 'N/A';
        const norm = v => (v || '').toString().toLowerCase().replace(/\s+/g, ' ').trim();
        return norm(a) === norm(b) ? '✅' : '❌';
      }
      const vpComparisons = [
        { label: 'body bg',           s: standaloneTokens.body.bg,            p: previewTokens.body.bg },
        { label: 'body color',        s: standaloneTokens.body.color,         p: previewTokens.body.color },
        { label: 'body fontFamily',   s: standaloneTokens.body.fontFamily,    p: previewTokens.body.fontFamily },
        { label: 'body fontSize',     s: standaloneTokens.body.fontSize,      p: previewTokens.body.fontSize },
        { label: 'card bg',           s: standaloneTokens.card?.bg,           p: previewTokens.card?.bg },
        { label: 'card borderRadius', s: standaloneTokens.card?.borderRadius, p: previewTokens.card?.borderRadius },
        { label: 'card padding',      s: standaloneTokens.card?.padding,      p: previewTokens.card?.padding },
        { label: 'header bg',         s: standaloneTokens.header?.bg,         p: previewTokens.header?.bg },
        { label: 'header color',      s: standaloneTokens.header?.color,      p: previewTokens.header?.color },
        { label: 'header height',     s: standaloneTokens.header?.height,     p: previewTokens.header?.height },
      ];
      const vpMatches = vpComparisons.filter(c => viewportCmp(c.s, c.p) === '✅').length;
      const vpTotalCmp = vpComparisons.filter(c => viewportCmp(c.s, c.p) !== 'N/A').length;
      const vpMatchRate = vpTotalCmp > 0 ? Math.round((vpMatches / vpTotalCmp) * 100) : 0;

      allViewportResults.push({
        viewport: VP,
        standaloneTokens,
        previewTokens,
        comparisons: vpComparisons,
        matchRate: vpMatchRate,
        matches: vpMatches,
        totalCmp: vpTotalCmp,
        screenshotStandalone: path.basename(screenshotStandalone),
        screenshotPreview: path.basename(screenshotPreview),
      });

      console.log(`  └ ${VP.name} 토큰 일치: ${vpMatchRate}% (${vpMatches}/${vpTotalCmp})`);
      console.log(`  └ ${VP.name} overflow: bodyScrollWidth=${previewTokens.overflow.bodyScrollWidth} viewport=${previewTokens.overflow.viewportWidth} ${previewTokens.overflow.hasOverflow ? '❌ OVERFLOW' : '✅ ok'}`);
    }

    // 후속 코드는 마지막 viewport (desktop/1200) 결과 기준 호환
    const lastResult = allViewportResults[0];   // desktop이 첫 번째
    const standaloneTokens = lastResult.standaloneTokens;
    const previewTokens = lastResult.previewTokens;

    // ============================================================
    // 3. 시각/토큰 비교
    // ============================================================
    console.log('[3/4] 토큰 비교...');

    function cmp(a, b) {
      if (a === null || b === null) return 'N/A';
      const norm = v => (v || '').toString().toLowerCase().replace(/\s+/g, ' ').trim();
      return norm(a) === norm(b) ? '✅' : '❌';
    }

    const comparisons = [
      { label: 'body bg',           standalone: standaloneTokens.body.bg,           preview: previewTokens.body.bg },
      { label: 'body color',        standalone: standaloneTokens.body.color,        preview: previewTokens.body.color },
      { label: 'body fontFamily',   standalone: standaloneTokens.body.fontFamily,   preview: previewTokens.body.fontFamily },
      { label: 'body fontSize',     standalone: standaloneTokens.body.fontSize,     preview: previewTokens.body.fontSize },
      { label: 'card bg',           standalone: standaloneTokens.card?.bg,          preview: previewTokens.card?.bg },
      { label: 'card borderRadius', standalone: standaloneTokens.card?.borderRadius, preview: previewTokens.card?.borderRadius },
      { label: 'card padding',      standalone: standaloneTokens.card?.padding,     preview: previewTokens.card?.padding },
      { label: 'header bg',         standalone: standaloneTokens.header?.bg,        preview: previewTokens.header?.bg },
      { label: 'header color',      standalone: standaloneTokens.header?.color,     preview: previewTokens.header?.color },
      { label: 'header height',     standalone: standaloneTokens.header?.height,    preview: previewTokens.header?.height },
    ];

    const matches = comparisons.filter(c => cmp(c.standalone, c.preview) === '✅').length;
    const totalCmp = comparisons.filter(c => cmp(c.standalone, c.preview) !== 'N/A').length;
    const matchRate = totalCmp > 0 ? Math.round((matches / totalCmp) * 100) : 0;

    // ============================================================
    // 4. 보고서 작성
    // ============================================================
    console.log('[4/4] 보고서 작성...');

    const reportLines = [
      `# v2 미리보기 vs Standalone 시각 비교 보고서 (반응형 v2)`,
      ``,
      `- 문서번호: FBU-CMP-V2-PREVIEW-v2-20260501`,
      `- 작성일: 2026-05-01`,
      `- 작성자: [claude]`,
      `- 작업: C1 — 미리보기 HTML 시각 검증 + P2-1 표현 정정 + P2-2 반응형 보강`,
      `- 검증 viewport: ${VIEWPORTS.map(v => `${v.name} ${v.width}×${v.height}`).join(', ')}`,
      ``,
      `## 0. 검증 범위 명시 (P2-1 [codex] B1 정정)`,
      ``,
      `본 비교는 **body/card/header 중심 10개 computed style 기준**입니다.`,
      ``,
      `| 검증 범위 | 포함 |`,
      `|---|:---:|`,
      `| body bg/color/fontFamily/fontSize | ✅ |`,
      `| card bg/borderRadius/padding | ✅ |`,
      `| header bg/color/height | ✅ |`,
      `| **22 컴포넌트 전체** | ❌ (검증 범위 밖) |`,
      `| **픽셀 단위 정합** | ❌ (검증 범위 밖) |`,
      `| **인터랙션** | ❌ (검증 범위 밖) |`,
      `| **반응형 토큰 (P2-2 보강)** | ✅ ${VIEWPORTS.length} viewport |`,
      ``,
      `> 따라서 "100% 일치"는 항상 **"핵심 10개 computed style 기준 100%"**로 해석.`,
      ``,
      `## 1. 비교 대상`,
      ``,
      '| 종류 | URL |',
      '|---|---|',
      `| **Standalone (시안 원본)** | \`${STANDALONE_URL}\` |`,
      `| **v2_preview (B1 산출물)** | \`${PREVIEW_URL}\` |`,
      ``,
      `## 2. 반응형 스크린샷 (P2-2 [codex] B1 신설)`,
      ``,
      ...allViewportResults.map(r => [
        `### 2.${VIEWPORTS.indexOf(r.viewport) + 1} ${r.viewport.device} (${r.viewport.width}×${r.viewport.height})`,
        ``,
        `**Standalone**:`,
        ``,
        `![standalone-${r.viewport.name}](./${r.screenshotStandalone})`,
        ``,
        `**v2 미리보기**:`,
        ``,
        `![v2_preview-${r.viewport.name}](./${r.screenshotPreview})`,
        ``,
      ]).flat(),
      `## 3. 3 viewport별 핵심 10개 computed style 비교 (F2 [codex] B1-P2-fix 정정)`,
      ``,
      '| Viewport | size | 일치율 | overflow assertion |',
      '|---|---|:---:|:---:|',
      ...allViewportResults.map(r => {
        const o = r.previewTokens.overflow;
        const overflowOk = !o.hasOverflow ? `✅ ok (scroll ${o.bodyScrollWidth} ≤ viewport ${o.viewportWidth})` : `❌ OVERFLOW (scroll ${o.bodyScrollWidth} > viewport ${o.viewportWidth})`;
        return `| ${r.viewport.name} | ${r.viewport.width}×${r.viewport.height} | ${r.matchRate}% (${r.matches}/${r.totalCmp}) | ${overflowOk} |`;
      }),
      ``,
      `### 3.1 desktop 1200×900 — ${matchRate}% 일치 — ${matches}/${totalCmp}`,
      ``,
      '| 속성 | Standalone | v2 미리보기 | 일치 |',
      '|---|---|---|:---:|',
      ...comparisons.map(c =>
        `| ${c.label} | \`${c.standalone || 'N/A'}\` | \`${c.preview || 'N/A'}\` | ${cmp(c.standalone, c.preview)} |`),
      ``,
      `## 4. CSS 변수 노출 (v2_preview만)`,
      ``,
      '| 변수 | 값 |',
      '|---|---|',
      ...Object.entries(previewTokens.cssVariables).map(([k, v]) =>
        `| \`--fbu-${k.replace(/([A-Z])/g, '-$1').toLowerCase()}\` | \`${v}\` |`),
      ``,
      `## 5. 메타`,
      ``,
      '| 항목 | Standalone | v2 미리보기 |',
      '|---|---|---|',
      `| document.title | \`${standaloneTokens.documentTitle}\` | \`${previewTokens.documentTitle}\` |`,
      ``,
      `## 6. 검증 결과 — 핵심 10개 computed style 기준 (P2-1 [codex] 정정)`,
      ``,
      matchRate >= 80
        ? `✅ **핵심 10개 computed style 기준 ${matchRate}% 일치** (${matches}/${totalCmp}) — Phase 0 acceptance criteria "차이 < 5%" (95% 이상 일치) 기준 ${matchRate >= 95 ? '**충족**' : matchRate >= 80 ? '**근접** (보강 검토)' : '미달'}.`
        : `🔴 **핵심 10개 computed style 기준 ${matchRate}% 일치** — 차이 大. v2_components.css 또는 토큰 추가 정정 필요.`,
      ``,
      `> 본 결과는 22 컴포넌트 / 픽셀 / 인터랙션 검증을 포함하지 않습니다 (P2-1 [codex] B1 정정).`,
      ``,
      `### 6.1 핵심 일치 항목`,
      ``,
      ...comparisons
        .filter(c => cmp(c.standalone, c.preview) === '✅')
        .map(c => `- ✅ ${c.label}: \`${c.standalone}\``),
      ``,
      `### 6.2 차이 발견 항목`,
      ``,
      ...comparisons
        .filter(c => cmp(c.standalone, c.preview) === '❌')
        .map(c => `- ❌ ${c.label}: standalone \`${c.standalone}\` vs preview \`${c.preview}\``),
      ``,
      `## 7. 다음 단계 제안`,
      ``,
      matchRate >= 95
        ? `- Phase 0 종료, **Phase 1 (EvaluationSnapshot API) 진입 가능**\n- v2 미리보기를 시연용으로 사용자 confirm`
        : matchRate >= 80
        ? `- Phase 0 90% 통과, **나머지 차이 항목 정정 후 Phase 1 진입**\n- 차이 항목별 v2_tokens.css 또는 v2_components.css 정정\n- 재실행: \`node scripts/compare_v2_preview_vs_standalone.js\``
        : `- 🔴 v2_components.css 또는 v2_tokens.css 전면 재검토\n- 차이 항목 우선순위:\n${comparisons.filter(c => cmp(c.standalone, c.preview) === '❌').map(c => `  - \`${c.label}\``).join('\n')}`,
      ``,
      `---`,
      ``,
      `**재실행 명령**: \`node scripts/compare_v2_preview_vs_standalone.js\``,
      ``,
      `**대상 갱신 시**: standalone HTML 또는 v2 컴포넌트 변경 후 재실행`
    ];
    fs.writeFileSync(REPORT_PATH, reportLines.join('\n'));
    console.log(`  └ report: ${REPORT_PATH}`);

    // 콘솔 요약
    console.log('');
    console.log('=== 비교 결과 ===');
    console.log(`일치율: ${matchRate}% (${matches}/${totalCmp})`);
    console.log(`Standalone bg:    ${standaloneTokens.body.bg}`);
    console.log(`v2_preview bg:    ${previewTokens.body.bg}`);
    console.log(`Standalone card:  ${standaloneTokens.card?.bg} radius=${standaloneTokens.card?.borderRadius}`);
    console.log(`v2_preview card:  ${previewTokens.card?.bg} radius=${previewTokens.card?.borderRadius}`);
    console.log(`Standalone hdr:   ${standaloneTokens.header?.bg} h=${standaloneTokens.header?.height}`);
    console.log(`v2_preview hdr:   ${previewTokens.header?.bg} h=${previewTokens.header?.height}`);

    if (matchRate < 95) {
      console.log('');
      console.log('=== 차이 항목 ===');
      comparisons.filter(c => cmp(c.standalone, c.preview) === '❌').forEach(c => {
        console.log(`  ❌ ${c.label}`);
        console.log(`      standalone: ${c.standalone}`);
        console.log(`      preview:    ${c.preview}`);
      });
    }

  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error('[FAIL]', err.message);
  console.error(err.stack);
  process.exit(1);
});
