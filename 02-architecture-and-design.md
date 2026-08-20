# 📄 Chapter 2: Technical Architecture & System Topology

> **"How We Built It: Low-Latency, Resilient & Pluggable"**  
> *A comprehensive engineering blueprint detailing the modular architecture, PgBouncer connection multiplexing, Prisma read-replica routing, pluggable provider design, and transactional event infrastructure.*

---

## 2.1 The "Learn, Unlearn, Relearn" Guide to Banking Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🚫 UNLEARN: "Microservices from Day 1 is the only way to build high-scale." │
│ Splitting into 20 microservices prematurely introduces network latency,     │
│ distributed transaction hell, and immense operational debugging friction.   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 💡 LEARN: "A cleanly decoupled Modular Monolith gives maximum speed & sanity"│
│ TypeDI Dependency Injection, bounded service domains, and strict internal   │
│ contracts allow you to run 10,000+ RPS on a single optimized cluster.      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🚀 RELEARN & MASTER: "Riverbrand uses a Pluggable Modular Architecture."    │
│ Every external dependency (WhatsApp, Cards, SMS, Mail) is a swappable      │
│ provider interface. Domain services emit async events to an Outbox relay.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2.2 Technology Stack & Architectural Topology

The Riverbrand Banking Engine (`RiverbrandBE`) is built on a high-throughput, non-blocking asynchronous architecture engineered specifically for financial technology systems.

![Technical High-Level Architecture](./images/technical-high-level-architecture.png)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FASTIFY HTTP SERVER ENGINE                     │
│               Ajv JSON Schema Validation | OpenAPI 3.0 / Scalar         │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
┌───────────────────────┐                           ┌────────────────────┐
│   PRISMA ORM 5.x      │                           │    REDIS 7.x       │
│  PostgreSQL 15 Driver │                           │ Distributed Lock   │
└───────────────────────┘                           │ Token Bucket       │
           │                                        │ WhatsApp Sessions  │
           ▼                                        └────────────────────┘
┌───────────────────────┐
│ PgBouncer Proxy 6432  │
│ Connection Pooler     │
└───────────────────────┘
           │
     ┌─────┴────────────────────────────────┐
     ▼                                      ▼
┌───────────────────────┐        ┌───────────────────────┐
│ Primary PostgreSQL 15 │        │ Read-Replica Mirror 1 │
│ Write Master (R/W)    │        │ Read Queries (RO)     │
└───────────────────────┘        └───────────────────────┘
```

### Stack Components & Selection Justifications

| Layer | Component | Version | Engineering Rationale |
| :--- | :--- | :--- | :--- |
| **Runtime** | Node.js | v20.x LTS | Event-driven single-threaded event loop providing high throughput for concurrent I/O-bound banking API requests. |
| **Framework** | Fastify | v4.x / v5.x | Up to 400% faster throughput than traditional Express.js. Native schema-based serialization with Ajv, zero overhead route resolution, and built-in plugin encapsulation. |
| **Language** | TypeScript | v5.3+ | Strict static typing across all request payloads, database queries, domain interfaces, and external gateway contracts, eliminating runtime type errors. |
| **Database & ORM** | PostgreSQL 15 & Prisma ORM 5.x | PostgreSQL 15<br/>Prisma 5.x | Robust relational integrity, ACID transaction guarantees, full-text search capabilities, combined with Prisma's auto-generated type-safe client and declarative migrations. |
| **Connection Pooler** | PgBouncer | v1.21+ | Dedicated PostgreSQL process connection manager. Converts 5,000 client connections into 50 pooled process connections, reducing DB RAM by 90%. |
| **Cache & In-Memory Store** | Redis | v7.x | High-speed memory storage used for Token Bucket Rate Limiting, distributed locking (`Redlock`), conversational WhatsApp session state machine, and active JWT blacklist storage. |
| **Conversational Bridge** | Multi-Provider WhatsApp Factory | Meta / Twilio / Termii / WATI / Interakt / 360dialog | Standardized `IWhatsAppProvider` interface allowing seamless switching across WhatsApp Business Solution Providers (BSPs). |
| **Dependency Injection** | TypeDI (`typedi`) | v0.10.x | Loose coupling between Controllers, Services, and Repositories via constructor-based Dependency Injection (`@Service()`). |
| **API Documentation** | `@fastify/swagger` & `@scalar/fastify-api-reference` | Latest | Auto-generated interactive OpenAPI 3.0 documentation served at `/documentation` (Swagger UI) and `/reference` (Scalar). |

---

## 2.3 Database Connection Architecture: PgBouncer & Read Replicas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🧠 MENTAL MODEL: The Bank Lobby vs. The VIP Concierge                       │
│                                                                             │
│ • Without PgBouncer: 5,000 customers burst into the lobby at once, each     │
│   demanding a dedicated bank clerk. The room runs out of oxygen (RAM        │
│   exhaustion) and crashes the bank.                                         │
│ • With PgBouncer: A sharp concierge at the door lets 5,000 requests queue   │
│   in milliseconds, serving them across 50 ultra-fast clerk desks.           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Why PgBouncer is Specific to PostgreSQL
Unlike MySQL (which uses lightweight threads per connection), PostgreSQL spawns a **full OS Process (`fork()`)** for each connection. Each process consumes **8 MB to 10 MB of RAM**.
- 5,000 direct connections = **50 GB RAM wasted on idle connections alone**.
- PgBouncer runs on port `6432` in transaction pooling mode (`pgbouncer=true`). Prisma communicates through PgBouncer as if it were PostgreSQL, maintaining thousands of client sessions on a lean pool of 50 physical connections.

```env
# Connection String via PgBouncer Pooler (Transaction Mode)
DATABASE_URL="postgresql://riverbrand:secret@pgbouncer:6432/riverbank_prod_db?schema=public&pgbouncer=true&connection_limit=50"
```

### 2. Read Replicas: The Master Vault vs. The Display Mirrors
In digital banking, **85% of database queries are Read operations** (checking balances, fetching transaction receipts), while **15% are Write operations** (debits, credits, transfers).

```
[Fastify Node.js Application]
             │
             ├──► Writes (UPDATE balance, INSERT transaction) ──► 🏛️ Primary Master DB (R/W)
             │                                                         │
             │                                              (Replication < 1ms)
             │                                                         ▼
             └──► Reads (SELECT balance, SELECT profile)  ──────► 🪞 Read Replica Mirrors (RO)
