# Figure Style Guide — Riverbrand Knowledge Book

All custom SVG figures MUST share one visual language. Follow this exactly.

## Canvas and Structure

- Canvas: `viewBox="0 0 960 560"` (landscape) unless the figure is a ladder/timeline (`960x640`).
- Root: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 560" font-family="Segoe UI, Avenir Next, Helvetica, Arial, sans-serif">`
- Background: full-bleed `<rect width="960" height="560" fill="#f8fafc"/>`.
- No external images, no CSS files, no scripts. Inline styles/attributes only.
- Every text element: explicit `font-size`, `fill`, `text-anchor`. Never rely on defaults.

## Palette (use ONLY these)

| Role | Color |
|---|---|
| Primary / structure | `#0f766e` (teal) |
| Primary light fill | `#ccfbf1` |
| Secondary / engineering | `#1e293b` (slate) |
| Secondary light fill | `#e2e8f0` |
| Accent / highlight / money | `#d97706` (amber) |
| Accent light fill | `#fef3c7` |
| Info / flows / sky | `#0ea5e9` |
| Danger / risk / quarantine | `#dc2626` |
| Danger light fill | `#fee2e2` |
| Card / surface | `#ffffff` |
| Border | `#cbd5e1` |
| Body text | `#334155` |
| Muted text | `#64748b` |
| Success | `#16a34a` |

## Shape Vocabulary

- Cards/boxes: `<rect rx="12" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>` — width ≥ 160, padding 16px.
- Pills/badges: `<rect rx="16" …/>` with 13px text.
- Arrows: define one marker in `<defs>`:
  `<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#0f766e"/></marker>`
  Use `marker-end="url(#arrow)"` on paths/lines. Flow arrows teal (`#0f766e`), risk flows red (`#dc2626` with `id="arrow-red"`), money flows amber (`#d97706` with `id="arrow-amber"`).
- Icons: built from primitive shapes only (circles, rects, paths). Style: 2–3px strokes, rounded joins. Money = circle with ₦/$/€ text or coin ellipse. Person = circle head + rounded rect body. Lock/shield/key/door/chat-bubble = simple geometric path. Keep icons abstract-geometric, NOT cartoonish.

## Typography

- Figure title (inside SVG, top-left, 22px, bold, `#1e293b`): e.g. "The Bank-Vault Airlock".
- Section/step labels: 15px bold `#334155`.
- Body/detail labels: 13px `#334155`.
- Captions/annotations: 12px `#64748b` (italic).
- Money/currency numbers: 14px bold `#d97706`.
- Never exceed 6 text lines per box; wrap manually with separate `<text>` lines (line-height 18).

## Composition Rules

- Title row at top (y≈36), diagram body y 80–520.
- 4–8 major elements max. White space is good.
- Left-to-right or top-to-bottom flow. Spacing between major boxes ≥ 40px.
- A "human element" in non-technical figures: small person icon + a one-line quote in a speech-style rounded rect where it helps the story.
- Technical figures may use numbered step badges (circle 15px radius with white number).

## File Naming and Output

- Exact filenames are prescribed per figure (see agent assignment). Write to `images/<filename>.svg`.
- Keep each file self-contained and valid (no truncated tags). Run a quick sanity check that the file parses (`python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])"`).
