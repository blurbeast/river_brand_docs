# Chapter 16 — New Engineer Onboarding: From Zero to First Deploy

> *Unlearn the naive implementation you would write first. Learn the failure modes and race conditions that break it. Relearn the architecture Riverbrand ships instead.*

## Recap

- **Unlearn:** "Clone the repo, find the entry point, ship a feature" — and the banking implementation you would write first: a balance column, a read, a subtraction, an update.
- **Learn:** What that first implementation loses under real traffic: double-spends, duplicated credits from retried webhooks, sessions that cannot be revoked, one vendor's outage taking down a channel, and regulatory ceilings you cannot enforce after the fact.
- **Relearn:** The RiverbrandBE shape — request → guards → service → ledger — and the two traces you will run this week (one transfer, one WhatsApp session) that show every guard doing its job on the way to your first deploy.

## 16.1 Day-One Environment

Welcome. If you are reading this on a laptop that has never seen this codebase, this section is the only thing that matters today: get the full banking stack running locally with every health check green. The rest of the chapter can wait until tomorrow.

You need five tools, and only five. Everything else — PostgreSQL, Redis, an SMTP inbox, the API itself — arrives in containers.

| Tool | Version | Why it is here |
| :--- | :--- | :--- |
| Node.js | v20.x LTS or higher | The runtime for the Fastify API server |
| npm | v10+ | Package management and the project script aliases |
| Docker Engine and Docker Compose | v24+ / v2.20+ | The one-command local stack: Postgres, Redis, Mailpit, API |
| Prisma CLI and psql | v5.x / PostgreSQL client v15 | Schema push, client generation, and direct database inspection |
| Git | v2.40+ | Version control for RiverbrandBE |

Clone the repository, enter the project root, and install dependencies:

```bash
npm install
```

Next comes `.env`, the master environment file in the project root. Do not copy secrets from a shared document or from production; create a local file and fill it from your team's secret store. The complete catalog — every variable, what it controls, and which provider issues it — lives in [§11.1](ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose), and you should read that section rather than trusting any abbreviated list here. On day one, you need five groups: server port and stage, database and Redis connection strings, the dual-token authorization secrets, local SMTP (Mailpit), and the WhatsApp provider block. A minimal starting point looks like this:

```env
PORT=8010
NODE_ENV=development
APP_STAGE=DEV
DATABASE_URL="postgresql://riverbrand:riverbrand_secret_2026@postgres:5432/riverbank_prod_db?schema=public"
REDIS_URL="redis://redis:6379"
WHATSAPP_PROVIDER="meta"
```

Then bring the stack up and confirm what is actually running:

```bash
npm run docker:up
docker compose ps
```

You should see four containers up: `postgres:15-alpine`, `redis:7-alpine`, `mailpit`, and the API image. Push the Prisma schema to the database and generate the typed client:

```bash
npm run prisma:push
npx prisma generate
```

Now the two health checks that define "green". Liveness is a fast loop check; readiness deep-pings the real dependencies — PostgreSQL, Redis, and SMTP:

```bash
curl -i http://localhost:8010/health/liveness
curl -i http://localhost:8010/health/readiness
```

While those run, learn the four ports you will use every day. The full port table is in [§11.2](ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation).

| Port | What lives there |
| :--- | :--- |
| `8010` | The Fastify API, Swagger UI at `/documentation`, Scalar reference at `/reference` |
| `8026` | Mailpit's web inbox — every email the dev stack "sends" is captured here (SMTP listens on `1025`) |
| `6432` | PgBouncer, the PostgreSQL connection pooler |
| `9095` | Prometheus metrics at `/metrics` — deliberately off the public API port |

Finish with a type check: `npx tsc --noEmit`. If it exits cleanly and readiness returns `200`, your day-one environment is done. When something refuses to start — a `P1001` database error, a stuck lock, a 403 from a webhook — do not debug alone at 2 a.m.; the troubleshooting playbook in [§11.6](ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook) already names the four most common failures and their fixes.

**Figure 16.1 — The onboarding path.**

```mermaid
graph TD
  A["Day 1: local stack up, health checks green"] --> B["Mental model: request to controller to service to ledger"]
  B --> C["Trace one transfer end to end"]
  C --> D["Trace one WhatsApp session"]
  D --> E["Service map: where to change what"]
  E --> F["End of week 1: a small change shipped and demoed"]
```

