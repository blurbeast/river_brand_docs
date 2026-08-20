# 📄 Chapter 1: Executive & Product Overview

> **"What the Application Does"**  
> *A non-technical blueprint for executives, product leaders, risk managers, and business stakeholders.*

---

## 1.1 Executive Vision & Product Mission

The **Riverbrand Enterprise Digital Banking Platform** (`RiverbrandBE`) is a high-performance, production-grade financial backend system designed to power next-generation digital banking services across mobile, web, and conversational channels.

In today's fast-evolving fintech landscape, modern financial institutions require systems that combine **uncompromised speed**, **absolute transaction integrity**, **strict regulatory compliance**, and **multi-channel accessibility**. Riverbrand fulfills this mission by serving as the central nervous system for all customer financial activities, money movement, wealth accumulation, identity verification, and automated customer communication.

![Riverbrand Digital Banking Ecosystem](./images/non-technical-high-level-ecosystem.png)

---

## 1.2 How the System Moves (Plain-English Analogy)

To understand how Riverbrand moves money securely, imagine a **Modern Airport & High-Security Vault**:

1. **The Passenger Entrances (Incoming Gateways)**: Money enters the system via external bank APIs (ProvidusBank, Fincra), debit cards (Flutterwave), or internal app transfers.
2. **The Air Traffic Controller & Vault Guard (Fastify API Gateway & Redis Lock)**: Every request passes through a central security checkpoint. If a user tries to transfer money twice simultaneously, the Vault Guard locks the wallet key instantly, preventing double-spending.
3. **The Immutable Bank Vault (PostgreSQL Database)**: All account balances and transaction histories are stored in a tamper-proof database vault. Every cent moved is permanently recorded with double-entry ledger precision.
4. **The Dispatch Couriers (Transactional Outbox & Notifications)**: Once a transaction is sealed in the vault, background couriers deliver instant confirmation receipts via WhatsApp messages, mobile push alerts, and email notifications.

![System Movement Flow](./images/system-movement.png)

---

## 1.3 Omni-Channel Tri-Client Architecture: Mobile, Web & WhatsApp

Riverbrand is engineered from the ground up as a **Unified Omni-Channel Digital Banking Engine**. It powers three first-class client channels, all operating against a single real-time ledger, distributed lock manager, and compliance core:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                UNIFIED FASTIFY API BACKEND                              │
│         Single Ledger | Real-Time Balances | Redlock Guard | KYC Limits | Outbox        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
          │                                   │                                   │
          ▼                                   ▼                                   ▼
┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
│   📱 NATIVE MOBILE APP    │   │  💻 WEB PORTAL & ADMIN    │   │   💬 24/7 WHATSAPP BOT    │
│      (iOS & Android)      │   │      (Customer & Staff)   │   │   (Conversational Chat)   │
├───────────────────────────┤   ├───────────────────────────┤   ├───────────────────────────┤
│ • Biometric / Face ID Auth│   │ • Customer Web Dashboard  │   │ • Zero-Friction Onboarding│
│ • Flutterwave Card Top-up │   │ • Executive Stats Console │   │ • Conversational Transfers│
│ • Live KYC Camera Uploads │   │ • Staff User Governance   │   │ • Airtime & Utility Bills │
│ • Target Savings Trackers │   │ • Granular RBAC Matrix    │   │ • Instant Chat Receipts   │
│ • FCM Multi-Device Push   │   │ • Non-Blocking Audit Logs │   │ • Multi-Currency Inquiries│
│ • Header: `x-local-token` │   │ • Header: `x-web-token`   │   │ • Webhook HMAC Signature  │
└───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

| Client Channel | Target Audience | Primary Functionality | Security & Authentication Layer |
| :--- | :--- | :--- | :--- |
| **📱 Native Mobile App** *(iOS / Android)* | Everyday retail customers, wealth builders | Full mobile banking: biometric sign-in, tokenized debit card wallet funding, live camera document uploads for Tier 3 KYC, Safelock deposits, Target Savings progress bars, FCM real-time push notifications. | `x-local-access-token` header, device hardware pairing, Argon2id passwords, 4-digit PIN bcrypt. |
| **💻 Customer Web Portal & Enterprise Admin Console** | Retail web customers & Administrative staff | Customer web dashboard, full funds transfer suite, executive financial metrics, system liabilities, user suspension/unsuspension, manual KYC approvals, granular RBAC permissions (`sys_roles`), system config flags, audit logs. | `x-web-access-token` header, short-lived browser session tokens, sidecar `jwt_version` instant revocation. |
| **💬 WhatsApp Conversational Banking** | Mobile-first users, low-bandwidth customers | 24/7 conversational banking: passwordless onboarding, BVN lookup, interbank & P2P transfers, airtime/data top-up, electricity token delivery, DSTV renewals, multi-currency balance queries, instant chat receipts. | Provider HMAC-SHA256 signature verification (`x-hub-signature-256`, `X-Twilio-Signature`), 4-digit PIN auth, 3-attempt brute-force Redis lockout. |

