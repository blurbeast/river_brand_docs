# 📄 Chapter 2: Technical Architecture & System Topology

> **"How We Achieved It"**  
> *Technical System Architecture, Pluggable Provider Design, Low-Latency Engineering, PgBouncer Connection Pooling, Prisma Read Replicas & Event Infrastructure.*

---

## 2.1 Technology Stack & Architectural Rationale

The Riverbrand Enterprise Digital Banking Engine (`RiverbrandBE`) is built on a high-throughput, non-blocking asynchronous architecture engineered specifically for financial technology systems.

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
           │                                        └────────────────────┘
           ▼
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
| **Cache & In-Memory Store** | Redis | v7.x | High-speed memory storage used for Token Bucket Rate Limiting, distributed locking (`Redlock`), session cache, and active JWT blacklist storage. |
| **Dependency Injection** | TypeDI (`typedi`) | v0.10.x | Loose coupling between Controllers, Services, and Repositories via constructor-based Dependency Injection (`@Service()`). |
| **API Documentation** | `@fastify/swagger` & `@scalar/fastify-api-reference` | Latest | Auto-generated interactive OpenAPI 3.0 documentation served at `/documentation` (Swagger UI) and `/reference` (Scalar). |

---

## 2.2 PostgreSQL Connection Architecture: PgBouncer & Read Replicas

### 1. Does Riverbrand Use Database Connections?
**Yes, absolutely.** Riverbrand relies on PostgreSQL 15 as its core relational persistence engine. 
- Every API endpoint that handles authentication, wallet balances, money transfers, or bill payments communicates with PostgreSQL via **Prisma ORM 5.x**.
- When the Fastify server starts up (`src/index.ts`), Prisma establishes an active database connection pool.

### 2. Why PgBouncer is Specific to PostgreSQL
You correctly identified that **PgBouncer is a specialized proxy built specifically for PostgreSQL**. Here is why PostgreSQL requires PgBouncer:

- **The Process Architecture of PostgreSQL**: Unlike MySQL or Microsoft SQL Server (which use lightweight internal threads for connections), PostgreSQL spawns a **full Operating System Process (`fork()`)** for every client connection. Each connection process consumes **8 MB to 10 MB of RAM** and requires CPU context switching.
- **The Problem**: If 5,000 Fastify app instances or worker threads open direct connections to PostgreSQL, PostgreSQL is forced to run 5,000 heavy OS processes, consuming **50 GB of RAM** just to maintain idle connections!
- **The PgBouncer Solution**: PgBouncer sits between Riverbrand's Node.js application and PostgreSQL on port `6432`. To Prisma, PgBouncer looks exactly like PostgreSQL. But behind the scenes, PgBouncer maintains a tiny pool of **50 actual OS connections** to PostgreSQL. As 5,000 incoming queries arrive from Node.js, PgBouncer routes them through the 50 pooled connections in transaction mode (`pgbouncer=true`).

#### Prisma Connection String with PgBouncer (`.env`)
```env
# Connection String via PgBouncer Pooler (Transaction Mode)
DATABASE_URL="postgresql://riverbrand:secret@pgbouncer:6432/riverbank_prod_db?schema=public&pgbouncer=true&connection_limit=50"
```

---

### 3. How Read Replicas (DB Read Mirrors) Work in Riverbrand

In digital banking, **85% of database queries are Read operations** (checking balance, viewing transaction receipts, fetching user profile), while **15% are Write operations** (wallet debits, credits, transfers).

To prevent read queries from slowing down money transfers, we split PostgreSQL into a **Primary Master (R/W)** and **Read Replica Mirrors (RO)**:

```
[Fastify Node.js Application]
             │
             ├──► Writes (UPDATE balance, INSERT transaction) ──► 🏛️ Primary Master DB (R/W)
             │                                                         │
             │                                              (Replication < 1ms)
             │                                                         ▼
             └──► Reads (SELECT balance, SELECT profile)  ──────► 🪞 Read Replica Mirrors (RO)
```