That path is the rest of this chapter. It is deliberately short: one mental model, two traces, one routing table, one checklist. By the end you should be able to point at any screen a customer sees and name the three services and two tables underneath it.

## 16.2 The Thirty-Thousand-Foot Mental Model

Before the code, the shape. Every request that touches money walks the same corridor: **request → controller → service → ledger**. Controllers validate HTTP — Ajv schemas, headers, route parameters. Services hold the business rules, wired together with TypeDI constructor injection so each one is testable in isolation. And the ledger — the double-entry book at the center of the system — records the outcome as balanced journal lines, never as a bare number changing in place. If you remember one sentence from day one, make it that one: **a balance is a consequence of ledger entries, not a primitive you edit.** The primer in [§3.1](ch03-domain-primer.md#31-double-entry-in-plain-words) explains why, and [§5.2](ch05-engineering-transaction-engine.md#52-the-immutable-double-entry-ledger) shows the tables.

Three doors lead into the corridor:

1. **Mobile and web clients over the REST API.** Client types are deliberately isolated: native mobile presents `x-local-access-token`, web and admin present `x-web-access-token` (or `x-access-token` plus a `x-client-type` header). One leaked key is damage at one door, not every door — see [§9.1](ch09-engineering-security-architecture.md#91-dual-token-client-isolation).
2. **WhatsApp conversations.** Business solution providers deliver chat messages as webhooks to `POST /whatsapp/webhook` on port 8010; provider adapters normalize them before any banking logic runs. That channel has its own trace in [§16.4](#164-trace-one-whatsapp-session).
3. **Partner webhooks.** Providus and Fincra report inbound deposits to dedicated virtual accounts, Flutterwave reports card events, and bill vendors confirm purchases. Every one of these is a message that may arrive twice, which is why idempotency is a guard and not an afterthought.

And there are four core guards standing between a request and the ledger. Learn their names now; the rest of the book teaches their mechanisms:

| Guard | What it stops | Where it lives |
| :--- | :--- | :--- |
| **The concurrency guard** — a Redis Redlock mutex on `lock:wallet:{walletId}` followed by one single-commit database transaction | Two movements of the same money running side by side | [§5.1](ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard) |
| **Idempotency references** — a unique reference per operation, checked against `rbp_brand_references` before work is redone | The same event being counted twice after a retry | [§5.3](ch05-engineering-transaction-engine.md#53-idempotency-references) |
| **Session and client isolation** — dual tokens plus the sidecar `jwt_version` kill-switch in `river_brand_sys_user_session_control` | A revoked or stolen session that keeps working | [§9.2](ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch) |
| **Regulatory ceilings** — daily velocity tracking and the pending-balance holding tank | Inbound money above a customer's KYC tier being lost or frozen | [§5.6](ch05-engineering-transaction-engine.md#56-the-pending-balance-holding-tank-and-kyc-ceilings) |

One more habit to build early: after the ledger commits, nothing external is called inside the request. Notifications — WhatsApp receipts, push alerts, emails — leave through the transactional outbox (`rbp_brand_outbox`), a relay worker delivers them, and anything that keeps failing lands in the dead-letter table (`rbp_brand_deadletter`) for replay. That is why a slow email provider never blocks a finished transfer; the pattern is taught in [§5.4](ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue) and the analogies live in [Appendix F](../appendices/app-f-analogy-atlas.md).

## 16.3 Trace One Transfer End to End

This is the centerpiece of your first week. Take one concrete movement and follow it all the way through. Chidi sends **₦25,000** from his NGN wallet to his sister Amina's account at another bank. The system issues reference `TRF-NGN-20260815-88392011` before anything moves. The same engine runs whether the request came from the mobile app or from a WhatsApp chat; we will trace the REST path here and the chat path in [§16.4](#164-trace-one-whatsapp-session).

1. **The request arrives at the Fastify server on port 8010.** The payload carries the debit shape the monetary engine expects — user, amount, currency, an idempotency key, and the destination (the full payload interface is documented in the transaction-engine chapter). Ajv validates the schema before any handler body runs.
2. **Client and HMAC authentication.** The client type header selects the right door ([§9.1](ch09-engineering-security-architecture.md#91-dual-token-client-isolation)); a bad signature ends here with `401 Unauthorized`.
3. **Rate limiting.** A Redis token bucket absorbs bursts; an exhausted bucket returns `429 Too Many Requests` before the database is touched.
4. **Sidecar session check.** The JWT carries a `jv` claim; the auth middleware compares it against the current `jwt_version` in `river_brand_sys_user_session_control` (cached in Redis). If Chidi reset his password this morning, any token from yesterday fails here with `401` — the kill-switch of [§9.2](ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch).
5. **Tier 1 — the distributed lock.** The engine acquires `lock:wallet:{walletId}` in Redis with a short time-to-live (documented as 5 seconds in the architecture notes and 10 seconds in the engine notes — treat it as "seconds, and released in a `finally` block"). If another movement holds the lock — say, Chidi double-tapped on a slow connection — the second request is refused immediately with `409 Conflict`. No queueing at the database, no interleaved writes. See [§5.1](ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard).
6. **Tier 2 — one single-commit transaction.** Inside `prisma.$transaction`, in order: the idempotency service checks `rbp_brand_references` for `TRF-NGN-20260815-88392011`; the daily-limit tracker consults `rbp_brand_daily_limit_tracker` against Chidi's KYC tier; the engine verifies `balance >= amount + fee`; it decrements the source `Wallet` row; it credits the destination; `GeneralLedgerService` writes the balanced `GLJournalEntry` and `GLJournalLine` pair; and an event row is inserted into `rbp_brand_outbox` with status `PENDING`. Then — and only then — the transaction commits. There is no state in which the wallet moved but the ledger did not.
7. **The lock is released** in the `finally` block, and Chidi gets `200 OK` with the reference number. The movement he sees as "done" is now immutable history in `Transaction` / `payment_transaction` and the journal lines.
8. **The outbox relay delivers the receipts.** `OutboxJob` is woken by PostgreSQL `LISTEN/NOTIFY` (with a safety cron sweep) and claims pending rows in batches using `FOR UPDATE SKIP LOCKED`. It sends the WhatsApp receipt card, the FCM push (`sys_device_tokens`), and the email. If a downstream provider fails, delivery retries with backoff; after repeated failures the row moves to `rbp_brand_deadletter`, where `DlqJob` sweeps it every 15 minutes for replay or operator attention. The jobs fleet is catalogued in [§11.3](ch11-engineering-operations-manual.md#113-the-background-jobs-fleet).
9. **Reconciliation closes the loop.** The daily `ReconciliationJob` compares internal transactions against commercial clearing settlement statements and flags mismatches for operators; `GeneralLedgerJob` snapshots the journal so assets equal liabilities plus equity is provable every morning.

**Figure 16.2 — One transfer through the guards, the ledger, and the outbox.**

```mermaid
sequenceDiagram
    autonumber
    actor C as Chidi (client)
    participant API as Fastify API (8010)
    participant R as Redis
    participant DB as PostgreSQL (via PgBouncer)
    participant P as Interbank rail (Providus / Fincra)
    participant O as OutboxJob relay

    C->>API: Transfer request (idempotency key TRF-NGN-...)
    API->>API: Dual-token auth, rate limit, sidecar jwt_version
    API->>R: Acquire lock:wallet:{walletId}
    alt Lock busy
        R-->>API: Lock rejected
        API-->>C: 409 Conflict
    else Lock acquired
        API->>DB: Single-commit transaction
        Note over DB: Idempotency check, daily-limit check,<br/>wallet debit and credit, double-entry<br/>GLJournalEntry and GLJournalLine,<br/>insert rbp_brand_outbox PENDING
        DB-->>API: COMMIT
        API->>R: Release lock
        API-->>C: 200 OK with reference
        API->>P: Push the interbank payout
        O->>DB: Claim PENDING outbox rows
        O->>C: Receipt via WhatsApp, push, and email
    end
```

When you trace this yourself in a debugger or a log line, pay attention to the boundaries — what happens before the lock, what happens inside the commit, and what happens strictly after the `200 OK`. Those boundaries are where every money bug in this system is allowed or prevented. The failure modes you will meet in practice are already catalogued:

| Failure | What the system does | Where it is taught |
| :--- | :--- | :--- |
| A second tap while the first movement is running | `409 Conflict` — one movement at a time per wallet | [§5.1](ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard) |
| The client retries after a timeout | The same reference is recognised; the work is not redone | [§5.3](ch05-engineering-transaction-engine.md#53-idempotency-references) |
| Insufficient balance | The debit is refused before any ledger write | [§5.1](ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard) |
| Receipt provider is down | The outbox retries with backoff, then dead-letters the event for replay | [§5.4](ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue) |
| The interbank rail is slow or returns a mismatch | The internal record stands on its reference; `ReconciliationJob` flags the mismatch against clearing statements | [§11.3](ch11-engineering-operations-manual.md#113-the-background-jobs-fleet) |
| Chidi's session was revoked mid-morning | The next request fails the `jv` check with `401` | [§9.2](ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch) |

The full failure-mode matrix lives in [§5.7](ch05-engineering-transaction-engine.md#57-failure-mode-matrix). Read it once this week even if nothing is on fire; it is the cheapest way to learn what the guards are for.

## 16.4 Trace One WhatsApp Session

The second trace is the channel most customers actually use. Amina opens WhatsApp, sends "Menu" to the bank's number, and within a few seconds she is navigating interactive buttons toward a transfer. Here is what happens in between.

1. **The message enters as a webhook.** The active business solution provider — Meta Graph API by default, or Twilio, Termii, WATI, Interakt, or 360dialog — POSTs to `POST /whatsapp/webhook` on port 8010. Locally you expose that port with `ngrok http 8010` and register the tunnel URL plus your verify token in the provider dashboard; the full procedure is in [§11.5](ch11-engineering-operations-manual.md#115-whatsapp-webhook-debugging).
2. **Signature verification first.** Before the body is trusted, the provider adapter's `verifyWebhookSignature` checks the SHA-256 HMAC (`x-hub-signature-256` for Meta, `X-Twilio-Signature` for Twilio) against the app secret in your `.env`. A mismatch is `403` — the webhook is dropped, not processed.
3. **The provider factory picks the adapter.** `WhatsAppProviderFactory` resolves the implementation named by `WHATSAPP_PROVIDER` in the environment catalog ([§11.1](ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose)) and asks it to `parseIncomingWebhook` into one normalized `IIncomingMessage`. Everything downstream is written against that contract, which is why switching providers is an environment change rather than a rewrite ([§7.2](ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory)).
4. **`WhatsAppBankingService.handleIncomingMessage` runs the ingestion pipeline.** It deduplicates message IDs (webhook retries are normal; marker keys `wa:msg:*` remember a delivery for 24 hours), checks the brute-force lockout flag (`wa:lockout:*`), maps the sender's phone number to a `user_user` account, recognises global navigation keywords (`HI`, `MENU`, `CANCEL`, `RESET`), and dispatches the input to the registered step handler for the current conversation state.
5. **Session state decides what the input means.** `WhatsAppSessionService` keeps the conversation in Redis under `wa:session:{phone}` with a rolling TTL (documented as 15 minutes in the architecture notes and 30 minutes in the service catalog — **UNVERIFIED**: confirm the current value in `WhatsAppSessionService` before you rely on it). The state machine is strict: `IDLE` → `MAIN_MENU` → `TRANSFER_SELECT_BANK` → `TRANSFER_ENTER_ACCOUNT` → `TRANSFER_ENTER_AMOUNT` → `TRANSFER_ENTER_PIN` → `TRANSFER_PROCESSING` → back to `MAIN_MENU`. Because state lives in Redis and not in process memory, a server restart or a horizontal scale-out does not lose an in-flight chat ([§7.3](ch07-engineering-channel-fabric.md#73-the-conversation-state-machine)).
6. **The domain handler executes the business step.** For a transfer, `WhatsAppTransferHandler` walks the remaining steps — account entry, live recipient-name resolution, wallet selection across NGN, USD, EUR, and GBP, and PIN authorization. PINs are stored hashed, and three failed attempts trigger the 30-minute lockout ([§9.3](ch09-engineering-security-architecture.md#93-pin-and-password-protection)).
7. **The money moves through the same engine as [§16.3](#163-trace-one-transfer-end-to-end).** Redlock, single commit, double-entry journal, outbox row — the chat channel is a different door into the same corridor. If you changed nothing else in your first month, internalize this: **channels never move money themselves; the monetary engine does.**
8. **The reply goes back out through the provider adapter.** `WhatsAppResponseService` renders the interactive buttons and the receipt card; `IWhatsAppProvider.sendInteractiveButtons` / `sendTextMessage` deliver them. The receipt also travels to FCM push and email via the outbox, so the notification matrix has a fallback for every channel ([§7.4](ch07-engineering-channel-fabric.md#74-push-notifications-and-the-notification-matrix)).

**Figure 16.3 — One WhatsApp message from webhook to ledger and back.**

```mermaid
graph TD
  A["Amina sends 'Menu' on WhatsApp"] --> B["BSP webhook POST /whatsapp/webhook on port 8010"]
  B --> C["Verify HMAC signature — reject on mismatch"]
  C --> D["WhatsAppProviderFactory resolves the active provider"]
  D --> E["Normalize to IIncomingMessage"]
  E --> F["WhatsAppBankingService.handleIncomingMessage"]
  F --> G{"Duplicate message ID?"}
  G -- yes --> H["Ignore the delivery"]
  G -- no --> I["Load or create session wa:session:{phone}"]
  I --> J["Dispatch to the domain step handler"]
  J --> K["Validate PIN and business rules"]
  K --> L["Monetary engine: lock, commit, ledger, outbox"]
  L --> M["Reply via IWhatsAppProvider — buttons and receipt card"]
```

To rehearse this without a phone, run the simulated chat suite: `npx ts-node scratch/test_whatsapp_banking.ts`. It walks the main menu, multi-currency balance inquiries, a conversational transfer with PIN authorization, an airtime top-up, and the brute-force PIN lockout. Then break something on purpose — set the wrong app secret and watch the webhook return 403 — and fix it using [§11.6](ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook). Debugging a real signature failure once, in dev, is worth more than reading about it twice.

## 16.5 The Service Map and Where to Change What

RiverbrandBE is a modular monolith with 39 catalogued domain services in seven categories. You will not read them all in week one, and you should not try. The useful skill is routing: given a change request, know which file to open first. The complete entries — methods, tables, external dependencies — live in [Chapter 13](ch13-engineering-service-catalog.md); the table below is the day-to-day cut. Start at the file, then read the chapter section before you type.

| If you need to change… | Start with | Then read |
| :--- | :--- | :--- |
| Sign-up, sign-in, password reset, token issuance | `AuthService` (`src/services/auth.ts`) | [§13.2](ch13-engineering-service-catalog.md#132-authentication-and-security-services) |
| OTP generation, delivery, or expiry | `OtpService` (`src/services/otp.ts`) | [§13.2](ch13-engineering-service-catalog.md#132-authentication-and-security-services) |
| Transaction PIN rules or lockouts | `PinService` (`src/services/monetary/pin/pin.ts`) | [§9.3](ch09-engineering-security-architecture.md#93-pin-and-password-protection) |
| Balances, currency conversion, wallet creation | `WalletService` (`src/services/monetary/wallet/wallet.ts`) | [§13.3](ch13-engineering-service-catalog.md#133-core-financial-and-wallet-engines) |
| The debit/credit core, fees, ledger movements | `FinancialEngine` (`src/services/monetary/financialEngine.ts`) | [§13.3](ch13-engineering-service-catalog.md#133-core-financial-and-wallet-engines) and [§5.1](ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard) |
| Transfers, statements, receipts | `TransactionService` (`src/services/monetary/transaction/transaction.ts`) | [§13.4](ch13-engineering-service-catalog.md#134-payment-and-transaction-services) |
| Airtime, data, electricity, cable bills | `BillPaymentService` (`src/services/monetary/transaction/BillPaymentService.ts`) | [§13.4](ch13-engineering-service-catalog.md#134-payment-and-transaction-services) |
| Card funding and Flutterwave webhooks | `FlutterwaveTransactionService` (`src/services/monetary/transaction/flutterwaveTransaction.ts`) | [§13.4](ch13-engineering-service-catalog.md#134-payment-and-transaction-services) |
| Inbound deposits and NUBAN provisioning | `ProvidusTransactionService` and `UserProvisioningService` (`src/services/userProvisioning.ts`) | [§5.5](ch05-engineering-transaction-engine.md#55-virtual-nuban-lifecycle) |
| Safelock, Target Savings, interest math | `SavingsService` (`src/services/monetary/savings/savings.ts`) and `SavingsJob` | [§7.1](ch07-engineering-channel-fabric.md#71-savingsjob-and-the-compounding-math) |
| KYC tiers, ceilings, pending-balance releases | `KycService` (`src/services/kyc.ts`), `PendingBalanceService`, `AdminKycService` | [§5.6](ch05-engineering-transaction-engine.md#56-the-pending-balance-holding-tank-and-kyc-ceilings) and [§13.6](ch13-engineering-service-catalog.md#136-kyc-verification-and-user-services) |
| WhatsApp menus, cards, receipt formatting | `WhatsAppResponseService` (`src/whatsapp-banking/services/WhatsAppResponseService.ts`) | [§13.7](ch13-engineering-service-catalog.md#137-communication-whatsapp-and-messaging-services) |
| A new WhatsApp provider adapter | New `IWhatsAppProvider` implementation plus `WhatsAppProviderFactory` (`src/whatsapp-banking/providers/WhatsAppProviderFactory.ts`) | [§7.2](ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory) |
| Conversational flows (transfer, airtime, KYC in chat) | The step handlers under `src/whatsapp-banking/services/handlers/` | [§13.7](ch13-engineering-service-catalog.md#137-communication-whatsapp-and-messaging-services) |
| Push notifications and device tokens | `PushNotificationService` and `DeviceTokenService` (`src/services/PushNotificationService.ts`) | [§7.4](ch07-engineering-channel-fabric.md#74-push-notifications-and-the-notification-matrix) |
| Background jobs and schedules | The job fleet under `src/job/` (`OutboxJob`, `DlqJob`, `SavingsJob`, `ReconciliationJob`, `BillReconciliationJob`, `ArchivalJob`, `GeneralLedgerJob`) | [§11.3](ch11-engineering-operations-manual.md#113-the-background-jobs-fleet) |
| Health, metrics, alerting | `HealthCheckService`, `MetricsService`, `AlertDispatcherService` | [§11.4](ch11-engineering-operations-manual.md#114-observability-and-metrics) |
| Session revocation and the kill-switch | `AuthService.signOut` and `river_brand_sys_user_session_control` | [§9.2](ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch) |
| Staff roles and permissions | `RoleService` and `PermissionService` (`src/services/RoleService.ts`) | [§9.4](ch09-engineering-security-architecture.md#94-role-based-access-control) |

Two conventions to internalise before your first pull request. First, service boundaries are real: controllers validate, services decide, the ledger records — if you find yourself writing business rules in a controller, stop and move them. Second, table prefixes are historical, not random: `rbp_brand_*` is the current brand prefix, while `user_user`, `savings_*`, and a few others are legacy names flagged for renaming. The canonical prefix map is [§3.5](ch03-domain-primer.md#35-the-schema-prefix-map), and the full column-level reference is [Appendix C](../appendices/app-c-data-dictionary.md).

## 16.6 First-Week Checklist

By the end of day five you should have run things, read things, and shipped something small. "Shipped" matters: a codebase you have never changed is a codebase you do not yet trust.

**Day 1 — environment.** Stack up, `docker compose ps` green, both health endpoints returning `200`, `npx tsc --noEmit` clean, and Swagger and Scalar open in two browser tabs ([§16.1](#161-day-one-environment), [§11.2](ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation)). Skim the [service catalog's reading guide](ch13-engineering-service-catalog.md#131-how-to-read-a-service-entry) so the entries make sense tomorrow.

**Day 2 — the money path.** Read [§3.1–§3.4](ch03-domain-primer.md#31-double-entry-in-plain-words) and [§5.1–§5.4](ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard). Then trace one transfer end to end with your own example amount ([§16.3](#163-trace-one-transfer-end-to-end)) — in a debugger, with log lines, or on paper. If you can narrate where the lock is acquired and what is true after the commit, day two is done.

**Day 3 — your corner of the map.** Read the [Chapter 13](ch13-engineering-service-catalog.md) entry for the service you are most likely to touch first, its tables in [Appendix C](../appendices/app-c-data-dictionary.md), and the failure modes in [§5.7](ch05-engineering-transaction-engine.md#57-failure-mode-matrix). Write down three questions for your onboarding buddy.

**Day 4 — the channel and the fire.** Run the WhatsApp test suite and trace one session ([§16.4](#164-trace-one-whatsapp-session)). Then break something deliberately in dev — a wrong webhook secret, a stale lock key — and recover it using the playbook in [§11.6](ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook).

**Day 5 — ship and teach.** Land one small change through the normal review path: a documentation fix, a missing test, a clearer log message in code you now understand. Then walk a teammate through the transfer trace from [§16.3](#163-trace-one-transfer-end-to-end) on a whiteboard, without notes. Teaching the trace is the fastest way to find the gaps in it.

Days 1–5 are the sprint. The full month — including the on-call shadow and the presentation to the team — is checklisted item by item in [Appendix I](../appendices/app-i-onboarding-checklist.md). Print it, tick it, and give it back to your manager at day 30.

## Key Takeaways

- Day one has one definition of done: the Docker stack up, Prisma pushed, and `/health/readiness` green on port 8010 — the full environment catalog is [§11.1](ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose), not a wiki page that drifts.
- Every money request walks the same corridor — request → controller → service → ledger — past four guards: the wallet lock plus single commit, idempotency references, the session kill-switch, and KYC ceilings.
- A transfer is finished at the commit, not at the HTTP response: the outbox delivers receipts afterwards, and the dead-letter queue catches what stumbles ([§5.4](ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue)).
- WhatsApp is a door, not a wing: webhooks are verified, normalized by the provider factory, and the conversation state machine hands real work to the same monetary engine the app uses.
- Before you open an editor, route the change: the table in [§16.5](#165-the-service-map-and-where-to-change-what) maps common requests to the service file and the chapter section that explains it.

## Frequently Asked Questions

### Do I need all six WhatsApp providers configured to work locally?

No. Set `WHATSAPP_PROVIDER` to one adapter — `meta` is the default in the environment catalog — and fill only that provider's credentials ([§11.1](ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose)). The factory resolves exactly one implementation at startup ([§7.2](ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory)), so the other five can stay empty until you need them.

### Which tables should I never edit by hand in dev?

Treat the ledger and the pipeline tables as append-only by habit: `GLJournalEntry`, `GLJournalLine`, `rbp_brand_outbox`, `rbp_brand_deadletter`, `rbp_brand_references`, and the audit tables. Manual edits there break the invariants the engine assumes; if you need to correct money, do it through a compensating movement, the way the reconciliation jobs expect ([§5.2](ch05-engineering-transaction-engine.md#52-the-immutable-double-entry-ledger), [§11.3](ch11-engineering-operations-manual.md#113-the-background-jobs-fleet)).

### What should I read first if I have never worked in fintech?

[Chapter 3](ch03-domain-primer.md) — double-entry, NUBANs, KYC tiers, and the schema map — before any code. The language of the business is the language of the tables, and [§2.3](ch02-learn-unlearn-relearn.md#23-what-engineers-relearn) is a short warm-up on the failure modes this industry actually loses money to.

### How do I get real provider webhooks onto my laptop?

Run `ngrok http 8010`, register the tunnel URL as the webhook callback in the provider dashboard, and use your local `WHATSAPP_VERIFY_TOKEN`. The steps, including the expected 403 signature failure and its fix, are in [§11.5](ch11-engineering-operations-manual.md#115-whatsapp-webhook-debugging).

### Where is the API reference for the endpoints I am about to call?

Swagger UI at `http://localhost:8010/documentation`, Scalar at `/reference`, and the raw OpenAPI spec at `/documentation/json` whenever the stack is up ([§11.2](ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation)). The curated endpoint reference is [Appendix D](../appendices/app-d-api-reference.md).

## Where to Go Next

*This chapter is shared by both tracks. Keep going with [Chapter 13 — Engineering: The Service Catalog](ch13-engineering-service-catalog.md) to learn where every capability lives, and [Chapter 11 — Engineering: Developer and Operations Manual](ch11-engineering-operations-manual.md) for ports, jobs, metrics, and runbooks. New engineers should then follow the persona path in [How to Read This Book](../front-matter/f05-how-to-read.md) and tick off [Appendix I](../appendices/app-i-onboarding-checklist.md) day by day.*