```

Prisma automatically routes writes to the Primary DB and reads to the Replica Mirrors using `@prisma/extension-read-replicas`:

```typescript
import { PrismaClient } from '@prisma/client';
import { readReplicas } from '@prisma/extension-read-replicas';

const basePrisma = new PrismaClient();

export const prisma = basePrisma.$extends(
  readReplicas({
    url: [
      process.env.DATABASE_READ_REPLICA_URL_1!, // Read Mirror 1
      process.env.DATABASE_READ_REPLICA_URL_2!, // Read Mirror 2
    ],
  })
);
```

---

## 2.4 Low-Level Technical Execution Flow

The diagram below traces an incoming financial request from signature verification to atomic execution and asynchronous notification relay:

![Technical Low-Level Flow](./images/technical-low-level-flow.png)

```
[1. INCOMING REQUEST] 
       │
       ▼
[2. CLIENT & HMAC AUTH] ──► (Invalid Signature? ──► Return 401 Unauthorized)
       │
       ▼
[3. REDIS RATE LIMIT] ──► (Bucket Exhausted? ──► Return 429 Too Many Requests)
       │
       ▼
[4. SIDECAR JWT VERSION] ──► (Version Mismatch? ──► Return 401 Session Revoked)
       │
       ▼
[5. REDIS REDLOCK] ──► (Acquire lock:wallet:{id} ──► Busy? Return 409 Conflict)
       │
       ▼
[6. POSTGRESQL $TRANSACTION]
       ├── Validate Balance >= Debit Amount
       ├── Decrement Source Wallet Balance
       ├── Increment Destination Wallet Balance
       ├── Insert Double-Entry Ledger Record
       └── Insert Outbox Event (Status: PENDING)
       │
       ▼
[7. RELEASE REDLOCK]
       │
       ▼
[8. RETURN 200 OK TO USER] 
       │
       ▼ (Asynchronous Background Execution)
