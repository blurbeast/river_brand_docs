# Chapter 11 — Engineering: Developer and Operations Manual

> *Unlearn the naive implementation you would write first. Learn the failure modes and race conditions that break it. Relearn the architecture Riverbrand ships instead.*

## Recap

- **Unlearn:** The idea that running a bank backend locally means installing Postgres, Redis, and a mail server by hand, and that operations is what happens after the code ships.
- **Learn:** The failure modes that actually bite in production — connection storms at payday, provider outages mid-transfer, stuck locks, poisoned webhooks, revoked sessions — and the operational discipline each one demands.
- **Relearn:** Riverbrand's answer: a one-command containerised stack, a fixed port and health contract, an autonomous fleet of background jobs, an internal observability plane, and runbooks written before the incident, not during it.

This chapter is the working manual for engineers and SREs operating RiverbrandBE: how to bring the stack up, what listens where, what runs while you sleep at the process level, how to watch it, how to debug the WhatsApp webhook path, and what to do when a page fires. The business framing of the same ground is [Chapter 10](ch10-for-everyone-reliability.md); the mechanisms specified here are cross-referenced to their home chapters rather than re-specified.

## 11.1 Prerequisites, Environment, and Docker Compose

**Prerequisites.** The local stack is containerised, so the host toolchain is deliberately short. The versions below are the documented baseline for RiverbrandBE:

| Tool | Version | Role |
| :--- | :--- | :--- |
| Node.js | v20.x LTS or higher | Application runtime |
| npm | v10+ | Package management and script runner |
| Docker Engine | v24+ | Container runtime |
| Docker Compose | v2.20+ | Stack orchestration |
| Prisma CLI | v5.x | Schema push/pull and client generation |
| psql (PostgreSQL client) | v15 | Direct database inspection |
| Git | v2.40+ | Version control |

