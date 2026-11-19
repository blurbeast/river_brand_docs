# Appendix A: Glossary

Every term in the Riverbrand Knowledge Book, defined twice: once in plain words for any reader, once for engineers. Terms are listed alphabetically. Cross-references point into the chapters where the concept is taught at length.

### AutoSave

**In plain words:** A standing rule that quietly moves spare money from your everyday balance into a savings pool on a schedule, so saving happens without you deciding each time.

**For engineers:** AutoSave sweeps are periodic, rule-based transfers that move idle primary-wallet balances into high-yield savings pools (a `Target` record). They run from scheduled jobs rather than user-initiated requests; see [§6.1](../chapters/ch06-for-everyone-wealth-and-channels.md#61-safelock-target-savings-and-autosave-stories) and [§7.1](../chapters/ch07-engineering-channel-fabric.md#71-savingsjob-and-the-compounding-math).

### BaaS (Banking-as-a-Service)

**In plain words:** Banking offered as a building block other companies can embed inside their own apps — the way a shop might offer a branded account without building a bank.

**For engineers:** A multi-tenant, white-label platform in which partners receive their own apps, NUBAN generation, compliance, and fee configuration on Riverbrand's rails. BaaS is on the roadmap, not yet in production; see [§15.6](../chapters/ch15-engineering-roadmap.md#156-open-banking-passkeys-and-post-quantum-crypto).

### BSP (WhatsApp Business Solution Provider)

**In plain words:** One of the licensed middlemen that connects a business to WhatsApp so it can legally chat with customers at scale.

**For engineers:** Riverbrand speaks to WhatsApp through an `IWhatsAppProvider` factory implemented over Meta Graph API, Twilio, Termii, WATI, Interakt, and 360dialog; the active provider is chosen by environment variable with zero code change. See [§7.2](../chapters/ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory).

### BVN (Bank Verification Number)

**In plain words:** The single identity number that links you to your bank accounts across the whole Nigerian banking system.

**For engineers:** An 11-digit CBN-mandated identifier verified through the Dojah gateway; a confirmed BVN verification promotes a customer from TIER1 to TIER2 and releases quarantined funds. See [§3.2](../chapters/ch03-domain-primer.md#32-nuban-nip-nibss-bvn-and-nin).

### Dead-Letter Queue

**In plain words:** The waiting room for messages the system tried and failed to deliver too many times — nothing is thrown away, it is set aside for a human or a retry.

**For engineers:** The `rbp_brand_deadletter` table holds outbox records that exhausted their retry budget (exponential backoff, five attempts); `DlqJob` sweeps it on a cron, alerts operators, and supports replay. See [§5.4](../chapters/ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue).

### Double-Entry

**In plain words:** The centuries-old rule that every movement of money is written down twice — once where it left, once where it arrived — so the book always adds up.

**For engineers:** Each transfer writes a balanced pair of lines inside a `GLJournalEntry` (`GLJournalLine` debit and credit) via `GeneralLedgerService`, inside the same commit as the balance mutation; entries are immutable, corrections are reversing entries. See [§3.1](../chapters/ch03-domain-primer.md#31-double-entry-in-plain-words).

### Dual-Token Isolation

**In plain words:** Phone sessions and browser sessions use different keys, so a stolen web login cannot open the phone door and vice versa.

**For engineers:** The auth middleware requires mobile clients to present the local access token and web/admin clients the web access token (or a shared header plus an explicit client-type claim); production startup fatals if either secret is unset. See [§9.1](../chapters/ch09-engineering-security-architecture.md#91-dual-token-client-isolation).

### Escrow and KYC Quarantine

**In plain words:** Money held safely in a locked drawer against a condition — usually "prove who you are" — and released automatically once the condition is met.

**For engineers:** The quarantine side of this is `rbp_brand_pending_balance` (status `QUARANTINED`, audited in `rbp_brand_pending_balance_audit`): inbound funds exceeding the tier ceiling are held rather than bounced, and `KycTierUpgradedHandler` releases them on a tier promotion. See [§3.4](../chapters/ch03-domain-primer.md#34-kyc-tiers-and-limits).

### FAPI (Financial-grade API)

**In plain words:** A strict security rulebook for bank-grade app connections, written so third parties can plug in without weakening the bank's defences.

**For engineers:** The Financial-grade API (FAPI 1.0/2.0) profiles that the roadmap's open-banking REST/GraphQL hub is designed to comply with; this is future work, not current behaviour. See [§15.6](../chapters/ch15-engineering-roadmap.md#156-open-banking-passkeys-and-post-quantum-crypto).

### Fastify

**In plain words:** The web framework that answers every request the Riverbrand apps send — the front door of the banking engine.

**For engineers:** The Node.js HTTP framework (v4/v5) used by RiverbrandBE, with Ajv schema validation and OpenAPI/Scalar documentation; the API listens on port 8010 in the dev stack. See [§11.2](../chapters/ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation).

### FCM (Firebase Cloud Messaging)

**In plain words:** The push-notification service that puts Riverbrand alerts on a customer's phone screen.

**For engineers:** Push dispatch goes through the Firebase Admin SDK and per-device `DeviceToken` records, with self-healing invalidation when a device is uninstalled; notifications are emitted asynchronously from the outbox relay. See [§7.4](../chapters/ch07-engineering-channel-fabric.md#74-push-notifications-and-the-notification-matrix).

### FIDO2

**In plain words:** Logging in with your face, fingerprint, or a physical security key instead of a password or a short PIN.

**For engineers:** FIDO2/WebAuthn hardware-backed passkeys are planned as step-up and replacement authentication (alongside HSM-held signing keys) on the roadmap; today's transaction credentials are Argon2id passwords and bcrypt PINs. See [§15.6](../chapters/ch15-engineering-roadmap.md#156-open-banking-passkeys-and-post-quantum-crypto).

### FX (Foreign Exchange)

**In plain words:** Swapping one currency for another — naira to dollars, pounds to euros — at a rate the bank sets.

**For engineers:** Riverbrand holds per-currency wallets (NGN, USD, GBP, EUR, CAD) and executes in-app swaps at the active administrative rate stored in the `ExchangeRate` record, writing both legs as ledger entries. See [§3.3](../chapters/ch03-domain-primer.md#33-wallets-and-the-five-currencies).

### GL (General Ledger)

**In plain words:** The master book of the bank — the single record every payment, deposit, and fee ultimately shows up in.

**For engineers:** The double-entry ledger built from `GLJournalEntry` / `GLJournalLine`, snapshotted daily into `GLBalanceSnapshot` by `GeneralLedgerJob`, which validates that total assets equal liabilities plus equity. See [§3.1](../chapters/ch03-domain-primer.md#31-double-entry-in-plain-words).

### Idempotency

**In plain words:** Asking twice for the same thing and getting it done once — a repeated tap can never charge you twice.

**For engineers:** Every money movement carries a cryptographically generated reference (`IdempotencyService`, `rbp_brand_references`) checked before execution inside the guarded transaction; duplicates return the original result instead of re-debiting. See [§5.3](../chapters/ch05-engineering-transaction-engine.md#53-idempotency-references).

### KYC (Know Your Customer)

**In plain words:** The bank's process of proving who you are, which unlocks higher limits the more you prove.

**For engineers:** Tiered verification (TIER1 phone/email → TIER2 BVN or NIN via Dojah → TIER3 government ID and address) driving the ceilings in `rbp_brand_kyc_benefit` and the velocity counter `rbp_brand_daily_limit_tracker`. See [§3.4](../chapters/ch03-domain-primer.md#34-kyc-tiers-and-limits).

### Ledger

**In plain words:** The bank's never-erased notebook: every movement of money is a new line, and your balance is just what those lines add up to.

**For engineers:** An append-only journal of immutable entries; balances are derived summaries, corrected only by reversing entries, never by updates to history. See [§3.1](../chapters/ch03-domain-primer.md#31-double-entry-in-plain-words).

### NIBSS (Nigeria Inter-Bank Settlement System)

**In plain words:** The shared plumbing company behind instant bank-to-bank transfers in Nigeria.

**For engineers:** The infrastructure operator of the NIP rail and related interbank services that Riverbrand reaches through its settlement providers (Providus, Fincra, Flutterwave). See [§3.2](../chapters/ch03-domain-primer.md#32-nuban-nip-nibss-bvn-and-nin).

### NIN (National Identification Number)

**In plain words:** Your number in Nigeria's national identity register — the other accepted identity key alongside the BVN.

**For engineers:** A national identity identifier verified via Dojah; a successful NIN check promotes the KYC tier and triggers the pending-balance release path. See [§3.2](../chapters/ch03-domain-primer.md#32-nuban-nip-nibss-bvn-and-nin).

### NIP (NIBSS Instant Payments)

**In plain words:** The express lane that moves money between Nigerian banks in seconds rather than days.

**For engineers:** Nigeria's real-time interbank rail, operated by NIBSS, over which Providus/Fincra transfers clear; inbound NIP credits reach Riverbrand as provider webhooks and are then booked to the ledger. See [§3.2](../chapters/ch03-domain-primer.md#32-nuban-nip-nibss-bvn-and-nin).

### NUBAN (Nigeria Uniform Bank Account Number)

**In plain words:** A bank account number that belongs to just you, so anyone can pay you from any bank — the number Riverbrand hands every customer at signup.

**For engineers:** A dedicated virtual account provisioned per customer through ProvidusBank with Fincra as fallback, persisted in `userAccountDetails` with an `ACCOUNT_CREATION` reference in `rbp_brand_references`. See [§5.5](../chapters/ch05-engineering-transaction-engine.md#55-virtual-nuban-lifecycle).

### Outbox Pattern

**In plain words:** Writing down "tell the customer" at the exact same moment you move their money, then letting a background courier actually send the message.

**For engineers:** Transactional outbox: the business mutation and a `rbp_brand_outbox` row commit atomically; `OutboxJob` (LISTEN/NOTIFY plus a safety cron, `FOR UPDATE SKIP LOCKED` batch sweeps) dispatches notifications and marks rows published. See [§5.4](../chapters/ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue).

### PAPSS (Pan-African Payment and Settlement System)

**In plain words:** A planned continental payment switch so money can cross African borders in local currencies without round-tripping through dollars or euros.

**For engineers:** A roadmap rail integration joining NIP, SEPA/FPS, FedNow, and ISO 20022 in the cross-border settlement engine; not yet in production. See [§14.2](../chapters/ch14-for-everyone-future-roadmap.md#142-new-rails-pan-african-and-cross-border).

### Pending Balance Holding Tank

**In plain words:** The locked drawer where money that exceeds your current KYC limit waits safely until your identity catches up.

**For engineers:** `rbp_brand_pending_balance` (status `QUARANTINED`) holds the surplus above a tier ceiling while the allowed portion credits the wallet; `KycTierUpgradedHandler` atomically sweeps it on upgrade, with `rbp_brand_pending_balance_audit` for the trail. See [§5.6](../chapters/ch05-engineering-transaction-engine.md#56-the-pending-balance-holding-tank-and-kyc-ceilings).

### PgBouncer

**In plain words:** The doorman that lets thousands of conversations with the database happen over a handful of real connections.

**For engineers:** PostgreSQL connection pooler in transaction mode on port 6432, multiplexing ~5,000 Fastify clients onto ~50 physical connections; configured via the pooled `DATABASE_URL`. See [§11.1](../chapters/ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose).

### Prisma

**In plain words:** The library that lets the banking code talk to the database without hand-writing every query.

**For engineers:** The ORM (5.x) over PostgreSQL 15 that RiverbrandBE uses for type-safe queries and migrations, extended with `@prisma/extension-read-replicas` for read routing; money mutations run inside interactive transactions. See [§5.1](../chapters/ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard).

### RBP

**In plain words:** The short name for the Riverbrand platform you will see stamped on the bank's own database tables — like a filing label on every cabinet.

**For engineers:** RBP is the namespace on Riverbrand domain tables (`rbp_brand_outbox`, `rbp_brand_kyc_benefit`, and so on); it is used as the product shorthand after first definition. The literal words behind the initials are **UNVERIFIED** against the codebase.

### Read Replica

**In plain words:** A live copy of the database used only for looking things up, so checking your balance never slows down someone else's transfer.

**For engineers:** PostgreSQL read-only mirrors routed via the Prisma read-replicas extension (`DATABASE_READ_REPLICA_URL_*`); writes go strictly to the primary, reads (balance checks, statements) to the replicas. See [§11.4](../chapters/ch11-engineering-operations-manual.md#114-observability-and-metrics).

### Reconciliation

**In plain words:** The nightly double-check that the bank's own notebook agrees with what the partner banks say happened.

**For engineers:** `ReconciliationJob` compares internal transaction logs against commercial clearing settlement statements (plus `BillReconciliationJob` for airtime/utility debits against vendor responses, with automated refunds), surfacing mismatches and missing webhooks. See [§10.2](../chapters/ch10-for-everyone-reliability.md#102-jobs-that-run-while-you-sleep).

### Redlock

**In plain words:** A single-serving token that lets only one transfer touch your wallet at a time, so a double-tap can never spend the same money twice.

**For engineers:** The Redis distributed-mutex algorithm used as tier 1 of the concurrency guard: `lock:wallet:{walletId}` with a short TTL, released in a `finally` block; a busy lock returns HTTP 409. See [§5.1](../chapters/ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard).

### RiverbrandBE

**In plain words:** The actual banking engine behind the apps and WhatsApp — the software this book documents.

**For engineers:** The Riverbrand Banking Engine codebase: a modular monolith on Node.js 20, Fastify, TypeScript, Prisma/PostgreSQL 15, and Redis 7, serving the mobile apps, web/admin console, and WhatsApp channel. See [Chapter 16](../chapters/ch16-engineer-onboarding.md).

### Safelock

**In plain words:** A fixed-deposit vault: you lock money away for a chosen number of days and earn interest you cannot accidentally spend.

**For engineers:** Funds are debited from `Wallet` into a `Target` record with `savingsType = SAFELOCK` for 30/90/180/365-day tenors; `SavingsJob` accrues interest (logged to `savings_usersavinginterestlog`), `SafelockMaturedHandler` pays out principal plus interest at maturity, and early breakage incurs a `breakage_rate` penalty and withdrawal tax. See [§6.1](../chapters/ch06-for-everyone-wealth-and-channels.md#61-safelock-target-savings-and-autosave-stories).

### SEPA (Single Euro Payments Area)

**In plain words:** The standard payment network that lets euros move across Europe as easily as a domestic transfer.

**For engineers:** A planned euro rail (with UK Faster Payments) for diaspora remittance corridors on the cross-border settlement roadmap. See [§14.2](../chapters/ch14-for-everyone-future-roadmap.md#142-new-rails-pan-african-and-cross-border).

### Settlement

**In plain words:** The moment when promised money actually becomes money in the right account at the right bank.

**For engineers:** Clearing and settlement across provider rails (Providus, Fincra, Flutterwave): inbound credits arrive as provider webhooks, and `ReconciliationJob` verifies internal books against the commercial settlement statements afterwards. See [§10.2](../chapters/ch10-for-everyone-reliability.md#102-jobs-that-run-while-you-sleep).

### Sidecar Session

**In plain words:** A kill-switch beside your account that can cancel every login everywhere the instant something looks wrong.

**For engineers:** The `river_brand_sys_user_session_control` table carries an atomic `jwt_version` (`jv`); password change, PIN reset, or logout increments it, and auth middleware rejects any token whose `payload.jv` is stale (Redis-cached, 15-second TTL). See [§9.2](../chapters/ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch).

### Target Savings

**In plain words:** A savings goal with a name — "school fees", "car deposit" — that fills up automatically on a schedule you choose.

**For engineers:** Scheduled daily/weekly/monthly debits toward a `Target` record driven by cron jobs, with maturity handling alongside Safelock and AutoSave sweeps. See [§6.1](../chapters/ch06-for-everyone-wealth-and-channels.md#61-safelock-target-savings-and-autosave-stories).

### Wallet

**In plain words:** One of your money boxes — one per currency — holding the balance you can spend right now.

**For engineers:** The per-currency balance container (`Wallet`) for NGN, USD, GBP, EUR, or CAD; balances are mutated only inside the guarded transaction and always mirrored by double-entry ledger lines. See [§3.3](../chapters/ch03-domain-primer.md#33-wallets-and-the-five-currencies).
