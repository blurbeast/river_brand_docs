# Riverbrand Knowledge Book — Content Standard

Every chapter/appendix writer MUST follow this standard. Read it fully before writing.

## The Book

Two paired tracks over one banking engine (RiverbrandBE): **For Everyone** chapters (plain language) and **Engineering** chapters (mechanism). Chapters 1–3 and 16 are shared/engineering-onboarding. Chapter numbering is continuous 1–16.

## Non-Negotiable Rules

1. **H1 format**: `# Chapter N — Title` (exactly; filename is `chNN-slug.md` and N must match).
2. **Section numbering**: H2s are `N.M Section Title` where N = chapter number. Never reuse a `N.M` number. Use unnumbered H2s for `## Recap`, `## Key Takeaways`, `## Frequently Asked Questions`, `## Where to Go Next`.
3. **ASCII anchor-safe headings**: no emoji in headings. Punctuation like `&` is fine but prefer "and".
4. **Recap block**: keep the shell's epigraph and `## Recap` (3 bullets: Unlearn / Learn / Relearn) at the top; rewrite the bullets to be specific to your chapter's arc.
5. **Chapter skeleton order**: Epigraph → Recap → numbered sections (N.1…) → `## Key Takeaways` (4–6 bullets) → `## Frequently Asked Questions` (4–5 Q&A, use `###` for each question) → `## Where to Go Next` (twin cross-link, already in shell — keep/adjust).
6. **Word floors**: Ch 1–3, 16 ≥ 2,500 words; non-technical twins (4,6,8,10,12,14) ≥ 2,800; technical twins (5,7,9,11,13,15) ≥ 3,500. Aim for the middle of the plan's target range (non-tech 2,800–3,800; tech 3,500–5,000).
7. **Banned hype words** (the checker enforces): "bulletproof", "absolute guarantee", "absolute mathematical guarantee", "military-grade", "unbreakable", "100% secure/safe/uptime", and any bare "99.99%" claim. Use "designed to…", "verified in…", "under tested load".
8. **Non-technical jargon ban** (the checker enforces): never write `rbp_brand_*`, `river_brand_*`, `jwt_version`, `.ts` file paths, `x-local-access-token`, `x-web-access-token`, `prisma.$transaction`, `FOR UPDATE SKIP LOCKED`, or handler class names in ch 4/6/8/10/12/14. Allowed and defined at first use: NUBAN, KYC, ledger, wallet. Explain by analogy first, formal name second in one line: *"engineers call this the outbox pattern — see §5.4"*.
9. **No duplicate headings within a file** (same level + same text). Use bold paragraphs, not repeated H3s, for recurring beats like "What We Built".
10. **Relative links only** — `../chapters/ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue` style. Every link and anchor must resolve (the checker verifies). Section anchors follow the slug rule: lowercase, punctuation/emoji stripped, spaces → hyphens (e.g. `## 5.4 The Outbox and Dead-Letter Queue` → `#54-the-outbox-and-dead-letter-queue`).
11. **Cross-references** to other parts of the book use `§N.M` and are hyperlinked.
12. **UNVERIFIED**: any fact not grounded in the old documentation gets an inline **UNVERIFIED** marker.

## Voice and Depth

- **Non-technical**: open with a named persona story (e.g. "Amina, a salary earner in Lagos…"). Mechanisms explained with real-world analogies (the book's canonical four: bank-vault airlock, hotel keycard, guaranteed courier, airport tower — they live in Appendix F, so cite and link, do not re-tell at length). Then a section `## N.x What We Built, Why, and Where It Goes` with bold-paragraph beats: **What we built** · **Why it matters** · **What we aim for** · **The approach ahead**. Honest metrics only.
- **Technical**: interface signatures, config excerpts, table names, sequence/state diagrams (Mermaid), failure-mode tables (markdown table). Ground every fact in the old docs (source files listed below). Preserve: Redlock + single-commit transaction, outbox + DLQ (`FOR UPDATE SKIP LOCKED`, LISTEN/NOTIFY), NUBAN Providus→Fincra fallback, pending-balance tank + KYC ceilings (₦50k/₦200k/₦5M tiers), dual-token isolation, sidecar `jwt_version` kill-switch, Argon2id, RBAC, audit trail, `IWhatsAppProvider` factory (Meta/Twilio/Termii/Wati/Interakt/360dialog), Redis conversation state machine, FCM, jobs fleet (OutboxJob, DlqJob, SavingsJob, ReconciliationJob, BillReconciliationJob, ArchivalJob, GeneralLedgerJob), ports (API 8010, Mailpit 8026, PgBouncer 6432, Prometheus 9095), 39 services with file paths.

## Figures

- Mermaid: use fenced ```mermaid blocks (sequenceDiagram / stateDiagram-v2 / graph TD). Precede each with a bold caption: `**Figure N.M — Title.**` These render live in the web book.
- Custom SVGs are added later (Phase 5). If your chapter needs one, insert a marker on its own line: `<!-- FIGURE: fig-ch05-redlock-guard.svg | Figure 5.2 — The Redlock guard -->`. Do NOT link to a nonexistent image file.

## Sources (old docs still in repo root — read them for facts, then leave them alone)

- `01-executive-overview.md` — vision, 5 currency journeys, analogies, competitive moat, risk matrix
- `02-architecture-and-design.md` — stack, PgBouncer, execution flow, Redlock, sidecar, WhatsApp factory, outbox/DLQ, KYC tank, observability
- `03-core-banking-and-financial-engine.md` — concurrency, NUBAN lifecycle, idempotency, limits, settlement
- `04-savings-investments-and-channels.md` — Safelock math, WhatsApp factory/state machine, FCM
- `05-security-compliance-and-auditing.md` — dual-token, jwt_version, PINs, RBAC, audit
- `06-future-upgrade-roadmap.md` — microservices, Kafka, CockroachDB, AI, GNN fraud, BaaS, benchmarks
- `07-developer-and-operations-manual.md` — setup, env, Docker, Prisma, webhooks, jobs, troubleshooting
- `08-service-catalog-and-deep-dive.md` — 39 services with paths/methods/tables
- `0*-non-technical-*.md` — existing plain-language material to enrich (do not copy the thin template style)

## Branding

"Riverbrand Banking System" (product/book), "RiverbrandBE" (codebase), "RBP" only after first definition. Table prefixes: document as-is; flag legacy names (`savings_*`, `user_user`) as to-be-renamed. See ch03 §3.5 for the canonical prefix map.

## Template Beats (non-technical "What We Built" section)

```
## N.x What We Built, Why, and Where It Goes

**What we built.** …plain prose…

**Why it matters.** …customer/business consequence…

**What we aim for.** …outcome we are driving at…

**The approach ahead.** …how this evolves (link to roadmap twin)…
```