Install dependencies from the repository root with `npm install`. New engineers should also read [§16.1](ch16-engineer-onboarding.md#161-day-one-environment) for the day-one environment walkthrough; this section is the reference, that one is the guided tour.

**The environment catalog.** All configuration enters through a single `.env` file at the repository root. The full catalog, as documented:

```env
# Server Port & Environment Mode
PORT=8010
NODE_ENV=development
APP_STAGE=DEV

# Database Connections & PgBouncer
DATABASE_URL="postgresql://riverbrand:riverbrand_secret_2026@postgres:5432/riverbank_prod_db?schema=public"
REDIS_URL="redis://redis:6379"

# Dual-Token Authorization Secrets
LOCAL_ACCESS_TOKEN="local-dev-secret-token"
WEB_ACCESS_TOKEN="web-dev-secret-token"
JWT_SECRET="riverbrand-jwt-secret-key-2026"

# Email SMTP Delivery (Mailpit Dev Server)
SMTP_HOST=mailpit
SMTP_PORT=1025
MP_SMTP_AUTH_ALLOW_INSECURE=1

# Firebase Admin Push Credentials
FIREBASE_PROJECT_ID="riverbrand-d806f"
FIREBASE_CLIENT_EMAIL="firebase-adminsdk-fbsvc@riverbrand-d806f.iam.gserviceaccount.com"
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# Third-Party Gateway API Credentials
DOJAH_API_KEY="prod_dojah_api_key_here"
DOJAH_APP_ID="prod_dojah_app_id_here"
PROVIDUS_CLIENT_ID="providus_client_id_here"
FINCRA_SECRET_KEY="fincra_secret_key_here"
FLUTTERWAVE_SECRET_KEY="FLWSECK_TEST-xxx-X"
TERMII_API_KEY="termii_api_key_here"

# WhatsApp Multi-Provider Configuration
WHATSAPP_PROVIDER="meta" # Options: meta, twilio, termii, wati, interakt, 360dialog
WHATSAPP_PHONE_NUMBER_ID="109283746592019"
WHATSAPP_ACCESS_TOKEN="EAAxxxxxx"
WHATSAPP_VERIFY_TOKEN="riverbrand_secure_webhook_verify_token_2026"
WHATSAPP_APP_SECRET="fb_app_secret_hash_here"

# Twilio WhatsApp Credentials (If provider is twilio)
TWILIO_ACCOUNT_SID="ACxxxxxx"
TWILIO_AUTH_TOKEN="tw_auth_token_here"
TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"

# Termii WhatsApp Credentials (If provider is termii)
TERMII_WHATSAPP_DEVICE_ID="termii_device_id_here"
```

Notes on the non-obvious entries. `LOCAL_ACCESS_TOKEN` and `WEB_ACCESS_TOKEN` are the dual-token authorization secrets: the mobile channel and the web console present different tokens by design, so one leaked channel token is not a key to the other door ([§9.1](ch09-engineering-security-architecture.md#91-dual-token-client-isolation)). `DOJAH_*` drives identity verification (KYC tier upgrades), `PROVIDUS_CLIENT_ID` and `FINCRA_SECRET_KEY` cover the two settlement partners for virtual NUBAN provisioning — primary and fallback ([§5.5](ch05-engineering-transaction-engine.md#55-virtual-nuban-lifecycle)) — and `FLUTTERWAVE_SECRET_KEY` plus `TERMII_API_KEY` cover bill purchase and SMS/WhatsApp gateways. The `WHATSAPP_PROVIDER` switch selects the active engine behind the `IWhatsAppProvider` factory: `meta`, `twilio`, `termii`, `wati`, `interakt`, or `360dialog` ([§7.2](ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory)); the Twilio and Termii blocks are required only when their engine is selected. In development, Mailpit captures all outbound mail on SMTP port 1025 with `MP_SMTP_AUTH_ALLOW_INSECURE=1`.

**Database URLs: direct versus pooled.** The catalog above shows the direct development URL. In production, `DATABASE_URL` points at PgBouncer rather than at PostgreSQL itself — the pooling contract is specified in [§11.2](#112-ports-health-and-api-documentation):

```env
# Connection String via PgBouncer Pooler (Transaction Mode)
DATABASE_URL="postgresql://riverbrand:secret@pgbouncer:6432/riverbank_prod_db?schema=public&pgbouncer=true&connection_limit=50"
```

Read queries are split from writes through Prisma read replicas (`@prisma/extension-read-replicas`, `DATABASE_READ_REPLICA_URL_1` / `_2`): balance checks and statements route to replica mirrors, while transfers and deposits commit strictly to the primary master.

**Docker Compose.** Two entry points exist. The development script starts the full local stack (PostgreSQL, Redis, Mailpit, Fastify API):

```bash
# Start Docker Container Stack (Postgres, Redis, Mailpit, Fastify API)
npm run docker:up

# Alternatively, run Production Docker Compose Stack
docker compose -f docker-compose.prod.yml up --build -d

# Verify Container Status
docker compose ps
```

Expected shape of `docker compose ps`:

```
NAME                    IMAGE                       STATUS         PORTS
riverbank_postgres_1    postgres:15-alpine          Up (healthy)   0.0.0.0:5432->5432/tcp
riverbank_redis_1       redis:7-alpine              Up (healthy)   0.0.0.0:6379->6379/tcp
riverbank_mailpit_1     axllent/mailpit             Up             0.0.0.0:1025->1025/tcp, 0.0.0.0:8026->8025/tcp
riverbank_api_1         riverbrand-backend:latest   Up             0.0.0.0:8010->8010/tcp
```

![Figure 11.1](../images/fig-ch11-docker-stack.svg)

**Figure 11.1 — The Docker Compose stack.** Postgres, Redis, Mailpit, and the Fastify API as one orchestrated unit, with health-checked dependencies and the port map below.

**Prisma lifecycle.** Schema changes are applied and the client regenerated with:

```bash
# Push Prisma Schema to PostgreSQL Database
npm run prisma:push

# Generate Type-Safe Prisma Client Artifacts
npx prisma generate

# Pull Live Database Schema Updates (Reverse Engineering)
npm run prisma:pull
```

`prisma:push` is the local-parity path (no migration files to review); `prisma:pull` reverse-engineers a live schema into the client. Before committing code, run the strict type check: `npx tsc --noEmit`.

## 11.2 Ports, Health, and API Documentation

Every process in the stack has a fixed port and a documented surface. The map below is the operational contract — the values the runbooks, probes, and dashboards assume.

| Surface | Port / URL | Purpose |
| :--- | :--- | :--- |
| Fastify API | `8010` | The banking engine's HTTP surface |
| Swagger UI | `http://localhost:8010/documentation` | Interactive OpenAPI 3.0 route testing |
| Scalar reference | `http://localhost:8010/reference` | Modern interactive API reference |
| Raw OpenAPI JSON | `http://localhost:8010/documentation/json` | Complete OpenAPI 3.0 specification |
| WhatsApp webhook | `POST http://localhost:8010/whatsapp/webhook` | Incoming Meta/Twilio message receiver |
| Liveness probe | `GET http://localhost:8010/health/liveness` | Fast process-alive check, returns `200 OK` |
| Readiness probe | `GET http://localhost:8010/health/readiness` | Deep dependency ping (Postgres, Redis, Mailpit) |
| Mailpit UI | `http://localhost:8026` | Visual inbox capturing all outgoing dev mail |
| Prometheus metrics | `http://localhost:9095/metrics` | Internal telemetry scrape endpoint |
| PgBouncer | `6432` | Transaction-mode pooler in front of PostgreSQL |
| PostgreSQL | `5432` | Primary database (behind PgBouncer in production) |
| Redis | `6379` | Locks, conversation state, and cache |

Quick verification with the stack up:

```bash
# Liveness Check
curl -i http://localhost:8010/health/liveness

# Readiness Check (Pings Postgres, Redis, Mailpit)
curl -i http://localhost:8010/health/readiness
```

The two probes answer different questions and must not be conflated. **Liveness** is the cheap loop check: is the process up and serving at all? A failing liveness probe means restart the container. **Readiness** is the expensive one: it actively pings PostgreSQL, Redis, PgBouncer, and the SMTP path (Mailpit in development) and returns non-200 while any dependency is unreachable. A failing readiness probe with passing liveness means *the service is awake but not fit for traffic* — leave it out of the rotation and fix the dependency (see [§11.6](#116-runbooks-and-troubleshooting-playbook), Runbook F).

**The PgBouncer tower.** Port 6432 is the control tower in front of the database: thousands of Fastify client sockets are held gracefully while their queries are multiplexed over a pool of 50 physical PostgreSQL connections in **transaction-pooling mode** (`pool_mode = transaction`), meaning a pooled connection is held only for the duration of one transaction and then handed to the next client. The plain-language telling of this — including where the analogy bends — is the airport tower in [Appendix F, §F.4](../appendices/app-f-analogy-atlas.md#f4-the-airport-control-tower-pgbouncer-multiplexing); the customer-facing consequence is [§10.1](ch10-for-everyone-reliability.md#101-the-airport-tower-view). The engineering record measures the database memory footprint under load at roughly a tenth of un-pooled demand (an estimated 50 GB of idle connections collapsing to well under 500 MB), and read queries routed to replica mirrors keep roughly 85% of read-only work off the write path.

![Figure 11.2](../images/fig-ch11-pgbouncer-tower.svg)

**Figure 11.2 — The PgBouncer tower.** Up to 5,000 client connections held in the sky, landed one transaction at a time onto 50 pooled database connections on port 6432.

One operational consequence deserves emphasis: because pooling is per-transaction, a long-running transaction can hold a pooled connection far longer than a quick one. Long analytical queries and ad-hoc `psql` sessions opened against the pooler are a self-inflicted runway blockage — point them at the replica, or accept that they queue ordinary traffic behind them.

**API documentation is live, not maintained.** The Swagger UI at `/documentation` and the Scalar reference at `/reference` render from the same OpenAPI 3.0 spec the Fastify routes generate, so a route added in code appears in the docs without a documentation step. The full endpoint inventory lives in [Appendix D: API and Endpoint Reference](../appendices/app-d-api-reference.md); the service-by-service catalog is [Chapter 13](ch13-engineering-service-catalog.md).

## 11.3 The Background Jobs Fleet

RiverbrandBE initialises an autonomous suite of scheduled workers and system guards on server startup. This fleet is the operational half of the reliability story told for everyone in [§10.2](ch10-for-everyone-reliability.md#102-jobs-that-run-while-you-sleep); below is the mechanism inventory, with the schedules the code actually registers.

| Worker | Schedule / Trigger | Responsibility |
| :--- | :--- | :--- |
| **`OutboxJob`** | PostgreSQL `LISTEN/NOTIFY` + safety cron (`*/5 * * * * *`) | Processes pending outbox events immediately on database commit; batch sweeps use `FOR UPDATE SKIP LOCKED` so multiple workers never claim the same row. |
| **`DlqJob`** | Scheduled cron (`*/15 * * * *`) | Sweeps dead-letter records (`rbp_brand_deadletter`) exceeding max retries, alerts operators, and enables automated replay. |
| **`SavingsJob`** | Daily at midnight (`0 0 * * *`) | Calculates and accrues daily compounding interest on active Safelock fixed deposits into `savings_usersavinginterestlog`. |
| **`ReconciliationJob`** | Daily automated sweep | Reconciles internal transactions against commercial bank clearing settlement statements, surfacing mismatched records. |
| **`BillReconciliationJob`** | Daily automated sweep | Reconciles airtime, electricity, and cable TV purchases against vendor aggregator responses; initiates automated refunds for failed bills. |
| **`ArchivalJob`** | Daily at midnight (`0 0 * * *`) | Archives and prunes processed outbox and audit events older than 3 days, keeping primary relational tables lean. |
| **`GeneralLedgerJob`** | Daily snapshot | Snapshots all double-entry general ledger accounts into `GLBalanceSnapshot`. |
| **`startMemoryGuard`** | Continuous interval | Monitors Node.js V8 heap and RSS memory consumption; triggers graceful worker recycling past thresholds. |

**The outbox path in detail.** The courier story of [Appendix F, §F.2](../appendices/app-f-analogy-atlas.md#f2-the-guaranteed-postal-courier-the-transactional-outbox-and-dead-letter-queue) has a precise mechanical shape here (the full specification is [§5.4](ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue)):

1. A financial operation — transfer, deposit, bill payment — inserts a message row into `rbp_brand_outbox` **inside the same single-commit database transaction** as the wallet debit/credit. The message cannot exist without the transfer, and the transfer cannot commit without its message.
2. The commit emits a PostgreSQL `NOTIFY`, which wakes `OutboxJob` immediately; the `*/5` second safety cron picks up anything the notification missed (crashed listeners, restored replicas).
3. `OutboxJob` sweeps pending rows in batches with `FOR UPDATE SKIP LOCKED` — the row-level claim that lets concurrent workers divide a backlog without double-sending.
4. Delivery calls the downstream provider (email gateway, Firebase FCM push, WhatsApp engine). Failures retry with exponential backoff. After **5 failed attempts**, the record moves to `rbp_brand_deadletter`.
5. `DlqJob` sweeps the dead-letter table every 15 minutes, alerts on stranded records, and replays them once the provider recovers. Nothing silently disappears; everything is either delivered or visibly stranded.

**Figure 11.3 — Outbox dispatch and dead-letter fallback.**

```mermaid
sequenceDiagram
    participant H as Fastify handler
    participant DB as PostgreSQL
    participant O as OutboxJob
    participant P as Provider (mail/FCM/WhatsApp)
    participant D as DlqJob

    H->>DB: Single-commit transaction: wallet move + outbox row (PENDING)
    DB-->>O: LISTEN/NOTIFY wake-up (safety cron every 5s)
    O->>DB: Batch claim FOR UPDATE SKIP LOCKED
    O->>P: Dispatch notification
    P-->>O: Failure
    Note over O: Retry with backoff, up to 5 attempts
    O->>DB: Move to rbp_brand_deadletter
    D->>DB: Sweep every 15 min, alert operators
    D->>P: Replay once provider recovers
```

Two operational habits follow. First, **watch the backlog gauge** (`outbox_pending_events_count`, [§11.4](#114-observability-and-metrics)): a queue that grows for more than a few minutes is a provider problem or a worker problem, and it is visible long before customers complain. Second, **never "fix" a stuck transfer by re-running it** — idempotency references ([§5.3](ch05-engineering-transaction-engine.md#53-idempotency-references)) exist precisely so retries are safe, but the correct lever is replaying the *message*, not the *money movement*.

**Where the other workers fit.** `SavingsJob` is the compounding engine whose arithmetic is specified in [§7.1](ch07-engineering-channel-fabric.md#71-savingsjob-and-the-compounding-math). `ReconciliationJob` and `BillReconciliationJob` are the daily truth-checks against partner banks and bill vendors — the operational close-out that ends every provider incident ([§10.4](ch10-for-everyone-reliability.md#104-an-incident-story)). `GeneralLedgerJob` produces the immutable daily snapshot auditors query ([§3.1](ch03-domain-primer.md#31-double-entry-in-plain-words)), and `ArchivalJob` is what keeps those queries fast by moving processed rows out of the hot tables after three days. The service catalog entry for the platform and job layer is [§13.8](ch13-engineering-service-catalog.md).

## 11.4 Observability and Metrics

Observability is deliberately **not** mounted on the public API. The architecture exposes Prometheus telemetry from an isolated metrics server (`src/services/metrics/metricsServer.ts`) on its own internal port, **9095**, and keeps the health suite (`src/services/health/healthCheckService.ts`) on the API port as the two probes of [§11.2](#112-ports-health-and-api-documentation). The separation is a security decision, not an aesthetic one: queue lengths, database names, and request topology are reconnaissance material, and a public `/metrics` route hands them to anyone who asks.

**The metric set.** Four series carry most day-to-day operations:

| Metric | Type | What it answers |
| :--- | :--- | :--- |
| `http_requests_total` | Counter (by method, route, status) | Traffic shape and error ratio per endpoint |
| `http_request_duration_seconds` | Histogram (p50, p90, p99) | Latency percentiles — the p99 is the customer's worst second |
| `financial_transactions_total` | Counter (by currency, status) | Transaction volume and failure rate per currency |
| `outbox_pending_events_count` | Gauge | Real-time depth of the notification backlog |

**What to alert on.** The design intent is proactive paging before degradation is customer-visible:

- **Outbox backlog growth** — `outbox_pending_events_count` climbing for more than one sweep interval means dispatch is failing; check provider status and worker liveness before it becomes a receipt complaint ([§11.3](#113-the-background-jobs-fleet)).
- **Error-ratio spikes** — a step change in `http_requests_total` with 5xx status codes usually names a failing dependency; correlate with readiness probe results ([Runbook F](#runbook-f-readiness-probe-failing-while-liveness-passes)).
- **Latency tail movement** — p99 rising while p50 is flat is a classic signature of connection-pool saturation at the PgBouncer tower ([§11.2](#112-ports-health-and-api-documentation)) or a slow downstream provider, not "the database got slower."
- **Dead-letter arrivals** — any growth in `rbp_brand_deadletter` is an alert in its own right; those are messages that exhausted their retries and need a human.

**Health diagnostics in code terms.** `/health/liveness` is a fast loop check returning `200 OK` as long as the process serves; `/health/readiness` performs active deep pings against PostgreSQL, Redis, PgBouncer, and SMTP and fails closed while any dependency is unreachable. Container health checks in the Compose stack (`Up (healthy)` in `docker compose ps`) wrap the same idea at the orchestration layer.

**Verification commands worth memorising:**

```bash
# Type-level verification of a change
npx tsc --noEmit

# Probe checks
curl -i http://localhost:8010/health/liveness
curl -i http://localhost:8010/health/readiness

# Scrape the internal metrics plane
curl -s http://localhost:9095/metrics | head
```

The roadmap direction here is OpenTelemetry distributed tracing — W3C trace-context propagation across Fastify handlers, PgBouncer queries, Redis operations, and outbound HTTP — which is planned engineering work ([§15.4](ch15-engineering-roadmap.md#154-opentelemetry-and-observability)), not current product. Until then, the four series above plus the probe pair are the observability contract.

## 11.5 WhatsApp Webhook Debugging

The WhatsApp channel is the one surface where a provider on the public internet calls *into* the stack, so local development needs a tunnel and a signature discipline. The consumer is `POST /whatsapp/webhook` on port 8010; the engine behind it is selected by `WHATSAPP_PROVIDER` and hidden behind the `IWhatsAppProvider` factory (`meta`, `twilio`, `termii`, `wati`, `interakt`, `360dialog` — [§7.2](ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory)).

**Tunneling with ngrok.** To receive real webhooks from the Meta Graph API or Twilio on a local machine:

```bash
ngrok http 8010
```

Then configure the provider dashboard:

- **Callback URL:** `https://<your-ngrok-subdomain>.ngrok-free.app/whatsapp/webhook`
- **Verify Token:** must equal `WHATSAPP_VERIFY_TOKEN` from `.env` (the documented dev value is `riverbrand_secure_webhook_verify_token_2026`)

**Figure 11.4 — Inbound webhook path.**

```mermaid
sequenceDiagram
    participant P as Provider (Meta / Twilio / Termii)
    participant T as ngrok tunnel
    participant W as POST /whatsapp/webhook
    participant V as Signature check
    participant F as IWhatsAppProvider factory
    participant S as Redis conversation state

    P->>T: HTTPS webhook delivery
    T->>W: Forward to Fastify :8010
    W->>V: HMAC verify (WHATSAPP_APP_SECRET / TWILIO_AUTH_TOKEN)
    V-->>W: 403 on mismatch (see Runbook C)
    W->>F: Route by WHATSAPP_PROVIDER
    F->>S: Read/update conversation state machine
    F-->>P: Reply via selected engine
```

**Signature verification is the first gate.** Meta deliveries are validated with an HMAC signature over the raw body using `WHATSAPP_APP_SECRET`; Twilio deliveries are validated against `TWILIO_AUTH_TOKEN`. A mismatch is an immediate `403 Forbidden` — the failure mode in [Runbook C](#runbook-c-webhook-403-invalid-signature). Never debug a 403 by disabling verification; fix the secret.

**The automated test suite.** The end-to-end simulated chat runner exercises the channel without a provider:

```bash
npx ts-node scratch/test_whatsapp_banking.ts
```

It covers the flows most likely to regress: main menu greeting and button rendering; balance inquiries across NGN, USD, EUR, and GBP; the conversational interbank transfer flow with PIN authorization; airtime top-up with network resolution; and brute-force PIN lockout after 3 failed attempts. Run it after any change to the conversation state machine ([§7.3](ch07-engineering-channel-fabric.md)) or the provider factory.

**The Twilio Studio flow template.** When the Twilio engine is in play, a visual Studio flow can be deployed directly onto the webhook rails:

```bash
node scripts/create-twilio-flow-template.js
```

**Debugging order that saves time.** (1) Is the tunnel live and the callback URL exact — including `/whatsapp/webhook`? (2) Does the verify token match `WHATSAPP_VERIFY_TOKEN`? (3) Does the signature secret match the provider dashboard? (4) Is `WHATSAPP_PROVIDER` set to the engine you think you are testing? (5) Is conversation state stale in Redis for the test phone number — a half-finished state machine will answer a new "hi" with the wrong menu. The state machine's own failure modes are catalogued in [§5.7](ch05-engineering-transaction-engine.md#57-failure-mode-matrix).

## 11.6 Runbooks and Troubleshooting Playbook

Four production failure cases dominate the operational record, and each has been expanded below into a runbook with the same four beats — **Symptom / Diagnosis / Fix / Prevention**. Two further runbooks cover the queue and probe failures that the observability plane of [§11.4](#114-observability-and-metrics) surfaces before customers do. The playbook index:

| # | Symptom | First look | Runbook |
| :--- | :--- | :--- | :--- |
| A | `PrismaClientInitializationError: Can't reach database server` | Docker container state | [Runbook A](#runbook-a-database-connection-refused-p1001) |
| B | `HTTP 409 Conflict` / `RedlockError` lock timeout | Redis lock keys | [Runbook B](#runbook-b-redis-lock-timeout-redlockerror) |
| C | `HTTP 403 Forbidden: Invalid HMAC signature` on webhook | Provider secrets in `.env` | [Runbook C](#runbook-c-webhook-403-invalid-signature) |
| D | `401 Unauthorized: Token has been revoked or has invalid version` | Session version sidecar | [Runbook D](#runbook-d-401-after-session-version-bump) |
| E | Outbox backlog growing / dead-letter arrivals | Provider + worker health | [Runbook E](#runbook-e-outbox-backlog-and-dead-letter-growth) |
| F | Readiness probe failing while liveness passes | Dependency containers | [Runbook F](#runbook-f-readiness-probe-failing-while-liveness-passes) |

### Runbook A: Database Connection Refused (P1001)

- **Symptom.** `PrismaClientInitializationError: Can't reach database server at postgres:5432` (Prisma error `P1001`). API requests fail at startup or mid-run; readiness probe is red.
- **Diagnosis.** The PostgreSQL container is not running or is restarting. Confirm with `docker compose ps` — the `riverbank_postgres_1` row should read `Up (healthy)`. If the stack is production-shaped, also confirm PgBouncer on 6432 is up, since `DATABASE_URL` may point at the pooler rather than at Postgres directly ([§11.2](#112-ports-health-and-api-documentation)).
- **Fix.** Restart the container and re-probe:

  ```bash
  docker compose restart postgres
  curl -i http://localhost:8010/health/readiness
  ```
- **Prevention.** Keep the Compose health checks enabled so `Up (unhealthy)` is visible before clients notice; never point local tooling at the production database URL; alert on readiness-probe failures rather than waiting for request errors.

### Runbook B: Redis Lock Timeout (RedlockError)

- **Symptom.** `HTTP 409 Conflict: A transaction is already in progress on this account`, or `RedlockError` in the logs. A customer's transfer is refused because the per-wallet distributed lock — the first tier of the two-tier concurrency guard ([§5.1](ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard)) — is still held.
- **Diagnosis.** Decide whether this is *contention* (two genuine taps in flight; the 409 is correct and self-clearing) or a *stale lock* (a worker died mid-transaction and left the key behind). Inspect live lock keys:

  ```bash
  docker exec -it riverbank_redis_1 redis-cli KEYS "lock:wallet:*"
  ```
- **Fix.** For contention: do nothing — the lock releases after the transaction commits and the customer retries safely. For a confirmed stale lock in development, delete the specific key (never flush the whole keyspace):

  ```bash
  docker exec -it riverbank_redis_1 redis-cli DEL "lock:wallet:123"
  ```
- **Prevention.** The lock carries a ten-second safety timeout, so a crashed server's lock expires on its own; correctness in that case rests entirely on tier two — the single-commit database transaction. If stale locks recur, look for handlers that hold the lock across slow external calls; external I/O belongs in the outbox ([§5.4](ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue)), not inside the lock window.

### Runbook C: Webhook 403 Invalid Signature

- **Symptom.** `HTTP 403 Forbidden: Invalid HMAC signature` on `POST /whatsapp/webhook`. Messages from WhatsApp never reach the conversation state machine.
- **Diagnosis.** The provider's signature does not validate against the local secret. For the Meta engine, `WHATSAPP_APP_SECRET` in `.env` must match the App Secret in the Meta App Dashboard; for the Twilio engine, `TWILIO_AUTH_TOKEN` must match the console value ([§11.5](#115-whatsapp-webhook-debugging)). Also confirm the request is hitting the exact callback path behind the ngrok tunnel.
- **Fix.** Align the secret, restart the API process to reload `.env`, and replay a test message. Do not disable signature verification to "get it working" — the signature is the only thing proving the call came from the provider rather than from anyone who found the tunnel URL.
- **Prevention.** Treat provider secrets as environment-scoped: different values for dev, staging, and production; rotate on staff departure; store them in the deployment platform's secret store, not in a committed file. The dual-token and sidecar machinery that protects *customer* sessions is specified in [§9.2](ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch).

### Runbook D: 401 After Session Version Bump

- **Symptom.** `401 Unauthorized` with a message like `Token has been revoked or has invalid version`, typically right after the customer reset their password or PIN. The JWT itself is well-formed and unexpired — it is being refused anyway.
- **Diagnosis.** This is the kill-switch working as designed. The account's `jwt_version` in `river_brand_sys_user_session_control` was incremented at the moment of the reset (see the hotel-keycard story in [Appendix F, §F.3](../appendices/app-f-analogy-atlas.md#f3-the-electronic-hotel-master-keycard-sidecar-session-revocation)), and every token issued before the bump fails its version check. If a customer reports this *without* having reset anything, treat it as suspicious and escalate.
- **Fix.** Re-authenticate: `POST /auth/login` issues a fresh JWT carrying the updated `jv` claim. For an admin-triggered global logout, the same path applies to every device at once.
- **Prevention.** Never lengthen token lifetimes to paper over revocation complaints. Support scripts should check the session-control sidecar before assuming a corrupted token, and the mobile/web clients should surface "please log in again" rather than retrying a revoked token in a loop. The dual-token split ([§9.1](ch09-engineering-security-architecture.md#91-dual-token-client-isolation)) means a revoked mobile session is not a revoked web session — check which channel is complaining.

### Runbook E: Outbox Backlog and Dead-Letter Growth

- **Symptom.** `outbox_pending_events_count` climbing for minutes; rows appearing in `rbp_brand_deadletter`; customers reporting late receipts. Money movements themselves are completing — this is the decoupled side-effect path in trouble ([§11.3](#113-the-background-jobs-fleet)).
- **Diagnosis.** First, is `OutboxJob` alive and sweeping (look for `LISTEN/NOTIFY` wake-ups and the 5-second safety cron in logs)? Second, is a downstream provider erroring (email gateway, FCM, WhatsApp engine)? Dead-letter arrivals after 5 attempts usually name a provider that has been down longer than the retry budget.
- **Fix.** Restore the provider or switch the engine (`WHATSAPP_PROVIDER` can move traffic to another gateway — [§7.2](ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory)). Then replay: `DlqJob`'s sweep re-sends recovered messages every 15 minutes, and operators can force replay for a specific stranded envelope. Verify the backlog gauge drains.
- **Prevention.** Alert on backlog slope, not just backlog size. Keep receipt senders out of request handlers (they already are — via the outbox), and remember that at-least-once delivery means a replay can legitimately produce a duplicate receipt; make notification consumers idempotent and never route money through the replay path.

### Runbook F: Readiness Probe Failing While Liveness Passes

- **Symptom.** `GET /health/liveness` returns `200 OK` but `GET /health/readiness` returns non-200. The process is alive; the service is declaring itself unfit for traffic.
- **Diagnosis.** Readiness actively pings PostgreSQL, Redis, PgBouncer, and SMTP (Mailpit in dev) ([§11.2](#112-ports-health-and-api-documentation)). The failing dependency is named in the probe response. Check `docker compose ps` for `unhealthy` or restarting containers, and confirm port 6432 if the database URL is pooler-fronted.
- **Fix.** Fix the dependency (`docker compose restart <service>`), re-run readiness until green, and only then return the instance to rotation. If PostgreSQL is up but readiness still fails through PgBouncer, restart the pooler — its transaction-mode state can wedge while the database is healthy.
- **Prevention.** Wire readiness into the load balancer's health gate so unfit instances take no traffic; alert on readiness flapping (a dependency that blips every hour is a latent outage); and keep Mailpit/SMTP in the dev readiness set so a broken mail path is caught locally, not in production.

## Key Takeaways

- **The stack is one command, the config is one file.** `npm run docker:up` (or `docker compose -f docker-compose.prod.yml up --build -d`) brings up Postgres, Redis, Mailpit, and the API; the full `.env` catalog covers ports, dual-token secrets, SMTP, Firebase, and every third-party gateway key ([§11.1](#111-prerequisites-environment-and-docker-compose)).
- **Ports are the operational contract:** API 8010 (`/documentation`, `/reference`, `/whatsapp/webhook`, `/health/*`), Mailpit 8026, Prometheus 9095, PgBouncer 6432 — liveness says "awake," readiness says "fit for traffic" ([§11.2](#112-ports-health-and-api-documentation)).
- **The jobs fleet does the night shift at process level:** outbox dispatch on `LISTEN/NOTIFY` with `FOR UPDATE SKIP LOCKED` sweeps, dead-letter replay every 15 minutes, midnight interest and archival, daily reconciliation and ledger snapshots, and a continuous memory guard ([§11.3](#113-the-background-jobs-fleet)).
- **Observability is internal by design:** four Prometheus series on port 9095 plus the probe pair; alert on backlog slope, error ratio, p99 movement, and dead-letter arrivals ([§11.4](#114-observability-and-metrics)).
- **Webhook debugging has a fixed order:** tunnel, verify token, signature secret, provider engine, stale conversation state — with the test suite and the Twilio Studio builder as the fast feedback loop ([§11.5](#115-whatsapp-webhook-debugging)).
- **Six runbooks, four beats each (Symptom / Diagnosis / Fix / Prevention):** P1001, Redlock timeout, webhook 403, session-version 401s, outbox backlog, and readiness flapping ([§11.6](#116-runbooks-and-troubleshooting-playbook)).

## Frequently Asked Questions

### What is the minimum toolchain to run RiverbrandBE locally?

Node.js v20.x LTS+, npm v10+, Docker Engine v24+ with Docker Compose v2.20+, Prisma CLI v5.x, psql v15, and Git v2.40+. Everything else — PostgreSQL, Redis, Mailpit — runs in containers, so no manual database or mail-server installation is needed. The full prerequisite table and install sequence are in [§11.1](#111-prerequisites-environment-and-docker-compose), and the guided version for a first week is [§16.1](ch16-engineer-onboarding.md#161-day-one-environment).

### Why is the database URL different in production?

In development the app talks to PostgreSQL directly; in production `DATABASE_URL` points at PgBouncer on port 6432 in transaction-pooling mode, with `connection_limit=50`, so thousands of client sockets are multiplexed over 50 physical connections ([§11.2](#112-ports-health-and-api-documentation)). Read queries additionally fan out to Prisma read replicas. The plain-language version of why this matters at payday is [§10.1](ch10-for-everyone-reliability.md#101-the-airport-tower-view).

### A customer's receipt never arrived but the transfer succeeded. What now?

That split is by design: money moves in the single-commit transaction; the receipt is an outbox envelope delivered asynchronously. Check `outbox_pending_events_count` and `rbp_brand_deadletter`, then work [Runbook E](#runbook-e-outbox-backlog-and-dead-letter-growth). Do not re-run the transfer — replay the message. Idempotency references ([§5.3](ch05-engineering-transaction-engine.md#53-idempotency-references)) make retries safe, but the money movement has already committed correctly.

### Should I disable signature verification to test webhooks locally?

No. Run the ngrok tunnel and use the documented verify token and app secret instead ([§11.5](#115-whatsapp-webhook-debugging)), or use the simulated chat suite (`npx ts-node scratch/test_whatsapp_banking.ts`), which needs no provider at all. A bypassed verification path is the kind of "temporary" local hack that reaches production.

### How do I know whether a 401 is a bug or the kill-switch doing its job?

Check whether the account's session version was recently bumped — a password or PIN reset increments `jwt_version` in `river_brand_sys_user_session_control` and invalidates every previously issued token by design ([Runbook D](#runbook-d-401-after-session-version-bump)). If the customer reset their credentials, the 401 is correct: re-authenticate and move on. If they did not, escalate — unexpected revocation activity is a security signal, not a support nuisance.

## Where to Go Next

*For everyone, see [Chapter 10 — For Everyone: How the Bank Stays Online](ch10-for-everyone-reliability.md).* The analogies this chapter cites live in [Appendix F: Analogy Atlas](../appendices/app-f-analogy-atlas.md), and the endpoint inventory lives in [Appendix D: API and Endpoint Reference](../appendices/app-d-api-reference.md).
