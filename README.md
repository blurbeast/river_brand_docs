# 🏦 Riverbrand Banking System Documentation

> **Authoritative Technical, Product & Architectural Knowledge Hub**  
> **Platform Version:** 1.0.0 Enterprise Release | **Target Stack:** Node.js v20 / Fastify / TypeScript / PostgreSQL / Redis / Docker

---

## 🧭 Master Dynamics & The "Learn, Unlearn, Relearn" Journey

Welcome to the official, end-to-end documentation suite for **Riverbrand Banking Engine** (`RiverbrandBE`).

Digital banking is often misunderstood as "just a database with balance numbers". In reality, modern banking software is an **orchestration of distributed consensus, real-time cryptography, non-blocking asynchronous state machines, and fail-safe financial ledgers**.

To truly master and teach this platform, we structure every concept around the **Learn, Unlearn, Relearn** framework:

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│     1. UNLEARN 🚫       │ ──► │       2. LEARN 💡       │ ──► │     3. RELEARN 🚀       │
│  Naive assumptions &    │     │  The real-world failure │     │  Riverbrand's resilient │
│  traditional antipatterns│    │  modes & race conditions│     │  architectural solutions│
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

### 🧠 The Core Mental Models

| Domain | 🚫 Unlearn (The Naive Way) | 💡 The Real Risk (Why it Fails) | 🚀 Relearn (Riverbrand's Architecture) |
| :--- | :--- | :--- | :--- |
| **Money Movements** | `UPDATE wallet SET balance = balance - 100` | Two rapid taps cause race conditions, resulting in double-spending and negative balances. | **Tier 1 Distributed Redlock** + **Tier 2 Single-Commit SQL Interactive Transactions** + **Immutable Double-Entry Ledger**. |
| **Session Security** | Storing JWTs and waiting for them to expire in 24 hours. | Stolen or lost devices stay logged in for hours, giving attackers free reign. | **Sidecar Session Control** with atomic `jwt_version` bumps that instantly kill all sessions globally on password reset. |
| **Conversational Chat** | A giant 2,000-line `if/else` or `switch` statement for WhatsApp bots. | Unmaintainable, state gets lost on restart, duplicate webhook deliveries cause double transfers. | **Hierarchical Redis State Machine** with strict step transition contracts and idempotent webhook processing. |
| **Background Work** | Calling slow third-party SMS/Email/Push APIs directly inside HTTP request handlers. | If third-party APIs lag or go down, customer HTTP requests hang, timeout, and crash the server. | **Transactional Outbox Pattern** with non-blocking event relay and exponential backoff retry workers. |
| **Database Connections** | Opening 5,000 direct connections to PostgreSQL from Fastify worker threads. | PostgreSQL spawns 5,000 OS processes, eating 50 GB of RAM and bringing the server to a halt. | **PgBouncer Connection Multiplexing** (5,000 clients -> 50 pooled DB connections) + **Prisma Read-Replicas**. |

---

## ⚡ The 5 Master Lifecycles of Riverbrand

Everything in Riverbrand flows through five core lifecycles:

```mermaid
graph TD
    subgraph L1["1. Genesis Lifecycle"]
        UserReg[User Registration] --> KycVal[BVN / NIN Identity Verification]
        KycVal --> NubanGen[Virtual NUBAN Auto-Provisioning]
    end

    subgraph L2["2. Quantum Money Lifecycle"]
        TxInit[Transfer Initiated] --> Redlock[Acquire Redis Redlock]
        Redlock --> AtomicTx[Atomic DB Debit + Credit]
        AtomicTx --> LedgerPost[Immutable Ledger Posting]
        LedgerPost --> OutboxEvent[Enqueue Outbox Event]
    end

    subgraph L3["3. WhatsApp Brain Lifecycle"]
        HookIn[Incoming WhatsApp Webhook] --> HmacCheck[HMAC Signature Verification]
        HmacCheck --> StateLookup[Redis Session State Lookup]
        StateLookup --> HandlerExec[Conversational Handler Execution]
        HandlerExec --> ChatReply[Rich Interactive Chat Response]
    end

    subgraph L4["4. Zero-Trust Security Lifecycle"]
        ClientReq[API Request] --> TokenIso[Client Type Isolation: Mobile vs Web]
        TokenIso --> JvCheck[Sidecar jwt_version Invalidation Check]
        JvCheck --> RateLimit[Token Bucket Rate Limiter]
        RateLimit --> AuditLog[Non-Blocking Audit Trail]
    end

    subgraph L5["5. Outbox Relay Lifecycle"]
        OutboxPoll[Outbox Background Worker] --> EventDispatch[Dispatch Notifications / Webhooks]
        EventDispatch --> AutoRetry[Dead-Letter Queue & Exponential Retry]
    end

    L1 --> L2
    L3 --> L2
    L2 --> L5
    L4 --> L2
```

---

## 🖼️ Visual Architecture & Diagram Gallery

To serve all stakeholders across executive, product, architecture, and engineering domains, the system is fully visualized across four core visual perspectives:

| Perspective | Diagram & Visual Reference | Primary Target Audience |
| :--- | :--- | :--- |
| **Technical High-Level** | ![Technical High-Level Architecture](./images/technical-high-level-architecture.png) | CTOs, Solutions Architects, Lead Engineers |
| **Technical Low-Level** | ![Technical Low-Level Flow](./images/technical-low-level-flow.png) | Core Backend Engineers, Security Auditors, DevOps |
| **Non-Technical High-Level** | ![Non-Technical High-Level Ecosystem](./images/non-technical-high-level-ecosystem.png) | C-Level Executives, Investors, Product Managers |
| **Non-Technical Low-Level** | ![Non-Technical Low-Level User Journey](./images/non-technical-low-level-journey.png) | Product Leads, Customer Support, Operations |

---

## 📚 Complete Document Library Index

The documentation suite is structured into 8 comprehensive, teachable chapters:

| Document | Focus & Audience | Key Topics Covered |
| :--- | :--- | :--- |
| 📄 [**01. Executive & Product Overview**](./01-executive-overview.md) | **Non-Technical / C-Suite / Operations** | Business value, banking ecosystem infographic, core product capabilities, wallet system, NUBAN provisioning, Safelock savings, conversational WhatsApp banking, KYC compliance, 5-currency user journeys. |
| 📄 [**02. Architecture & System Topology**](./02-architecture-and-design.md) | **Architects / Lead Engineers** | Microservice-ready modular monolith, Technical High-Level Architecture, Low-Level Execution Flow, PgBouncer connection pooling, Prisma read replicas, Event Bus, Outbox pattern, Prometheus metrics. |
| 📄 [**03. Core Banking & Financial Engine**](./03-core-banking-and-financial-engine.md) | **Financial Engineers / Auditors** | Atomic balance locking, double-spending guard (`Redlock`), interbank & P2P transfers, pending balance hold/release mechanics, KYC daily transaction ceilings. |
| 📄 [**04. Savings, WhatsApp & Channels**](./04-savings-investments-and-channels.md) | **Product Engineers / Channel Leads** | Safelock fixed deposits, Target Savings, AutoSave sweeps, Multi-Provider WhatsApp Engine (Meta, Twilio, Termii, Wati, Interakt, 360dialog), Redis session state machine, conversational handlers, FCM push notifications. |
| 📄 [**05. Security, Revocation & Auditing**](./05-security-compliance-and-auditing.md) | **Security Officers / Compliance** | Dual-Token isolation (`x-local-access-token` vs `x-web-access-token`), sidecar session invalidation (`jwt_version`), Argon2/bcrypt PINs, multi-channel OTP failover, WhatsApp HMAC webhook signatures, RBAC matrix, non-blocking audit trails. |
| 📄 [**06. Future Strategic Upgrade Roadmap**](./06-future-upgrade-roadmap.md) | **CTO / VP Engineering / Product Strategy** | Global hyper-scaling trajectory, Kafka event mesh, multi-region distributed SQL, Autonomous AI Banking agents, GNN fraud detection, PAPSS/SEPA clearing rails, and Multi-Tenant BaaS. |
| 📄 [**07. Developer & Operations Manual**](./07-developer-and-operations-manual.md) | **DevOps / Backend Engineers** | Local setup guide, Docker Compose deployment, environment variables catalog, database migrations, WhatsApp webhook testing & scripts, interactive Scalar/Swagger UI docs, troubleshooting playbook. |
| 📄 [**08. Complete Backend Service Catalog**](./08-service-catalog-and-deep-dive.md) | **Core Backend Engineers / System Auditors** | Line-by-line service specifications for all 36+ core backend services, WhatsApp providers, handlers, DTO payloads, database entities, external dependencies, error codes, and configuration switches. |

---

## 🎯 Quick Navigation by Role

### 💼 For C-Level Executives, Investors & Non-Technical Stakeholders
- Start with **[Chapter 01: Executive & Product Overview](./01-executive-overview.md)** for the high-level banking ecosystem, plain-English analogies, and visual user journeys.
- Review **[Chapter 06: Future Strategic Upgrade Roadmap](./06-future-upgrade-roadmap.md)** for long-term growth, scalability options, and international banking expansion.

### 🛡️ For Information Security, Risk & Compliance Officers
- Deep-dive into **[Chapter 05: Security, Revocation & Auditing](./05-security-compliance-and-auditing.md)** to inspect authentication token isolation, sidecar JWT versioning, instant token revocation, WhatsApp HMAC webhook security, and non-repudiable audit logging.
- Read **[Chapter 03: Core Banking & Financial Engine](./03-core-banking-and-financial-engine.md)** for double-spending safeguards and daily transaction volume ceilings per KYC tier.

### 💻 For Core Engineers, Architects & Systems Developers
- Study **[Chapter 02: Architecture & System Topology](./02-architecture-and-design.md)** for technical architecture blueprints, low-level execution flows, dependency injection, and database ORM designs.
- Examine **[Chapter 04: Savings, WhatsApp & Channels](./04-savings-investments-and-channels.md)** and **[Chapter 08: Backend Service Catalog](./08-service-catalog-and-deep-dive.md)** for WhatsApp multi-provider architecture, session state machines, handlers, and domain services.

### 🚀 For DevOps, Infrastructure & Reliability Engineers
- Follow **[Chapter 07: Developer & Operations Manual](./07-developer-and-operations-manual.md)** for local container stacks, WhatsApp webhook debugging, Mailpit email mocking, Prometheus metric scraping, Docker Compose production profiles, and recovery playbooks.

---

## 🛠️ Tech Stack At A Glance

- **Runtime Engine**: Node.js v20 (LTS) with TypeScript 5.x
- **Web Application Framework**: Fastify 4.x / 5.x (High-throughput non-blocking HTTP)
- **Data Persistence**: PostgreSQL 15 with Prisma ORM 5.x & PgBouncer Connection Pooler
- **Cache & Distributed Locking**: Redis 7.x (In-memory token bucket rate limiting, distributed `Redlock`, and WhatsApp conversational state machine)
- **WhatsApp Multi-Provider Bridge**: Meta Graph API v18+, Twilio Programmable Messaging, Termii WhatsApp API, Wati, Interakt, 360dialog
- **Messaging & Notifications**: Mailpit (Development SMTP), SendGrid / Brevo (Production Email), Firebase Cloud Messaging (FCM Push), Termii / Twilio (SMS OTP)
- **Payment & Identity Providers**: ProvidusBank (Virtual NUBAN), Fincra (Virtual Accounts & Settlements), Flutterwave (Cards & Transfers), Dojah (BVN / NIN Identity Verification)
- **Containerization & Metrics**: Docker Compose, Prometheus, Grafana

---

## ⚖️ Intellectual Property & Confidentiality

Copyright © 2026 **Riverbrand Partners**. All Rights Reserved.  
Confidential and proprietary documentation for internal systems engineering, executive governance, and authorized technical partner integration.