---

## 1.4 Core Product Capabilities ("What the App Does")

The application delivers eight major business functional pillars:

### 1. 💳 Digital Accounts & Dedicated Virtual NUBAN Accounts
- **Dedicated Bank Accounts**: Upon completing user registration, the system automatically provisions dedicated Nigerian Uniform Bank Account Numbers (NUBAN) through integrated commercial banking gateways (such as ProvidusBank and Fincra).
- **Direct Deposit Reception**: Customers can receive funds directly from any commercial bank account in Nigeria into their Riverbrand digital account instantly.
- **Account Dashboard**: Provides customers with real-time balance metrics, active account numbers, provider details, and account health statuses.

### 2. 💸 Multi-Currency Wallets & Balance Ledger
- **Multi-Currency Provisioning**: Supports multi-currency digital wallets (including NGN, USD, GBP, and EUR).
- **Real-Time Exchange Rates**: Calculates dynamic cross-currency conversions using centralized administrative exchange rate matrices (`ExchangeRate`).
- **Ledger Transparency**: Every deposit, transfer, withdrawal, and bill payment creates immutable ledger entries (`payment_transaction` and `transactions`), guaranteeing full balance traceability.

### 3. 🔄 Money Transfers & Interbank Payments
- **Interbank Transfers**: Allows customers to send money instantly to any commercial bank account in Nigeria.
- **Peer-to-Peer (P2P) Internal Transfers**: Enables zero-fee instant funds transfers between Riverbrand app users using their username, phone number, or tag.
- **Beneficiary Management**: Automatically saves commercial bank accounts, airtime phone numbers, and internal P2P contacts for effortless repeat transactions.

### 4. ⚡ Utility Bills, Airtime & Data Bundles
- **Airtime & Mobile Data Top-up**: Instant purchase of airtime and data bundles across all major telecommunications networks (MTN, Airtel, Glo, 9mobile).
- **Utility & Entertainment Payments**: Direct bill payments for Electricity utility providers (prepaid meter token generation and postpaid clearing), Cable TV subscriptions (DSTV, GOTV, Startimes), Internet service providers, and Gaming/Betting wallet top-ups.
- **Automated Digital Receipts**: Generates email and PDF receipts immediately following every completed bill transaction.

### 5. 📈 Wealth Management: Safelock, Target Goals & AutoSave
- **Safelock Fixed Deposits**: Customers can lock upfront capital for specified tenures (e.g., 30, 90, 180, 365 days) to earn high-yield compounding interest. Capital cannot be liquidated prior to maturity, instilling financial discipline and giving the institution predictable liquidity reserves.
- **Target Savings Goals**: Goal-based savings plans (e.g., "Rent 2027", "New Car Fund") with scheduled daily, weekly, or monthly automatic wallet debits.
- **AutoSave Sweeps**: Automated rules that periodically sweep idle wallet balances into designated interest-bearing savings accounts.

### 6. 💬 24/7 WhatsApp Conversational Banking Engine
- **Full Banking on WhatsApp**: Customers can perform everyday banking tasks directly inside WhatsApp by conversing with Riverbrand's automated multi-provider conversational engine.
- **End-to-End WhatsApp Banking Capabilities**:
  - **Zero-Friction Registration**: Unregistered users can sign up, verify email via OTP, validate BVN, capture selfie photo KYC, set their 4-digit transaction PIN, and receive an instant dedicated NUBAN bank account without leaving WhatsApp.
  - **Instant Interbank & P2P Transfers**: Send money to any Nigerian bank or Riverbrand peer by simply typing the recipient account number and amount, authorized with secret 4-digit PIN.
  - **Airtime & Data Purchases**: Buy mobile top-ups for self or third parties across MTN, Airtel, Glo, and 9mobile with automatic network detection.
  - **Utility & Cable TV Payments**: Pay electricity bills and renew DSTV/GOTV subscriptions with instant token delivery in chat.
  - **Multi-Currency Balance Inquiries**: Check live wallet balances in NGN, USD, EUR, and GBP with mini-statements.
  - **Real-Time Debit/Credit Alerts**: Inbound deposits and outbound payments automatically push rich interactive receipt cards to the user's WhatsApp conversation.
