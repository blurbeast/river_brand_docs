# Appendix B: Frequently Asked Questions

This appendix collects the twenty questions this book gets asked most, sorted by who is asking. The first group is for leaders, investors, and product owners — plain language, with links to the chapters that carry the full story. The second is for engineers joining the codebase — mechanism and file names, with links into the technical chapters. Every answer is two to four sentences on purpose; the links are where you go for depth. If your question is not here, the [glossary](app-a-glossary.md) and the chapter recaps are the next best place to look.

## For Leaders

These ten questions are the ones that come up in board rooms, diligence sessions, and first customer meetings. The answers are deliberately short enough to say out loud.

### What exactly is the Riverbrand Banking System?

Riverbrand is a digital banking platform — one ledger-first banking engine (RiverbrandBE) behind three doors: the mobile and web apps, WhatsApp chat, and partner payment rails. It serves everyday money journeys across five currencies: receiving income, paying bills, sending money, saving with yield, and holding balances in more than one currency. Customers meet it as a bank; your team runs it as one carefully bounded codebase. The full product map is in [§1.3](../chapters/ch01-riverbrand-story.md#13-what-riverbrand-is-the-product-map).

### How is Riverbrand different from a traditional core banking system?

Traditional cores grew up around branch batch processing and tend to treat a balance as a number that gets edited; Riverbrand records every movement as balanced double-entry history first, and derives balances from that history. It is also built conversation-first — most customers meet the bank inside WhatsApp rather than inside an app store download — and every external dependency (messaging, cards, SMS, mail) sits behind a swappable interface instead of being hard-wired to one vendor. The practical difference is that questions like "why is this balance what it is?" become queries over records rather than arguments over state. The problem it is answering is described in [§1.2](../chapters/ch01-riverbrand-story.md#12-the-problem-with-core-banking-today), and the customer-side picture of money movement is [Chapter 4](../chapters/ch04-for-everyone-how-money-moves.md).

### Is customer money safe here?

The design goal is that money moves exactly once, is always traceable to a reference, and is never silently editable — enforced by one-movement-at-a-time locking per wallet, idempotent references, and an immutable ledger ([§4.2](../chapters/ch04-for-everyone-how-money-moves.md#42-the-bank-vault-airlock), [§5.1](../chapters/ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard)). Customer access is protected by revocable sessions, device-separated credentials, and hashed payment secrets, and every sensitive action is written to a permanent audit record ([Chapter 8](../chapters/ch08-for-everyone-safety-and-compliance.md)). No system can promise perfection; this one is designed to make loss hard to cause and hard to hide — the honest framing of what it does and does not promise is in [§1.5](../chapters/ch01-riverbrand-story.md#15-success-metrics-honestly-stated).

### What happens if a payment or messaging provider fails?

Banking continues on the rails and adapters that are still healthy: the WhatsApp layer resolves one provider from six supported vendors at a time, so switching vendors is a configuration change rather than a rewrite, and every outbound message travels through a retry queue that parks failures for replay instead of dropping them. Inbound deposit provisioning itself has a fallback path from Providus to Fincra ([§5.5](../chapters/ch05-engineering-transaction-engine.md#55-virtual-nuban-lifecycle)). Customers notice a delayed receipt at worst, not a lost transfer, because the movement is already committed before any vendor is contacted ([§5.4](../chapters/ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue)). The business-side story of a provider stumble is [§6.4](../chapters/ch06-for-everyone-wealth-and-channels.md#64-when-a-provider-fails), and the multi-vendor design is [§7.2](../chapters/ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory).

### What are the limits on what a customer can do?

Limits follow KYC ("know your customer") tiers, which are regulatory, not arbitrary: phone-verified customers move up to ₦50,000 a day with a ₦300,000 wallet ceiling, identity-verified (BVN or NIN) up to ₦200,000 a day and ₦500,000 held, and fully verified up to ₦5,000,000 a day and above. Money that arrives above a customer's current ceiling is not frozen or bounced — the allowed part lands at once and the excess waits in a visible holding account until the customer upgrades ([§3.4](../chapters/ch03-domain-primer.md#34-kyc-tiers-and-limits), [§4.4](../chapters/ch04-for-everyone-how-money-moves.md#44-the-quarantined-balance)). The ladder is deliberately climbable: each step is one identity check, and each step raises the ceiling ([§8.3](../chapters/ch08-for-everyone-safety-and-compliance.md#83-what-a-kyc-tier-means-for-a-customer)).

### What does it cost to run this platform?

The architecture is deliberately lean for its capability set: a modular monolith rather than dozens of microservices, a connection pooler (PgBouncer) that the engineering notes credit with reducing active database memory usage from 50 GB to under 500 MB under high load, and read traffic split away from writes ([§11.2](../chapters/ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation)). The same stack runs entirely on a developer laptop — PostgreSQL, Redis, Mailpit, and the API in four containers — which is also a good proxy for how small a production footprint can start ([§11.1](../chapters/ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose)). Actual spend depends on transaction volume, region, and redundancy choices, so treat those as levers rather than a fixed price list; what scales expensively later is already scoped as a roadmap item rather than hidden in [Chapter 15](../chapters/ch15-engineering-roadmap.md).

### What is coming next for the platform?

The roadmap moves in three horizons: pan-African and cross-border rails, open banking and banking-as-a-service partnerships, and progressively more automation on top of the existing engine ([§14.5](../chapters/ch14-for-everyone-future-roadmap.md#145-three-strategic-horizons)). On the engineering side, the near-term upgrades are an event backbone, geo-distributed SQL, Kubernetes and GitOps, and richer observability ([Chapter 15](../chapters/ch15-engineering-roadmap.md)). Importantly, these are additive: the ledger-first core and the provider-agnostic channel layer are the parts the roadmap builds on rather than replaces. The customer-visible version of the same future is [Chapter 14](../chapters/ch14-for-everyone-future-roadmap.md).

### Who is Riverbrand for?

It is built for people underserved by branch-era banking: salary earners and small-business owners who live on their phones, savers who want disciplined yield products, and customers who hold or receive money in more than one currency. The WhatsApp door matters most here — a chat bank serves customers whose devices or data budgets make a full app a poor fit, and it is open around the clock ([§6.3](../chapters/ch06-for-everyone-wealth-and-channels.md#63-banking-in-a-chat-window)). The five journeys and the personas behind them are in [§1.3](../chapters/ch01-riverbrand-story.md#13-what-riverbrand-is-the-product-map), and everything the bank can do for them is listed in [Chapter 12](../chapters/ch12-for-everyone-product-catalog.md).

### How does compliance actually work day to day?

Three mechanisms run continuously rather than as periodic reviews: KYC tier ceilings enforced at transaction time, surplus deposits quarantined until identity is verified, and a permanent audit record of every sensitive action by customers and staff ([§8.4](../chapters/ch08-for-everyone-safety-and-compliance.md#84-the-audit-trail)). Staff powers are split into roles so no single person can both create and approve a privileged action ([§9.4](../chapters/ch09-engineering-security-architecture.md#94-role-based-access-control)). Daily reconciliation jobs then compare the internal books against external clearing statements, so discrepancies surface as operational alerts rather than as surprises at audit time ([§11.3](../chapters/ch11-engineering-operations-manual.md#113-the-background-jobs-fleet)). The governance posture and its limits are stated honestly in [§8.5](../chapters/ch08-for-everyone-safety-and-compliance.md#85-regulatory-posture-and-governance).

### How do I explain this to a board in five minutes?

Lead with the problem — core banking failures are usually double-counting, double-spending, frozen funds, and lost receipts — then show that Riverbrand answers each with one mechanism: ledger-first recording, per-wallet locking, the holding tank, and the guaranteed-courier notification queue, all described in [Chapter 4](../chapters/ch04-for-everyone-how-money-moves.md). Then show the honest metrics in [§1.5](../chapters/ch01-riverbrand-story.md#15-success-metrics-honestly-stated) and the market positioning in the [competitive matrix](app-e-competitive-matrix.md#the-master-matrix). Close with the three horizons from [§14.5](../chapters/ch14-for-everyone-future-roadmap.md#145-three-strategic-horizons), because boards buy direction as much as current state. If asked "what could go wrong", answer with the failure-mode honesty of [§5.7](../chapters/ch05-engineering-transaction-engine.md#57-failure-mode-matrix) rather than reassurance — it plays better in the room.

## For Engineers

These ten questions are the ones new hires ask in their first two weeks. Each answer names the file or section to open next.

### Where do I start as a new engineer?

Start with [Chapter 16](../chapters/ch16-engineer-onboarding.md) — day-one environment, the mental model, and the two traces you will re-walk yourself. Then tick off [Appendix I](app-i-onboarding-checklist.md) day by day; it is the same path in checkbox form, with a definition of "onboarded" at the end.

### How do transfers stay consistent when requests collide?

A Redis Redlock mutex serializes movements per wallet — one at a time, with a fast refusal for the loser — and inside that lock a single database transaction moves balances, writes balanced journal lines, and queues the notification event as one commit ([§5.1](../chapters/ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard), [§5.2](../chapters/ch05-engineering-transaction-engine.md#52-the-immutable-double-entry-ledger)). Retries are absorbed by idempotency references in `rbp_brand_references`, so a timeout-and-retry cannot move money twice ([§5.3](../chapters/ch05-engineering-transaction-engine.md#53-idempotency-references)). There is deliberately no state where the wallet moved but the ledger did not — the commit is the only moment of truth. The failure-mode matrix is [§5.7](../chapters/ch05-engineering-transaction-engine.md#57-failure-mode-matrix).

### How are user sessions revoked?

Tokens carry a version claim (`jv`) checked against the sidecar table `river_brand_sys_user_session_control`; a password reset, PIN reset, or sign-out increments `jwt_version`, and every outstanding token fails its next request instantly ([§9.2](../chapters/ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch)). Client types are also isolated — mobile and web present different access tokens — so one leaked credential is contained to one door ([§9.1](../chapters/ch09-engineering-security-architecture.md#91-dual-token-client-isolation)). If a user reports "it says my token has been revoked", that version check is what happened, and re-login issues a token with the current `jv` claim ([§11.6](../chapters/ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook)).

### How do I add a new WhatsApp provider?

Implement the five-method `IWhatsAppProvider` contract — signature verification, webhook parsing, text, interactive buttons, interactive lists — and register the adapter with `WhatsAppProviderFactory` so the environment variable can select it ([§7.2](../chapters/ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory)). Nothing downstream changes, because everything is written against the normalized message shape ([§13.7](../chapters/ch13-engineering-service-catalog.md#137-communication-whatsapp-and-messaging-services)). Fill the new provider's credentials per the environment catalog in [§11.1](../chapters/ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose), and verify the webhook signature path with a deliberately wrong secret before you trust it ([§11.5](../chapters/ch11-engineering-operations-manual.md#115-whatsapp-webhook-debugging)).

### How do I run the whole platform locally?

Install Node 20, npm 10, Docker with Compose, Prisma CLI and psql; then `npm install`, create `.env`, run `npm run docker:up`, `npm run prisma:push`, and check `/health/liveness` and `/health/readiness` on port 8010 ([§11.1](../chapters/ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose)). The stack brings up PostgreSQL 15, Redis 7, Mailpit on port 8026, and the API on 8010, and the guided version of the same morning is [§16.1](../chapters/ch16-engineer-onboarding.md#161-day-one-environment). For real provider webhooks on a laptop, put `ngrok http 8010` in front and register the tunnel ([§11.5](../chapters/ch11-engineering-operations-manual.md#115-whatsapp-webhook-debugging)).

### Where are the database tables defined?

The column-level reference is [Appendix C](app-c-data-dictionary.md), and the map of schema prefixes — `rbp_brand_*` for current-brand tables, `user_user`, `savings_*` and others flagged as legacy names — is [§3.5](../chapters/ch03-domain-primer.md#35-the-schema-prefix-map). Prisma owns the schema in code; `npm run prisma:push` applies it and `npx prisma generate` refreshes the typed client ([§11.1](../chapters/ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose)). Do not invent new tables on the legacy prefixes — the map exists so new work lands on `rbp_brand_*`.

### How do background jobs get scheduled?

A fleet starts with the server: `OutboxJob` is triggered by PostgreSQL `LISTEN/NOTIFY` with a safety cron sweep and claims rows with `FOR UPDATE SKIP LOCKED`, `DlqJob` runs every 15 minutes, and `SavingsJob`, `ReconciliationJob`, `BillReconciliationJob`, `ArchivalJob`, and `GeneralLedgerJob` run on daily schedules ([§11.3](../chapters/ch11-engineering-operations-manual.md#113-the-background-jobs-fleet)). Each job has exactly one owner service and one set of tables, so "who moved my money at midnight" is answerable from the job table alone. The customer-visible meaning of that fleet is [§10.2](../chapters/ch10-for-everyone-reliability.md#102-jobs-that-run-while-you-sleep).

### What happens when Redis goes down?

Redis holds the wallet locks, rate-limit buckets, conversation sessions, and the active token blacklist, so money movement refuses to run without its lock rather than proceeding unguarded — transfers pause with explicit errors instead of corrupting balances ([§5.1](../chapters/ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard)). Readiness checks turn red while the dependency is unavailable, and the recovery steps — including cleaning up stale lock keys in dev — are in the runbooks ([§11.6](../chapters/ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook)). The wider failure table, including what each guard does when its backing store is missing, is [§5.7](../chapters/ch05-engineering-transaction-engine.md#57-failure-mode-matrix).

### How do I add a new biller or bill type?

Start from `BillPaymentService` (`src/services/monetary/transaction/BillPaymentService.ts`), which validates the customer's meter or card number before any wallet debit, and add the vendor's confirmation path to `BillReconciliationJob` so failed purchases are refunded automatically ([§13.4](../chapters/ch13-engineering-service-catalog.md#134-payment-and-transaction-services), [§11.3](../chapters/ch11-engineering-operations-manual.md#113-the-background-jobs-fleet)). If the biller should also sell in WhatsApp, the conversational side lives in `WhatsAppBillPaymentHandler` under the chat step handlers ([§13.7](../chapters/ch13-engineering-service-catalog.md#137-communication-whatsapp-and-messaging-services)). Give every purchase its own idempotency reference in the standard format so vendor retries stay harmless ([§5.3](../chapters/ch05-engineering-transaction-engine.md#53-idempotency-references)).

### Where is the API reference?

While the stack is up, Swagger UI is at `http://localhost:8010/documentation`, Scalar at `/reference`, and the raw OpenAPI spec at `/documentation/json` ([§11.2](../chapters/ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation)). The curated endpoint reference that does not require a running stack is [Appendix D](app-d-api-reference.md). New engineers should treat the live Swagger as the source of truth for request shapes, because it is generated from the same schemas the server validates against.
