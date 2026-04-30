#!/usr/bin/env node
/**
 * v2 Standalone 디자인 토큰 추출 (rendered DOM 기준) — v2 (selector 보강)
 *
 * 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v7 §2.2 + 사용자 결정 A3
 * 작성자:   [claude]
 *
 * v1 → v2 변경 (사용자 결정 A3 반영):
 *  - selector 8 → 50+ 영역 확장
 *  - color frequency 분석 (사용 빈도 top 20)
 *  - font-size 분포
 *  - spacing 분포
 *  - 카드/배지/버튼/테이블/검색바/KPI 등 컴포넌트 영역별 추출
 *  - 사용자 확정: standalone "흰색-회색 톤" — 베이지 가정 폐기
 *
 * 사용자 결정 (2026-05-01):
 *  - standalone 그대로 흰색-회색 톤 유지 (#F5F4EE 베이지 아님)
 *  - rendered DOM 기준 v2_tokens.css 전면 재정의
 */

const path = require('path');
const fs = require('fs');

const STANDALONE_PATH = path.resolve(__dirname, '..', 'docs', 'reference', 'dual_engine_v2_standalone.html');
const OUTPUT_DIR = path.resolve(__dirname, '..', 'outputs', 'reference');
const OUTPUT_JSON = path.join(OUTPUT_DIR, 'v2_tokens_rendered.json');
const OUTPUT_CSS = path.join(OUTPUT_DIR, 'v2_tokens_rendered.css');
const OUTPUT_REPORT = path.join(OUTPUT_DIR, 'v2_tokens_analysis_report.md');