- **Multi-Provider Reliability**: Supports **Meta Graph API**, **Twilio Programmable Messaging**, **Termii WhatsApp**, **WATI**, **Interakt**, and **360dialog** with automated signature validation and failover.

### 7. 🛡️ Tiered KYC & Identity Verification
- **Tier 1 (Basic)**: Standard registration with phone number verification and daily transaction limit of ₦50,000.
- **Tier 2 (Identity Verified)**: Verification of Bank Verification Number (BVN) and National Identity Number (NIN) via the Dojah Identity Gateway / Mono API, elevating daily transaction limit to ₦200,000.
- **Tier 3 (Full KYC)**: Upload and verification of residential address proof and government-issued photo ID (`UserDocument`), granting high-volume daily limits (up to ₦5,000,000+).

### 8. 📊 Enterprise Admin Console & Audit Controls
- **Staff Operations Dashboard**: Real-time executive dashboard showing active user count, aggregate wallet liabilities, provider reserve totals, transaction volume velocity, and pending KYC verifications.
- **User Governance**: Administrative capabilities to suspend, unsuspend, upgrade KYC tiers, or lock suspicious user accounts.
- **Granular RBAC**: Role-Based Access Control matrix (`sys_roles`, `sys_permissions`) enforcing strict segregation of duties among administrative staff.
- **Asynchronous Audit Trail**: Every administrative action, user sign-in, password modification, and system event is permanently logged into non-repudiable audit tables.

---

## 1.5 Step-by-Step Customer Journey (Non-Technical Workflow)

The diagram below illustrates how an everyday retail customer interacts with Riverbrand's multi-channel ecosystem, from initiating a chat on WhatsApp to authenticating securely and receiving instant digital confirmation receipts:

![Non-Technical Low-Level User Journey](./images/non-technical-low-level-journey.png)

### The 5-Step Frictionless Transaction Flow:
1. **Step 1 — Open WhatsApp & Message Riverbrand**: User sends a friendly greeting (e.g., "Hi Riverbrand" or "Transfer 5000").
2. **Step 2 — Instant Interactive Welcome Menu**: The conversational engine presents interactive button options (Transfer Money, Buy Airtime, Check Balance, Savings).
3. **Step 3 — Enter Transaction Details**: User provides destination account number or picks from saved beneficiaries, with live account name resolution.
4. **Step 4 — Authorize Securely with PIN**: High-risk financial operations prompt the customer for their secret 4-digit PIN (protected with bcrypt/argon2 hashing and brute-force lockout).
5. **Step 5 — Instant Receipt & Dual Notification**: The transaction executes atomically, and the user receives a clean digital receipt card on WhatsApp alongside an FCM push notification.

---

## 1.6 Complete User Lifecycle: Five Multi-Currency Journey Scenarios

To illustrate how users interact with Riverbrand across different currencies and financial goals, consider these five end-to-end user lifecycle scenarios:

![Multi-Currency User Journeys](./images/user-journey-5-currencies.png)

### 🇳🇬 Scenario 1: NGN Local Retail User Journey
- **User Profile**: Tunde, a retail professional in Lagos.
- **Step 1 (Sign-Up & Provisioning)**: Tunde registers on the mobile app or WhatsApp. The system automatically provisions a dedicated NUBAN virtual account (`9920123456 - ProvidusBank`).
- **Step 2 (Local Deposit)**: Tunde transfers ₦150,000 NGN from GTBank. Inbound webhook triggers atomic wallet credit, email receipt, and FCM push notification.
- **Step 3 (Everyday Banking)**: Tunde opens WhatsApp and types "Pay DSTV". The WhatsApp bot validates his 4-digit PIN and executes a ₦35,000 bill payment instantly.