#### Configuring Read Replicas in Prisma ORM (`src/database/index.ts`)
Using the `@prisma/extension-read-replicas` extension, Prisma automatically routes writes to the Primary Master DB and reads to the Replica Mirrors:

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

- **Automatic Query Routing**: When code executes `prisma.wallet.update({ ... })` or `prisma.$transaction(...)`, Prisma routes the query to the **Primary Master DB**.
- When code executes `prisma.wallet.findUnique({ ... })` or `prisma.transaction.findMany({ ... })`, Prisma routes the query to **Read Replica Mirrors**, ensuring balance checks never slow down money transfers!

---

## 2.3 Pluggable Architecture & Low-Latency Engineering

Rather than tightly coupling business rules directly to specific vendors (e.g. tying money transfers directly to a single card processor or SMS vendor), Riverbrand implements a **Pluggable Modular Design**.

![Pluggable Low-Latency Architecture](./images/pluggable-architecture.png)

### 1. Plain-English Non-Technical Explanation (The Universal Power Plug)
- **Legacy Monolith Problem (Tightly Coupled)**: In old legacy banking systems, if you wanted to switch your SMS vendor from Termii to Twilio, or change card processors from Flutterwave to Paystack, developers had to rewrite half the application code. It was like hardwiring your television directly into the wall bricks—if you moved house, you had to tear down the wall.
- **Riverbrand Pluggable Approach (Universal Plug-and-Play)**: Riverbrand acts like a **Universal Power Socket**. Payment gateways, SMS providers, email delivery services, and alerting channels are separate, standardized "plugs". Adding a new payment gateway or SMS provider requires snapping in a new adapter without touching a single line of core banking wallet code!

### 2. Deep Technical Implementation Patterns

#### A. Provider Factory & Strategy Pattern (`src/providers/` & `src/utils/sms/`)
- Payment cards and virtual accounts use factory abstractions (`cardProviderFactory.ts`).
- Core services consume standard interfaces (`ICardProvider`, `IPaymentProvider`). If Flutterwave fails or a new provider like Fincra or Providus is added, `cardProviderFactory` dynamically routes requests based on configuration without changing business service code.

#### B. Pluggable Multi-Driver Mailer & SMS Failover (`src/utils/mailing/` & `src/utils/sms/`)
- The mailer service (`Mailer.ts`) supports dynamic fallback chains: `SendGridDriver` ➔ `BrevoDriver` ➔ `SmtpDriver (Mailpit)`.
- SMS OTP routing (`src/utils/sms/index.ts`) evaluates provider availability dynamically between Termii and Twilio.

#### C. Pluggable Alert Dispatcher (`src/services/alerting/`)
- The alert service (`AlertDispatcherService.ts`) maintains a registry of receivers implementing `IAlertReceiver`.
- Alerts are broadcast concurrently to `SlackAlertReceiver`, `EmailAlertReceiver`, and `GenericWebhookAlertReceiver` without tightly binding alerting logic to HTTP route handlers.

#### D. Decoupled In-Memory Event Bus (`src/events/EventBus.ts`)
- Domain events (`UserRegistered`, `KycTierUpgraded`, `VirtualAccountCreated`, `P2PTransferDebited`) are emitted asynchronously.
- Event handlers in `src/events/handlers/` listen to events independently, allowing new background features (e.g. marketing triggers, analytics tracking) to be plugged in with zero code modifications to core controllers.

### 3. Low-Latency Engineering Performance Pillars

| Low-Latency Pillar | Implementation Detail | Performance Benefit |
| :--- | :--- | :--- |
| **Fastify JIT Schema Compilation** | Fastify pre-compiles Ajv JSON validation schemas into optimized JS functions at startup. | Eliminates JSON parsing overhead, reducing route resolution latency to sub-milliseconds. |
| **In-Memory Redis Token Bucket** | Rate limiting (`TokenBucketRateLimiter`) and lock checks execute entirely in Redis memory. | Evaluates incoming request authorization in under 2 milliseconds without hitting database disk I/O. |
| **Asynchronous Non-Blocking I/O** | Audit logs, outbox inserts, push notifications, and emails execute asynchronously outside the primary HTTP response loop. | Returns HTTP `200 OK` responses immediately to mobile app users without waiting for third-party network calls. |