[9. OUTBOX WORKER RELAY] ──► Send WhatsApp Message / Push Alert / Email Receipt
```

---

## 2.5 Pluggable Provider Architecture

Riverbrand isolates all third-party dependencies behind strict TypeScript interfaces:

![Pluggable Low-Latency Architecture](./images/pluggable-architecture.png)

### 1. Multi-Provider WhatsApp Gateway (`src/whatsapp-banking/providers/`)
All WhatsApp communication adheres to the `IWhatsAppProvider` interface:
- **MetaWhatsAppProvider**: Direct Meta Graph API v18+ with SHA-256 HMAC signature validation.
- **TwilioWhatsAppProvider**: Twilio Programmable Messaging API with `X-Twilio-Signature`.
- **TermiiWhatsAppProvider**: Direct telco gateway for Nigerian telecommunications.
- **WatiWhatsAppProvider**, **InteraktWhatsAppProvider**, **ThreeSixtyDialogProvider**: Enterprise BSP adapters.

```typescript
export interface IWhatsAppProvider {
  parseIncomingWebhook(body: any, headers: Record<string, string>): Promise<IIncomingMessage>;
  sendTextMessage(to: string, text: string): Promise<boolean>;
  sendInteractiveButtons(to: string, header: string, body: string, buttons: IButtonOption[]): Promise<boolean>;
  sendInteractiveList(to: string, title: string, sections: IListSection[]): Promise<boolean>;
  verifyWebhookSignature(rawBody: string, headers: Record<string, string>): boolean;
}
```

### 2. Multi-Driver Email & SMS Routing (`src/utils/mailing/` & `src/utils/sms/`)
- Dynamic failover chain: `SendGridDriver` ➔ `BrevoDriver` ➔ `SmtpDriver (Mailpit)`.
- SMS OTP dynamically routes between Termii and Twilio based on provider health checks.

### 3. Decoupled In-Memory Event Bus (`src/events/EventBus.ts`)
- Domain events (`UserRegistered`, `KycTierUpgraded`, `VirtualAccountCreated`, `P2PTransferDebited`) are emitted asynchronously without blocking controllers.
- Handlers in `src/events/handlers/` listen to events independently, keeping business controllers clean and decoupled.

---

## 2.6 Directory Structure & Code Topography

```
RiverbrandBE/
├── Dockerfile                      # Multi-stage production container build
├── docker-compose.yml              # Local development stack (Postgres, Redis, Mailpit)
├── docker-compose.prod.yml         # Production container orchestrator
├── src/
│   ├── api/                        # HTTP Layer (Controllers, Routes, Middleware, Swagger Docs)
│   │   ├── controllers/            # Controller Request Handlers
│   │   ├── middleware/             # Auth, RBAC, Rate Limiter, Metrics Plugins
│   │   └── routes/                 # Fastify Modular Route Definitions
│   ├── config/                     # Environment Variable Validation & Client Configs
│   ├── database/                   # Persistence Layer
│   │   ├── schema.prisma           # Master Prisma Schema (2,150+ lines)
│   │   ├── repository/             # Data Access Layer & Repositories
│   │   └── migrations/             # Standardized SQL Migration Files
│   ├── events/                     # Event Bus System & Domain Event Handlers
│   │   ├── EventBus.ts             # In-Memory Node EventEmitter Bus
│   │   └── handlers/               # Decoupled Domain Event Listeners
│   ├── interfaces/                 # Master TypeScript Interface Definitions
│   ├── job/                        # Cron Jobs (Outbox Processor, DLQ Replayer, Savings Interest)
│   ├── providers/                  # External Integrations (Fincra, Flutterwave, Dojah, Termii)
│   ├── schema/                     # Ajv Validation Schemas with OpenAPI Metadata
│   ├── services/                   # Business Domain Services (User, Wallet, Savings, KYC)
│   ├── utils/                      # Utilities (Logger, Locking, Crypto, Mailer)
│   └── whatsapp-banking/           # Multi-Provider Meta/Twilio/Termii/Wati Webhook Engine
└── index.ts                        # Application Entrypoint & Lifecycle Manager
```

---

## 2.7 Transactional Outbox Pattern & Event Relay

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🧠 MENTAL MODEL: The Guaranteed Postman                                     │
│                                                                             │
│ Problem: If we send money in PostgreSQL and then call WhatsApp API, what    │
│ happens if the WhatsApp API is down? Money is sent, but receipt is lost.    │
│ Solution: We save the outgoing message in the database in the SAME          │
│ transaction as the money transfer. A background worker picks it up and      │
│ retries until it is 100% delivered.                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
[Business Operation] ──(Single DB Transaction)──► [Update Wallet Balance]
                                            └────► [Insert Outbox Record (PENDING)]
                                                               │
                                                               ▼
[Outbox Cron Processor (src/job/outbox.ts)] ◄───(Polls Every 5s)──┘
        │
        ├─────────► [Publish Notification / Call Third-Party API] ──► (Status: PUBLISHED)
        │
        └─────────► [If Failure (Attempts > 5)] ──► [Move to Dead Letter Queue (DLQ)]
                                                            │
                                                            ▼
                                           [DLQ Replayer Job (src/job/dlq.ts)]
```

---

## 2.8 Observability & Prometheus Metrics

Riverbrand embeds deep observability directly into the server pipeline:
- **Dedicated Metrics Server (`src/services/metrics/metricsServer.ts`)**: Runs on isolated internal port `9095` serving `/metrics` for Prometheus scraping without exposing metrics to public internet clients.
- **Key Metrics Tracked**:
  - `http_requests_total`: Request counts by method, route, and status code.
  - `http_request_duration_seconds`: Histogram measuring API endpoint response latency percentiles (p50, p90, p99).
  - `financial_transactions_total`: Counter tracking money movement events by type and status.
  - `outbox_pending_events_count`: Gauge tracking pending event backlog in the outbox queue.
- **Health Diagnostics Service (`src/services/health/healthCheckService.ts`)**:
  - `/health/liveness`: Returns `200 OK` if the Fastify event loop is responsive.
  - `/health/readiness`: Performs active connectivity ping tests against PostgreSQL, Redis, Mailpit SMTP, and Outbox queues.

---

*Next Chapter: [03. Core Banking & Financial Engine](./03-core-banking-and-financial-engine.md) — Financial Ledger, Money Movement & Double-Spending Guard.*
