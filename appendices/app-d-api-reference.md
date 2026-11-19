# Appendix D: API and Endpoint Reference

This appendix catalogs the HTTP surface that the old documentation suite actually documents — and stops there. It is not a full REST reference. The RiverbrandBE API exposes far more routes than appear below; the complete, always-current surface is the interactive OpenAPI documentation served by the running stack at `/documentation`. Every route, header, status code, and configuration key recorded here is grounded in the 2026 documentation suite (primarily the developer and operations manual, the architecture chapter, the core-banking chapter, and the service catalog). Anything the old docs do not name is marked **UNVERIFIED**, with the standing note: *the full surface is the live Swagger at `/documentation`*. Marked items are tracked in the [UNVERIFIED register](app-g-changelog.md#unverified-register).

## Scope and Grounding

The rule this appendix follows is the book's evidence rule in its strictest form: a route appears as a route only where the old docs name its path or method. Domain *actions* — provisioning a NUBAN, moving money, registering a device — appear as action descriptions everywhere in the old suite but only occasionally as literal HTTP paths. Where a path is named, it is listed below as documented. Where only the action is named, the appendix describes the action and marks the exact route **UNVERIFIED**. This keeps the reference useful for orientation without pretending to a completeness the sources cannot support.

## Base URL and Ports

The API server listens on port **8010** in every documented environment (`PORT=8010` in the master `.env`; the Docker Compose stack publishes `0.0.0.0:8010->8010/tcp`). Local base URL: `http://localhost:8010`. In production the base URL sits behind whatever ingress the deployment provides — **UNVERIFIED** in the old docs.

| Port | Service | What it is | Documented evidence |
| --- | --- | --- | --- |
| 8010 | RiverbrandBE API (Fastify) | The banking API itself: routes, health checks, interactive docs, and the WhatsApp webhook. | `PORT=8010`; Compose mapping `0.0.0.0:8010->8010/tcp` |
| 8026 | Mailpit web inbox | Visual dashboard capturing all outgoing development emails. Mailpit's internal web port 8025 is published as 8026. | Compose mapping `0.0.0.0:8026->8025/tcp`; `http://localhost:8026` |
| 6432 | PgBouncer | PostgreSQL connection pooler. Production-style connection strings point at `pgbouncer:6432` with `pgbouncer=true&connection_limit=50`. | Architecture chapter connection string |
| 9095 | Prometheus metrics | Live metric telemetry for Prometheus scraping (`prom-client` counters, gauges, histograms). | `http://localhost:9095/metrics`; `MetricsService` serves on 9095 |

Supporting infrastructure ports documented in the same Compose output: PostgreSQL on 5432, Redis on 6379, and Mailpit's SMTP listener on 1025 (with `MP_SMTP_AUTH_ALLOW_INSECURE=1` for local development).

## Interactive API Documentation

Three documentation surfaces are served by the API container itself when the stack is up:

| Surface | Local URL | What it gives you |
| --- | --- | --- |
| Swagger UI | `http://localhost:8010/documentation` | Interactive OpenAPI 3.0 route testing interface. |
| Scalar reference | `http://localhost:8010/reference` | A modern interactive API reference interface. |
| Raw OpenAPI JSON | `http://localhost:8010/documentation/json` | The complete OpenAPI 3.0 JSON specification — machine-readable and diffable. |

Standing policy for this book: when a question is "what routes exist and what do their payloads look like?", the answer is the live Swagger at `/documentation` (or the raw spec at `/documentation/json` in CI). This appendix orients; it does not enumerate.

## Health and Readiness

Two operational probes, both documented with exact paths and both exercised by `HealthCheckService` (`src/services/health/healthCheckService.ts`):

| Endpoint | Method | Semantics |
| --- | --- | --- |
| `/health/liveness` | GET | Fast loop check returning `200 OK` — "is the process alive?". |
| `/health/readiness` | GET | Active deep ping tests against PostgreSQL, Redis, PgBouncer, and SMTP (the operations manual describes it as pinging Postgres, Redis, and Mailpit). Returns readiness only when dependencies answer. |

These are the endpoints to wire into container health checks and load-balancer probes. They are named identically in the architecture chapter and the developer and operations manual, so their paths are treated as documented fact.

## The WhatsApp Webhook

| Item | Documented value |
| --- | --- |
| Endpoint | `POST /whatsapp/webhook` (full local form: `POST http://localhost:8010/whatsapp/webhook`) |
| Role | Incoming Meta/Twilio message receiver for conversational banking. |
| Callback URL for providers | `https://<your-ngrok-subdomain>.ngrok-free.app/whatsapp/webhook` when tunneled locally with `ngrok http 8010`. |
| Verify token | `WHATSAPP_VERIFY_TOKEN` from `.env` (the documented development value is `riverbrand_secure_webhook_verify_token_2026`), configured in the Meta Developer Dashboard. |
| Signature validation | HMAC signature verification on every delivery. On mismatch the endpoint answers `403 Forbidden: Invalid HMAC signature`. The signing secret is `WHATSAPP_APP_SECRET` for Meta, or `TWILIO_AUTH_TOKEN` when the Twilio provider is active. |
| Provider selection | `WHATSAPP_PROVIDER` chooses the active adapter: `meta`, `twilio`, `termii`, `wati`, `interakt`, or `360dialog` — resolved at runtime by the provider factory behind one `IWhatsAppProvider` contract. |

Downstream of the webhook, message deduplication (24-hour Redis markers on message IDs), a 30-minute brute-force lockout counter, and the conversation state machine live in the WhatsApp service family; their internals are specified in the channel-fabric chapter and the service catalog, not here.

## Authentication and the Dual-Token Model

RiverbrandBE does not use one bearer token for every client. The auth middleware (`src/api/middleware/auth.ts`) enforces **dual-token client-type isolation** so a token minted for a mobile app cannot be replayed against the web surface, and vice versa. The header names are part of the documented contract:

| Client | Primary header | Alternative form |
| --- | --- | --- |
| Mobile native | `x-local-access-token: <TOKEN>` | `x-access-token: <TOKEN>` plus `x-client-type: mobile` |
| Web console | `x-web-access-token: <TOKEN>` | `x-access-token: <TOKEN>` plus `x-client-type: web` |

Each header is validated against its own auth schema. On startup, if the app stage is `PROD` or `PRODUCTION`, the server refuses to run unless both `LOCAL_ACCESS_TOKEN` and `WEB_ACCESS_TOKEN` are configured — a fatal shutdown (`process.exit(1)`) prevents an insecure deployment. The isolation mechanism is specified in [§9.1 Dual-Token Client Isolation](../chapters/ch09-engineering-security-architecture.md#91-dual-token-client-isolation).

## Login, Tokens, and Revocation

The documented authentication lifecycle, as the old docs describe it:

1. **Login.** The client authenticates against `POST /auth/login` (the exact path is named in the operations manual's troubleshooting playbook). `AuthService.signIn` validates credentials, checks account suspension status, verifies the client token type from the headers above, fetches the current `jwtVersion` from the sidecar table, and issues a signed JWT carrying that version as the `jv` claim.
2. **Authenticated calls.** Requests present the token in the appropriate client-type header. The middleware validates the signature and the `jv` claim against the sidecar version (with a 15-second hot cache).
3. **Revocation.** On password reset or sign-out, the sidecar's `jwtVersion` is incremented atomically. Every token issued under the previous version is now dead: the next call receives `401 Unauthorized` with the documented message *"Token has been revoked or has invalid version"*.
4. **Recovery.** Re-authenticate via `POST /auth/login` to obtain a fresh JWT carrying the updated `jv` claim. There is no other documented recovery path — that is the point of the kill-switch.

Related error codes on the auth surface (from the service catalog): `INVALID_CREDENTIALS` (401), `USER_SUSPENDED` (403), and `ACCOUNT_ALREADY_EXISTS` (409).

## Documented Request and Result Shapes

One request shape is documented verbatim in the old suite: the atomic debit payload consumed by the financial engine. It is an internal service contract rather than a public route schema, but it is the best grounded description of what a money-movement call carries, and integrators reading the Swagger will recognise its fields. Documented fields of `IAtomicDebitPayload`: `userId`, `amount`, `idempotencyKey`, `sessionId`, `extReferenceId`, `purpose` (a `ReferencePurpose`), `provider`, `providerFee`, `currency`, `currencyId`, `chargeType`, `nature`, `description`, `recipientEmail`, `recipientId`, `saveBeneficiary`, `sourceAccountName`, `sourceAccountNumber`, `sourceBankName`, and `skipLedger`. Documented fields of `IAtomicDebitResult`: `success`, `reference`, `sessionId`, `previousBalance`, `newBalance`, `debitedAmount`, `fee`, `providerFee`, and `realisedFee`. Two conventions follow from this shape and hold across the platform: every movement carries a cryptographic `idempotencyKey` (see `rbp_brand_references` in [Appendix C](app-c-data-dictionary.md)), and every result reports both the previous and the new balance so clients never need a second read. How these fields map onto the public HTTP payloads is **UNVERIFIED**; the full surface is the live Swagger at `/documentation`.

## Domain Routes Named in the Old Documentation

Only these money-movement routes appear with literal paths in the old suite:

| Route | What it does | Source |
| --- | --- | --- |
| `POST /auth/login` | Authenticate and obtain a JWT with the current `jv` claim. | Operations manual, troubleshooting problem D |
| `POST /user/provision-virtual-account` | Provision the customer's dedicated NUBAN (Providus first, Fincra fallback). Answers `200 OK` with existing details if the account already exists, `201 Created` with fresh NUBAN details otherwise. | Core-banking chapter, provisioning sequence |
| `POST /user/device-token` | Register a device's FCM push token (`DeviceToken`). | Savings and channels chapter, push-notification flow |
| `POST /whatsapp/webhook` | Receive inbound WhatsApp messages (see above). | Developer and operations manual |

Everything else — transfers, bill payments, savings products, KYC submission, beneficiaries, admin dashboards — is a documented *action* with an **UNVERIFIED** route. The full surface is the live Swagger at `/documentation`. Do not construct client integrations from this table alone; generate them from `/documentation/json`.

## Errors and Status Codes

| Code / message | HTTP | Meaning and remedy (as documented) |
| --- | --- | --- |
| `P1001` | — (client-side Prisma error surfaced as failure) | `PrismaClientInitializationError: Can't reach database server at postgres:5432`. The database container is down; restart it (`docker compose restart postgres`). |
| `RedlockError` / "A transaction is already in progress on this account" | 409 Conflict | A distributed wallet lock (`lock:wallet:{walletId}`, 10s TTL) is held by an in-flight movement. Inspect live locks with `redis-cli KEYS "lock:wallet:*"`; in development a stuck lock key can be deleted manually. A duplicate transfer request rejected at the lock also answers 409. |
| "Token has been revoked or has invalid version" | 401 Unauthorized | The sidecar `jwtVersion` was incremented (password reset or sign-out). Re-authenticate via `POST /auth/login`. |
| "Invalid HMAC signature" | 403 Forbidden | WhatsApp webhook signature validation failed. Confirm `WHATSAPP_APP_SECRET` (Meta) or `TWILIO_AUTH_TOKEN` (Twilio) matches the provider dashboard. |
| `INVALID_CREDENTIALS` | 401 | Sign-in failed: wrong email/phone or password. |
| `USER_SUSPENDED` | 403 | The account is suspended; sign-in is refused. |
| `ACCOUNT_ALREADY_EXISTS` | 409 | Sign-up collided with an existing user record. |
| "Transaction in progress" (lock rejection) | 409 Conflict | The concurrency guard refused a second concurrent movement on the same wallet; the client should retry after the in-flight request settles. |
| Transfer/debit failure modes (insufficient balance, limit exceeded, provider outage) | **UNVERIFIED** | The old docs describe these failure modes narratively but do not standardize their status codes. The full surface is the live Swagger at `/documentation`. |

Success shapes that *are* documented: `200 OK` for idempotent returns (existing NUBAN, liveness probes) and `201 Created` for fresh provisioning.

## Configuration Keys

The master `.env` documented in the operations manual is the configuration contract for the HTTP surface. Keys below are reproduced as documented; values shown in the manual are development placeholders and must never be reused in production.

| Key | Purpose |
| --- | --- |
| `PORT`, `NODE_ENV`, `APP_STAGE` | Server port (8010) and environment mode (`DEV`, `PROD`/`PRODUCTION` enforce dual-token presence). |
| `DATABASE_URL`, `REDIS_URL` | PostgreSQL (direct or via PgBouncer at 6432 with `pgbouncer=true&connection_limit=50`) and Redis (`redis://redis:6379`) connections. |
| `LOCAL_ACCESS_TOKEN`, `WEB_ACCESS_TOKEN`, `JWT_SECRET` | The two client-type tokens and the JWT signing secret. |
| `SMTP_HOST`, `SMTP_PORT`, `MP_SMTP_AUTH_ALLOW_INSECURE` | Outgoing mail (Mailpit in development: host `mailpit`, port 1025). |
| `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY` | Firebase Admin credentials for push notifications. |
| `DOJAH_API_KEY`, `DOJAH_APP_ID` | Dojah identity gateway (BVN/NIN verification). |
| `PROVIDUS_CLIENT_ID`, `FINCRA_SECRET_KEY` | NUBAN provisioning gateways (Providus primary, Fincra fallback). |
| `FLUTTERWAVE_SECRET_KEY` | Card funding and payout clearing. |
| `TERMII_API_KEY`, `TERMII_WHATSAPP_DEVICE_ID` | Termii SMS/WhatsApp gateway. |
| `WHATSAPP_PROVIDER`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET` | WhatsApp multi-provider configuration (`meta`, `twilio`, `termii`, `wati`, `interakt`, `360dialog`). |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` | Twilio WhatsApp credentials when that provider is active. |

## Where the Full Surface Lives

Recap of the standing rule: this appendix documents what the old documentation suite documents — the ports, the health probes, the webhook, the dual-token headers, the revocation flow, and the handful of literal routes that appear in its pages. For request and response schemas, for the routes marked **UNVERIFIED** here, and for anything added to RiverbrandBE after the 2026 suite was written, the authority is the running stack: Swagger at `/documentation`, Scalar at `/reference`, and the raw spec at `/documentation/json`. For the tables these endpoints touch, see [Appendix C: Data Dictionary](app-c-data-dictionary.md). For the operational runbooks behind the error table, see the engineering operations chapter, [§11.6](../chapters/ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook).