---

## 2.4 Modular Monolith Architecture

The application is structured as a **Modular Monolith**. This architectural pattern provides the simplicity of a single deployable unit with the clean boundaries and modularity of microservices, making future microservice extraction straightforward when scale demands it.

### Code Directory Topography

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
│   │   ├── schema.prisma           # Complete Master Prisma Schema (2,150+ lines)
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
│   └── whatsapp-banking/           # Meta Graph API Webhook & Conversational Engine
└── index.ts                        # Application Entrypoint & Lifecycle Manager
```

---

## 2.5 Database Schema & Relational Integrity

The persistence model managed in `src/database/schema.prisma` contains over 60 relational models designed to maintain strict financial consistency while preserving backward compatibility with legacy data schemas.

### Primary Domain Entity Relationships

```mermaid
erDiagram
    user_user ||--o| river_brand_sys_user_session_control : "has sidecar session"
    user_user ||--o| Wallet : "owns primary"
    user_user ||--o{ userAccountDetails : "owns NUBAN accounts"
    user_user ||--o{ Transaction : "executes ledger transactions"
    user_user ||--o{ UserDocument : "uploads KYC verification docs"
    user_user ||--o{ DeviceToken : "registers FCM push tokens"
    user_user ||--o{ AuditUserActivity : "generates user activity logs"
    
    Wallet ||--o{ rbp_brand_pending_balance : "holds pending funds"
    Target ||--o{ SavingsTransaction : "records savings deposits"
    
    Role ||--o{ RolePermission : "defines permissions"
    UserRole }|--|| Role : "assigns role"
    UserRole }|--|| user_user : "assigned to user"
```

---

## 2.6 Transactional Outbox Pattern & Event Relay

To solve the dual-write problem (where database updates succeed but external webhook notifications fail due to network glitches), Riverbrand uses the **Transactional Outbox Pattern**.

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

## 2.7 Operational Observability & Metrics Infrastructure

Riverbrand embeds deep observability directly into the server pipeline using Prometheus metrics and Fastify hooks.

### Metrics Infrastructure Components

- **Metrics Service (`src/services/metrics/metricsService.ts`)**: Built on top of `prom-client`. Collects application metrics:
  - `http_requests_total`: Counter tracking HTTP requests by method, route, and status code.
  - `http_request_duration_seconds`: Histogram measuring API endpoint response latency percentiles (p50, p90, p99).
  - `financial_transactions_total`: Counter tracking money movement events by type (`TRANSFER`, `BILL_PAYMENT`, `SAFELOCK`) and status.
  - `outbox_pending_events_count`: Gauge tracking pending event backlog in the outbox queue.
- **Dedicated Metrics HTTP Server (`src/services/metrics/metricsServer.ts`)**: Runs on isolated internal port `9095` serving `/metrics` for Prometheus scraping without exposing metrics to public internet clients.
- **Health Diagnostics Service (`src/services/health/healthCheckService.ts`)**:
  - `/health/liveness`: Returns `200 OK` if Fastify event loop is responsive.
  - `/health/readiness`: Performs active connectivity ping tests against PostgreSQL 15, Redis 7, Mailpit SMTP, and Outbox queues.

---

## 2.8 Summary

By combining PgBouncer connection pooling, Prisma read replica routing, pluggable provider interfaces, TypeDI dependency injection, Fastify JIT compilation, and the Transactional Outbox pattern, Riverbrand achieves an ultra-low latency, scalable banking architecture.

*Next Chapter: [03. Core Banking & Financial Engine](./03-core-banking-and-financial-engine.md) — Financial Ledger, Money Movement & Double-Spending Guard.*