### 🇺🇸 Scenario 2: USD Cross-Border Wealth & Safelock Journey
- **User Profile**: Sarah, a tech consultant building dollar-denominated wealth.
- **Step 1 (Multi-Currency Account)**: Sarah activates her USD wallet inside Riverbrand.
- **Step 2 (FX Conversion)**: Sarah deposits ₦1,600,000 NGN and executes an in-app exchange to convert it to $1,000.00 USD at the active administrative exchange rate (`ExchangeRate`).
- **Step 3 (Safelock Fixed Deposit)**: She locks $1,000 USD into a 180-Day Safelock at 8% p.a. interest.
- **Step 4 (Automated Yield & Maturity)**: The nightly cron job accrues daily USD interest. At maturity, $1,040 USD (principal + net interest) is credited back to her primary USD wallet.

### 🇪🇺 Scenario 3: EUR International Remittance & KYC Pending Hold Journey
- **User Profile**: Amara, a university student receiving international funds from Europe.
- **Step 1 (Incoming EUR Inflow)**: Amara receives a €2,500 EUR remittance from a sponsor in Germany.
- **Step 2 (Tier 1 Limit Trigger)**: Because Amara is currently Tier 1 (daily deposit limit €500 EUR equivalent), the system credits €500 EUR to her main wallet and automatically places €2,000 EUR into `rbp_brand_pending_balance`.
- **Step 3 (KYC Upload & Auto-Release)**: Amara submits her BVN and NIN via the app. Dojah Gateway verifies her identity, upgrading her to Tier 2. The event handler (`KycTierUpgradedHandler`) automatically releases the held €2,000 EUR into her available balance.

### 🇬🇧 Scenario 4: GBP Freelancer & Automated Target Savings Journey
- **User Profile**: David, a freelance software engineer earning in British Pounds.
- **Step 1 (GBP Wallet Inflow)**: David receives £1,200 GBP client payment into his Riverbrand GBP account.
- **Step 2 (Target Goal Setup)**: He creates a target savings goal: "UK Master's Degree - £5,000 GBP".
- **Step 3 (AutoSave Rules)**: David enables AutoSave, configured to sweep £150 GBP every Friday from his GBP wallet into his Target Savings pool.
- **Step 4 (Goal Tracking)**: Real-time progress bar alerts update him via push notifications as he approaches his savings goal.

### 🇨🇦 Scenario 5: CAD Business Payment & Security Revocation Safeguard
- **User Profile**: Ken, an import-export business manager in Toronto.
- **Step 1 (High-Volume CAD Payment)**: Ken receives a $10,000 CAD invoice payment into his corporate wallet.
- **Step 2 (Security Threat / Password Reset)**: Ken misplaces his tablet and immediately resets his account password from his laptop.
- **Step 3 (Sidecar Instant Revocation)**: The sidecar session controller (`river_brand_sys_user_session_control`) increments `jwtVersion` from 1 to 2.
- **Step 4 (Protection Verified)**: Any stale access token on the lost tablet is rejected instantly (`401 Unauthorized`) across all API servers, safeguarding his $10,000 CAD balance.

---

## 1.7 Business Value & Key Risk Mitigations

| Business Risk | How Riverbrand Engine Mitigates It | Plain-English Explanation |
| :--- | :--- | :--- |
| **Double-Spending & Race Conditions** | Distributed Redis Locks (`Redlock`) + SQL Transactions (`$transaction`) | Prevents a customer from tapping "Transfer" twice simultaneously on two phones to spend the same money twice. |
| **Session Hijacking / Stolen Tokens** | Dual-Token Isolation + Sidecar `jwtVersion` Invalidation | If a user loses their phone or changes their password, all active logins across all devices are cut off instantly. |
| **Third-Party Provider Outages** | Multi-Provider WhatsApp Fallback + Transactional Outbox Pattern | If one SMS, WhatsApp, or email vendor experiences downtime, the system dynamically switches to backup gateways without dropping transactions. |
| **Regulatory Non-Compliance (KYC/AML)** | Tiered Limits Tracker (`rbp_brand_daily_limit_tracker`) + Dojah BVN/NIN Gateway | Enforces exact daily transfer ceilings according to government regulations based on verified user identity level. |
| **Unauthorized Admin Abuse** | Non-Blocking Audit Trail + Granular RBAC | Ensures staff can only perform actions assigned to their exact role, and logs every staff click with timestamp and IP address. |

---

## 1.8 Summary

The Riverbrand Enterprise Digital Banking Engine represents a robust, highly resilient digital bank in a box. It converts complex financial infrastructure into a seamless, elegant experience for everyday retail customers, wealth builders, and administrative teams.

*Next Chapter: [02. Architecture & System Topology](./02-architecture-and-design.md) — Technical System Architecture & Engineering Specifications.*