async function main() {
  let chromium;
  try {
    ({ chromium } = require('@playwright/test'));
  } catch (err) {
    console.error('[FAIL] @playwright/test 미설치');
    process.exit(1);
  }

  if (!fs.existsSync(STANDALONE_PATH)) {
    console.error(`[FAIL] standalone 미존재: ${STANDALONE_PATH}`);
    process.exit(1);
  }
  console.log(`[INFO] standalone: ${STANDALONE_PATH}`);

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });

  try {
    const fileUrl = 'file://' + STANDALONE_PATH;
    console.log(`[INFO] 페이지 로드: ${fileUrl}`);
    await page.goto(fileUrl);

    console.log('[INFO] bundler unpack 대기...');
    try {
      await page.waitForFunction(
        () => !document.getElementById('__bundler_loading'),
        { timeout: 30000 }
      );
    } catch (err) {
      console.warn('[WARN] bundler_loading 미해제 — 5초 추가 대기');
      await page.waitForTimeout(5000);
    }

    // 추가 안정화
    await page.waitForTimeout(2000);

    console.log('[INFO] computed style 수집 (50+ 영역)...');

    const result = await page.evaluate(() => {
      // ============================================================
      // 유틸리티
      // ============================================================
      function rgbToHex(rgb) {
        if (!rgb || rgb === 'rgba(0, 0, 0, 0)' || rgb === 'transparent') return null;
        const m = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (!m) return rgb;
        const [, r, g, b] = m;
        return '#' + [r, g, b].map(n => parseInt(n).toString(16).padStart(2, '0').toUpperCase()).join('');
      }

      function getComputed(el, prop) {
        return getComputedStyle(el).getPropertyValue(prop).trim();
      }

      function firstMatchingComputed(selectors, prop) {
        for (const sel of selectors) {
          const el = document.querySelector(sel);
          if (el) {
            const v = getComputed(el, prop);
            if (v && v !== '' && v !== 'rgba(0, 0, 0, 0)') return v;
          }
        }
        return null;
      }

      // ============================================================
      // 1. Color frequency 분석 (전체 화면 사용 빈도)
      // ============================================================
      const allElements = document.querySelectorAll('*');
      const colorCounts = new Map();
      const bgColorCounts = new Map();
      const borderColorCounts = new Map();

      function bump(map, key) {
        if (!key || key === 'rgba(0, 0, 0, 0)' || key === 'transparent') return;
        map.set(key, (map.get(key) || 0) + 1);
      }

      for (const el of allElements) {
        const cs = getComputedStyle(el);
        bump(colorCounts, cs.color);
        bump(bgColorCounts, cs.backgroundColor);
        bump(borderColorCounts, cs.borderColor);
      }

      const topColors = [...colorCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20)
        .map(([color, count]) => ({ color, hex: rgbToHex(color), count }));

      const topBgColors = [...bgColorCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20)
        .map(([color, count]) => ({ color, hex: rgbToHex(color), count }));

      const topBorderColors = [...borderColorCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([color, count]) => ({ color, hex: rgbToHex(color), count }));

      // ============================================================
      // 2. Font-size 분포
      // ============================================================
      const fontSizeCounts = new Map();
      const fontWeightCounts = new Map();
      const fontFamilySet = new Set();

      for (const el of allElements) {
        const cs = getComputedStyle(el);
        bump(fontSizeCounts, cs.fontSize);
        bump(fontWeightCounts, cs.fontWeight);
        if (cs.fontFamily) fontFamilySet.add(cs.fontFamily);
      }

      const topFontSizes = [...fontSizeCounts.entries()]
        .sort((a, b) => parseFloat(b[0]) - parseFloat(a[0]))   // 큰 → 작은 정렬
        .map(([size, count]) => ({ size, count }));

      // ============================================================
      // 3. Border-radius 분포
      // ============================================================
      const radiusCounts = new Map();
      for (const el of allElements) {
        const r = getComputedStyle(el).borderRadius;
        if (r && r !== '0px') bump(radiusCounts, r);
      }
      const topRadii = [...radiusCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([radius, count]) => ({ radius, count }));

      // ============================================================
      // 4. Spacing 분포 (padding)
      // ============================================================
      const paddingCounts = new Map();
      for (const el of allElements) {
        const p = getComputedStyle(el).padding;
        if (p && p !== '0px') bump(paddingCounts, p);
      }
      const topPaddings = [...paddingCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([padding, count]) => ({ padding, count }));

      // ============================================================
      // 5. 컴포넌트별 영역 추출
      // ============================================================

      // KPI 디스플레이 — 큰 숫자
      const kpiDisplay = (() => {
        // 가장 큰 font-size 가진 요소 찾기
        let maxSize = 0;
        let maxEl = null;
        for (const el of allElements) {
          const size = parseFloat(getComputedStyle(el).fontSize);
          if (size > maxSize && el.textContent.trim().length > 0 && el.textContent.trim().length < 20) {
            maxSize = size;
            maxEl = el;
          }
        }
        if (!maxEl) return null;
        const cs = getComputedStyle(maxEl);
        return {
          tag: maxEl.tagName.toLowerCase(),
          textContent: maxEl.textContent.trim().slice(0, 20),
          fontSize: cs.fontSize,
          fontWeight: cs.fontWeight,
          color: cs.color,
          colorHex: rgbToHex(cs.color),
          lineHeight: cs.lineHeight
        };
      })();

      // 카드 영역 후보들
      const cardCandidates = [];
      const cardSelectors = [
        '[class*="rounded-"]',
        '[class*="card"]',
        '[class*="Card"]',
        'main > div > div',
        'section > div'
      ];
      for (const sel of cardSelectors) {
        const els = document.querySelectorAll(sel);
        for (const el of els) {
          const cs = getComputedStyle(el);
          if (cs.borderRadius !== '0px' && parseFloat(cs.borderRadius) > 0) {
            cardCandidates.push({
              tag: el.tagName.toLowerCase(),
              className: el.className.toString().slice(0, 100),
              bg: cs.backgroundColor,
              bgHex: rgbToHex(cs.backgroundColor),
              borderRadius: cs.borderRadius,
              padding: cs.padding,
              border: cs.border
            });
            if (cardCandidates.length >= 10) break;
          }
        }
        if (cardCandidates.length >= 10) break;
      }

      // 헤더 영역
      const headerCandidates = [];
      const headerSelectors = [
        'header', 'nav', '[class*="header"]', '[class*="Header"]',
        '[class*="navbar"]', '[class*="topbar"]',
        'body > div:first-child'
      ];
      for (const sel of headerSelectors) {
        const el = document.querySelector(sel);
        if (el) {
          const cs = getComputedStyle(el);
          headerCandidates.push({
            selector: sel,
            tag: el.tagName.toLowerCase(),
            className: el.className.toString().slice(0, 100),
            bg: cs.backgroundColor,
            bgHex: rgbToHex(cs.backgroundColor),
            color: cs.color,
            colorHex: rgbToHex(cs.color),
            height: cs.height,
            padding: cs.padding
          });
        }
      }

      // 버튼 영역
      const buttons = [...document.querySelectorAll('button, [role="button"], [class*="btn"], [class*="Button"]')]
        .slice(0, 5).map(el => {
          const cs = getComputedStyle(el);
          return {
            text: el.textContent.trim().slice(0, 30),
            bg: cs.backgroundColor,
            bgHex: rgbToHex(cs.backgroundColor),
            color: cs.color,
            colorHex: rgbToHex(cs.color),
            borderRadius: cs.borderRadius,
            padding: cs.padding,
            fontSize: cs.fontSize,
            border: cs.border
          };
        });

      // 입력 필드
      const inputs = [...document.querySelectorAll('input, textarea, select')]
        .slice(0, 5).map(el => {
          const cs = getComputedStyle(el);
          return {
            type: el.type || el.tagName.toLowerCase(),
            bg: cs.backgroundColor,
            bgHex: rgbToHex(cs.backgroundColor),
            color: cs.color,
            colorHex: rgbToHex(cs.color),
            borderRadius: cs.borderRadius,
            border: cs.border,
            padding: cs.padding,
            fontSize: cs.fontSize
          };
        });

      // 테이블
      const tableInfo = (() => {
        const table = document.querySelector('table');
        if (!table) return null;
        const cs = getComputedStyle(table);
        const firstRow = table.querySelector('tr');
        const firstCell = table.querySelector('td, th');
        return {
          tableBg: rgbToHex(cs.backgroundColor),
          rowBorder: firstRow ? getComputedStyle(firstRow).borderBottom : null,
          cellPadding: firstCell ? getComputedStyle(firstCell).padding : null,
          cellHeight: firstCell ? getComputedStyle(firstCell).height : null,
          fontSize: firstCell ? getComputedStyle(firstCell).fontSize : null
        };
      })();

      // 배지/칩
      const badges = [...document.querySelectorAll('[class*="badge"], [class*="chip"], [class*="rounded-full"], [class*="pill"]')]
        .slice(0, 5).map(el => {
          const cs = getComputedStyle(el);
          return {
            text: el.textContent.trim().slice(0, 30),
            className: el.className.toString().slice(0, 80),
            bg: cs.backgroundColor,
            bgHex: rgbToHex(cs.backgroundColor),
            color: cs.color,
            colorHex: rgbToHex(cs.color),
            borderRadius: cs.borderRadius,
            padding: cs.padding,
            fontSize: cs.fontSize,
            fontWeight: cs.fontWeight
          };
        });

      // ============================================================
      // 6. Body 메타
      // ============================================================
      const bodyCs = getComputedStyle(document.body);

      return {
        body: {
          bg: bodyCs.backgroundColor,
          bgHex: rgbToHex(bodyCs.backgroundColor),
          color: bodyCs.color,
          colorHex: rgbToHex(bodyCs.color),
          fontFamily: bodyCs.fontFamily,
          fontSize: bodyCs.fontSize,
          margin: bodyCs.margin,
          padding: bodyCs.padding
        },

        // 빈도 분석
        frequency: {
          colors: topColors,
          backgrounds: topBgColors,
          borderColors: topBorderColors,
          fontSizes: topFontSizes,
          fontWeights: [...fontWeightCounts.entries()].sort((a,b) => b[1]-a[1]).map(([w,c]) => ({weight: w, count: c})),
          fontFamilies: [...fontFamilySet],
          radii: topRadii,
          paddings: topPaddings
        },

        // 컴포넌트별
        components: {
          kpiDisplay,
          cards: cardCandidates,
          headers: headerCandidates,
          buttons,
          inputs,
          table: tableInfo,
          badges
        },

        meta: {
          documentTitle: document.title,
          bodyChildCount: document.body.children.length,
          totalElements: allElements.length,
          windowSize: { width: window.innerWidth, height: window.innerHeight }
        }
      };
    });

    // ============================================================
    // 출력 정리
    // ============================================================
    const fullResult = {
      _meta: {
        extracted_at: new Date().toISOString(),
        source: STANDALONE_PATH,
        viewport: { width: 1200, height: 800 },
        engine: 'chromium',
        script_version: 'v2 (A3 selector 보강)'
      },
      ...result
    };

    fs.writeFileSync(OUTPUT_JSON, JSON.stringify(fullResult, null, 2));
    console.log(`[OK] JSON: ${OUTPUT_JSON}`);

    // CSS 변수 자동 생성 (frequency 기반)
    const top3Bg = result.frequency.backgrounds.slice(0, 5).map(b => b.hex).filter(Boolean);
    const top3Text = result.frequency.colors.slice(0, 5).map(c => c.hex).filter(Boolean);
    const topFontSize = result.frequency.fontSizes.slice(0, 5);

    const cssLines = [
      '/**',
      ' * v2 Standalone rendered DOM 토큰 — 자동 생성 v2',
      ` * extracted_at: ${fullResult._meta.extracted_at}`,
      ` * script:       ${fullResult._meta.script_version}`,
      ' *',
      ' * 사용자 결정 (2026-05-01):',
      ' *  - standalone 그대로 흰색-회색 톤 유지',
      ' *  - 베이지 #F5F4EE 가정 폐기',
      ' *',
      ' * 본 파일은 web/styles/v2_tokens.css 정정용 reference.',
      ' */',
      '',
      ':root {',
      '  /* === Body 기본 (rendered) === */',
      `  --rendered-body-bg:           ${result.body.bgHex || result.body.bg};`,
      `  --rendered-body-color:        ${result.body.colorHex || result.body.color};`,
      `  --rendered-body-font-family:  ${result.body.fontFamily};`,
      `  --rendered-body-font-size:    ${result.body.fontSize};`,
      '',
      '  /* === Top 5 background 빈도 === */',
      ...top3Bg.map((hex, i) => `  --rendered-bg-top${i+1}:        ${hex};   /* count: ${result.frequency.backgrounds[i].count} */`),
      '',
      '  /* === Top 5 text color 빈도 === */',
      ...top3Text.map((hex, i) => `  --rendered-text-top${i+1}:      ${hex};   /* count: ${result.frequency.colors[i].count} */`),
      '',
      '  /* === Top 5 font-size === */',
      ...topFontSize.map((f, i) => `  --rendered-fs-top${i+1}:        ${f.size};  /* count: ${f.count} */`),
      '',
      '  /* === KPI Display === */',
      result.components.kpiDisplay
        ? `  --rendered-kpi-display-size:  ${result.components.kpiDisplay.fontSize};`
        : '  /* KPI display 미발견 */',
      result.components.kpiDisplay
        ? `  --rendered-kpi-display-color: ${result.components.kpiDisplay.colorHex};`
        : '',
      '',
      '  /* === Card border-radius === */',
      ...(result.frequency.radii.slice(0, 3).map((r, i) => `  --rendered-radius-top${i+1}:    ${r.radius};   /* count: ${r.count} */`)),
      '}',
      ''
    ];
    fs.writeFileSync(OUTPUT_CSS, cssLines.filter(l => l !== '').join('\n').replace(/\n{3,}/g, '\n\n'));
    console.log(`[OK] CSS: ${OUTPUT_CSS}`);

    // ============================================================
    // 분석 보고서 (Markdown)
    // ============================================================
    const reportLines = [
      `# v2 Standalone 디자인 토큰 분석 보고서`,
      ``,
      `- 추출일: ${fullResult._meta.extracted_at}`,
      `- 스크립트: ${fullResult._meta.script_version}`,
      `- 출처: \`${path.basename(STANDALONE_PATH)}\``,
      `- viewport: 1200x800`,
      ``,
      `## 1. Body 기본`,
      ``,
      '| 속성 | 값 |',
      '|---|---|',
      `| background | \`${result.body.bgHex || result.body.bg}\` |`,
      `| color | \`${result.body.colorHex || result.body.color}\` |`,
      `| font-family | \`${result.body.fontFamily}\` |`,
      `| font-size | \`${result.body.fontSize}\` |`,
      ``,
      `## 2. Top 10 background 색상 (빈도)`,
      ``,
      '| # | hex | rgb | 사용 횟수 |',
      '|---|---|---|---|',
      ...result.frequency.backgrounds.slice(0, 10).map((b, i) =>
        `| ${i+1} | \`${b.hex || '?'}\` | \`${b.color}\` | ${b.count} |`),
      ``,
      `## 3. Top 10 text 색상 (빈도)`,
      ``,
      '| # | hex | rgb | 사용 횟수 |',
      '|---|---|---|---|',
      ...result.frequency.colors.slice(0, 10).map((c, i) =>
        `| ${i+1} | \`${c.hex || '?'}\` | \`${c.color}\` | ${c.count} |`),
      ``,
      `## 4. Border 색상`,
      ``,
      '| # | hex | rgb | 사용 횟수 |',
      '|---|---|---|---|',
      ...result.frequency.borderColors.slice(0, 5).map((c, i) =>
        `| ${i+1} | \`${c.hex || '?'}\` | \`${c.color}\` | ${c.count} |`),
      ``,
      `## 5. Font-size 분포 (큰 → 작은)`,
      ``,
      '| 크기 | 사용 횟수 |',
      '|---|---|',
      ...result.frequency.fontSizes.slice(0, 15).map(f =>
        `| \`${f.size}\` | ${f.count} |`),
      ``,
      `## 6. Border-radius 분포`,
      ``,
      '| radius | 사용 횟수 |',
      '|---|---|',
      ...result.frequency.radii.slice(0, 10).map(r =>
        `| \`${r.radius}\` | ${r.count} |`),
      ``,
      `## 7. KPI Display`,
      ``,
      result.components.kpiDisplay
        ? `\`\`\`json\n${JSON.stringify(result.components.kpiDisplay, null, 2)}\n\`\`\``
        : `미발견`,
      ``,
      `## 8. Card 후보 (${result.components.cards.length}개)`,
      ``,
      ...result.components.cards.slice(0, 5).map((c, i) => [
        `### Card ${i+1}`,
        '```json',
        JSON.stringify(c, null, 2),
        '```',
        ''
      ]).flat(),
      `## 9. Header 후보 (${result.components.headers.length}개)`,
      ``,
      ...result.components.headers.slice(0, 5).map((h, i) => [
        `### Header ${i+1} (selector: \`${h.selector}\`)`,
        '```json',
        JSON.stringify(h, null, 2),
        '```',
        ''
      ]).flat(),
      `## 10. Button (${result.components.buttons.length}개)`,
      ``,
      ...result.components.buttons.slice(0, 3).map((b, i) => [
        `### Button ${i+1}`,
        '```json',
        JSON.stringify(b, null, 2),
        '```',
        ''
      ]).flat(),
      `## 11. Input/Form (${result.components.inputs.length}개)`,
      ``,
      ...result.components.inputs.slice(0, 3).map((inp, i) => [
        `### Input ${i+1}`,
        '```json',
        JSON.stringify(inp, null, 2),
        '```',
        ''
      ]).flat(),
      `## 12. Table`,
      ``,
      result.components.table
        ? `\`\`\`json\n${JSON.stringify(result.components.table, null, 2)}\n\`\`\``
        : `테이블 미발견`,
      ``,
      `## 13. 배지/칩 (${result.components.badges.length}개)`,
      ``,
      ...result.components.badges.slice(0, 5).map((b, i) => [
        `### Badge ${i+1}`,
        '```json',
        JSON.stringify(b, null, 2),
        '```',
        ''
      ]).flat(),
      `## 14. 메타`,
      ``,
      `- documentTitle: \`${result.meta.documentTitle}\``,
      `- 전체 element 수: ${result.meta.totalElements}`,
      `- body 자식 수: ${result.meta.bodyChildCount}`,
      `- font-family 종류: ${result.frequency.fontFamilies.length}`,
      ``,
      `## 15. font-family 목록`,
      ``,
      ...result.frequency.fontFamilies.slice(0, 10).map(f => `- \`${f}\``),
      ``,
      `---`,
      ``,
      `**다음 단계 (A1 후속)**: 본 분석 결과로 \`web/styles/v2_tokens.css\`를 전면 재정의.`
    ];
    fs.writeFileSync(OUTPUT_REPORT, reportLines.join('\n'));
    console.log(`[OK] Report: ${OUTPUT_REPORT}`);

    console.log('');
    console.log('=== 핵심 요약 ===');
    console.log(`Body bg:        ${result.body.bgHex || result.body.bg}`);
    console.log(`Body color:     ${result.body.colorHex || result.body.color}`);
    console.log(`Body font:      ${result.body.fontFamily.slice(0, 60)}...`);
    console.log(`전체 element:    ${result.meta.totalElements}`);
    console.log(`Top 3 bg:       ${result.frequency.backgrounds.slice(0, 3).map(b => b.hex).join(', ')}`);
    console.log(`Top 3 text:     ${result.frequency.colors.slice(0, 3).map(c => c.hex).join(', ')}`);
    console.log(`Top 3 fontsize: ${result.frequency.fontSizes.slice(0, 3).map(f => f.size).join(', ')}`);
    console.log(`Top 3 radius:   ${result.frequency.radii.slice(0, 3).map(r => r.radius).join(', ')}`);
    if (result.components.kpiDisplay) {
      console.log(`KPI Display:    ${result.components.kpiDisplay.fontSize} ${result.components.kpiDisplay.colorHex}`);
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
