# How to Read This Book

## The Master Method: Learn, Unlearn, Relearn

Every chapter in this book is built on one pedagogy, and this is its only home:

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│      1. UNLEARN         │ ──► │        2. LEARN         │ ──► │       3. RELEARN        │
│  Discard naive          │     │  Understand real        │     │  Master Riverbrand's    │
│  assumptions and        │     │  failure modes, race    │     │  resilient, ledger-first│
│  traditional shortcuts  │     │  conditions, and traps  │     │  architecture           │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

1. **Unlearn** — the comfortable mental model you arrived with ("a bank is a balance number in a database") is wrong. Every chapter opens by dismantling it.
2. **Learn** — the real forces at play: concurrency, immutability, idempotency, provider failure, regulatory ceilings. The chapters teach the mechanism honestly, trade-offs included.
3. **Relearn** — how Riverbrand answers those forces, and why that answer holds under load. By the end of each chapter you can reason about the system, not just recite it.

You will see a short **recap block** at the top of every chapter — a three-line reminder of the unlearn/learn/relearn arc for that topic. The full method lives here; chapters only echo it.

## The Two Tracks

| | Non-Technical Track | Technical Track |
|---|---|---|
| **Chapters** | 4, 6, 8, 10, 12, 14 (+ Foundations 1–3) | 5, 7, 9, 11, 13, 15, 16 (+ Foundations 1–3) |
| **Language** | Plain English, stories, analogies | Interfaces, tables, diagrams, runbooks |
| **Jargon policy** | At most: NUBAN, KYC, ledger, wallet — always defined | Full implementation vocabulary |
| **Questions answered** | What did we build? Why? What does it do for people? What's next? | How does it work? Where is the code? How does it fail? How do I run it? |

Twin chapters cover the same domain back-to-back: read one, and the cross-link box at its end takes you to the other.

## Persona Reading Paths

### The Executive / Investor (≈ 60 minutes)
1. [Preface](f04-preface.md) — why this book exists
2. [Chapter 1: The Riverbrand Story](../chapters/ch01-riverbrand-story.md) — vision, market, product map
3. [Chapter 4: How Money Moves](../chapters/ch04-for-everyone-how-money-moves.md)
4. [Chapter 6: Wealth Building and WhatsApp Banking](../chapters/ch06-for-everyone-wealth-and-channels.md)
5. [Chapter 12: The Product Catalog](../chapters/ch12-for-everyone-product-catalog.md) — everything the bank can do
6. [Chapter 14: The Future of Autonomous Global Banking](../chapters/ch14-for-everyone-future-roadmap.md)
7. [Appendix E: Competitive Matrix](../appendices/app-e-competitive-matrix.md)

### The New Engineer (Days 1–30)
1. This page, then [Chapter 2: Learn, Unlearn, Relearn](../chapters/ch02-learn-unlearn-relearn.md)
2. [Chapter 3: Domain Primer](../chapters/ch03-domain-primer.md) — the language of the business
3. [Chapter 16: New Engineer Onboarding](../chapters/ch16-engineer-onboarding.md) — from zero to first deploy
4. [Chapter 5: The Transaction Engine](../chapters/ch05-engineering-transaction-engine.md) — the heart of the system
5. [Chapter 11: Developer and Operations Manual](../chapters/ch11-engineering-operations-manual.md)
6. [Chapter 13: The Service Catalog](../chapters/ch13-engineering-service-catalog.md) — where every capability lives
7. [Appendix I: 30-Day Onboarding Checklist](../appendices/app-i-onboarding-checklist.md)

### The Operations / SRE Engineer
1. [Chapter 10: How the Bank Stays Online](../chapters/ch10-for-everyone-reliability.md) (the business framing)
2. [Chapter 11: Developer and Operations Manual](../chapters/ch11-engineering-operations-manual.md) — jobs, metrics, runbooks
3. [Appendix D: API and Endpoint Reference](../appendices/app-d-api-reference.md)
4. [Chapter 15: The Upgrade Roadmap](../chapters/ch15-engineering-roadmap.md) — what is changing next

### The Auditor / Compliance Officer
1. [Chapter 8: Safety, Privacy, and Compliance](../chapters/ch08-for-everyone-safety-and-compliance.md)
2. [Chapter 9: Security Architecture](../chapters/ch09-engineering-security-architecture.md)
3. [Chapter 3, §3.4–3.5](../chapters/ch03-domain-primer.md) — KYC tiers and the data map
4. [Appendix C: Data Dictionary](../appendices/app-c-data-dictionary.md)

### The Product Manager
1. [Chapter 1: The Riverbrand Story](../chapters/ch01-riverbrand-story.md)
2. [Chapter 4](../chapters/ch04-for-everyone-how-money-moves.md) and [Chapter 6](../chapters/ch06-for-everyone-wealth-and-channels.md) (non-technical twins)
3. [Chapter 12: The Product Catalog](../chapters/ch12-for-everyone-product-catalog.md)
4. [Chapter 14: The Future](../chapters/ch14-for-everyone-future-roadmap.md)
5. [Appendix B: FAQ](../appendices/app-b-faq.md)

## Conventions Used in This Book

- **Recap block** — three lines at the top of every chapter (Unlearn / Learn / Relearn).
- **In Plain Words** sidebars — everyday chapters pause for a one-paragraph translation of the hard part.
- **Cross-link boxes** — the end of every chapter points to its twin track.
- **UNVERIFIED badge** — fact pending confirmation against the RiverbrandBE codebase.
- **§-references** — every claim about another part of the book links to it (`see §5.4`).
- **Figures** — every diagram is numbered and listed in the [List of Figures](f07-list-of-figures.md).
