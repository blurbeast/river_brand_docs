# 📄 Chapter 4: Savings, WhatsApp Banking & Channel Integration

> **"Wealth Engine, Multi-Provider Conversational Banking & Push Notifications"**  
> *Detailed technical specification on Safelock yield calculations, multi-provider WhatsApp engine (Meta, Twilio, Termii, Wati, Interakt, 360dialog), Redis conversational state machines, and FCM push dispatch.*

---

## 4.1 Wealth Management Engine: Safelock, Target Savings & AutoSave

The wealth engine (`src/services/monetary/savings/savings.ts`) enables retail customers to save disciplined funds and earn competitive compounding interest yields while providing the platform with predictable liquidity reserves.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RIVERBRAND WEALTH ENGINE                        │
│               Compounding Interest Engine & Scheduled Sweeps           │
└────────────────────────────────────────────────────────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌────────────────────┐
│  SAFELOCK DEPOSITS  │   │   TARGET SAVINGS    │   │  AUTOSAVE SWEEPS   │
│ • Locked Tenures    │   │ • Goal-Based        │   │ • Daily/Weekly     │
│ • Guaranteed Yield  │   │ • Scheduled Debits  │   │ • Wallet Sweeps    │
└─────────────────────┘   └─────────────────────┘   └────────────────────┘
```

### 1. Safelock Fixed Deposit Engine
- **Upfront Capital Locking**: Customer funds are debited from the main wallet (`Wallet`) and locked inside a `Target` record where `savingsType = SAFELOCK`.
- **Compound Interest Calculation Formula**:
  $$\text{Daily Yield} = \frac{\text{Principal Amount} \times \text{Annual Interest Rate (\%)}}{365 \times 100}$$
- **Daily Interest Accrual Job (`src/job/savings.ts`)**: Runs every night at 00:00 UTC. Iterates through active locked deposits, calculates the daily yield, updates `currentAmount`, and records an entry in `savings_usersavinginterestlog`.
- **Maturity Auto-Payout (`src/events/handlers/SafelockMaturedHandler.ts`)**: On the maturity date (`endDate`), the principal plus net accrued interest is credited back to the customer's primary wallet automatically.
- **Early Breakage Penalty Math**: If a customer requests emergency liquidation prior to maturity, a breakage penalty rate (`breakage_rate`, typically 20-30% of accrued interest) and government tax (`govern_withdrawal_tax_amount`) are deducted, returning only net principal + remaining interest.

---

## 4.2 Multi-Provider WhatsApp Conversational Banking Engine

Riverbrand features an enterprise-grade conversational banking engine (`src/whatsapp-banking/`) designed with a **Pluggable Multi-Provider Architecture**. Rather than hardcoding the banking logic to a single WhatsApp BSP (Business Solution Provider), Riverbrand exposes a unified contract (`IWhatsAppProvider`) allowing dynamic runtime switching across providers.

```mermaid
graph TD
    UserChat[📱 WhatsApp User] -->|HTTP Webhook POST| Controller[⚡ WhatsAppController.ts]
    Controller -->|Signature Verify| Factory[🏭 WhatsAppProviderFactory]
    
    Factory -->|Provider Selected| Provider[🔌 Active Provider Adapter]
    subgraph Providers [Supported WhatsApp Gateways]
        Meta[Meta Graph API v18+]
        Twilio[Twilio Programmable Messaging]
        Termii[Termii WhatsApp API]
        Wati[WATI CRM & Messaging]
        Interakt[Interakt BSP]
        ThreeSixty[360dialog Cloud API]
    end
    Provider --- Providers
    
    Provider -->|Normalized Payload| Engine[🤖 WhatsAppBankingService]
    Engine -->|State / Locks| Redis[(⚡ Redis Session State Machine)]
    Engine -->|Business Logic| Handlers[📦 Domain Handlers]
    
    subgraph Handlers [Conversational Step Handlers]
        H_Reg[WhatsAppRegistrationHandler]
        H_Trf[WhatsAppTransferHandler]
        H_Air[WhatsAppAirtimeHandler]
        H_Bill[WhatsAppBillPaymentHandler]
        H_Kyc[WhatsAppKycHandler]
    end
    
    Handlers --> Financial[🏦 Core Financial Services & Ledger]
    Handlers --> Response[💬 WhatsAppResponseService]
    Response --> Provider
```

### Supported WhatsApp Provider Integrations

| Provider Adapter (`src/whatsapp-banking/providers/`) | Primary Use Case | Signature Verification Mechanism | Message Types Supported |
| :--- | :--- | :--- | :--- |
| **`MetaWhatsAppProvider`** | Official Meta Graph Cloud API (Direct) | `x-hub-signature-256` HMAC-SHA256 | Text, Interactive Buttons, Lists, Flows, Templates |
| **`TwilioWhatsAppProvider`** | Global Twilio Messaging & Twilio Studio Flows | `X-Twilio-Signature` HMAC-SHA1 | Text, Media, Twilio Studio Webhooks, Templates |
| **`TermiiWhatsAppProvider`** | African Regional Telco Gateway | Termii API Token / Bearer Header | Text, Media, Interactive Menus |
| **`WatiWhatsAppProvider`** | WATI Customer Engagement Platform | WATI Webhook Token | Text, Buttons, Templates, Media |
| **`InteraktWhatsAppProvider`** | Interakt Omnichannel Platform | Interakt Signature Header | Text, Interactive Lists, Quick Replies |
| **`ThreeSixtyDialogProvider`** | High-Throughput 360dialog Cloud API | 360dialog Client API Key | Text, Buttons, Lists, Media, Flows |

---

## 4.3 Redis-Backed Conversational State Machine (`WhatsAppSessionService`)

Conversational banking requires tracking state across multiple chat interactions while maintaining low latency and zero database bloat. Riverbrand uses **Redis in-memory caching** (`src/whatsapp-banking/services/WhatsAppSessionService.ts`) to manage session lifecycles.

### Session Lifecycle & Data Model

```typescript
export interface WhatsAppUserSession {
  phoneNumber: string;                // e.g. "2348012345678"
  step: WhatsAppStep;                 // Current conversational state
  authenticated: boolean;             // True if phone maps to verified user
  userId?: string;                    // Linked database user_user ID
  userFullName?: string;              // Customer display name
  failedPinAttempts: number;          // Counter for brute-force prevention
  sessionData: Record<string, any>;   // Dynamic step cache (e.g. transfer amount, bank, recipient)
  lastActivity: number;               // Unix timestamp (ms)
}
```

### Redis Key Layout & TTL Rules

- **Active Session**: `wa:session:{cleanPhoneNumber}` — TTL: `1800 seconds` (30 minutes). Reset on every inbound message.
- **Message Deduplication**: `wa:msg:{messageId}` — TTL: `86400 seconds` (24 hours). Prevents duplicate processing of webhook retries.
- **Security Lockout**: `wa:lockout:{cleanPhoneNumber}` — TTL: `1800 seconds` (30 minutes). Automatically set when `failedPinAttempts >= 3`.
- **Global Reset Keywords**: Sending `HI`, `HELLO`, `MENU`, `MAIN`, `START`, `CANCEL`, `RESET`, or `EXIT` instantly clears step memory and returns the customer to the top-level main menu (`WhatsAppStep.IDLE`).

---

## 4.4 Conversational Step Handlers Deep Dive

The business logic is partitioned into dedicated domain handlers (`src/whatsapp-banking/services/handlers/`):

```
                               ┌───────────────────────────────────┐
                               │     INCOMING WHATSAPP MESSAGE     │
                               └───────────────────────────────────┘
                                                 │
                                                 ▼
                               ┌───────────────────────────────────┐
                               │    WhatsAppBankingService.ts      │
                               │  Evaluates session.step in Redis  │
                               └───────────────────────────────────┘
                                                 │
         ┌───────────────────┬───────────────────┼───────────────────┬───────────────────┐
         ▼                   ▼                   ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  REGISTRATION   │ │    TRANSFERS    │ │ AIRTIME & DATA  │ │  BILL PAYMENTS  │ │ KYC & BALANCES  │
│     HANDLER     │ │     HANDLER     │ │     HANDLER     │ │     HANDLER     │ │     HANDLER     │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1. `WhatsAppRegistrationHandler` (`WhatsAppRegistrationHandler.ts`)
Allows prospective customers to complete frictionless KYC onboarding without ever downloading the native mobile app:
1. **Name Capture (`REGISTRATION_NAME`)**: User enters First and Last Name.
2. **Email Capture & OTP (`REGISTRATION_EMAIL` & `REGISTRATION_EMAIL_OTP`)**: Dispatches a 6-digit cryptographic OTP to the email.
3. **BVN Verification (`REGISTRATION_BVN`)**: Queries Dojah Identity Gateway to verify identity against national database.
4. **Selfie Capture (`REGISTRATION_SELFIE`)**: User takes a photo inside WhatsApp, uploaded to secure cloud storage.
5. **Set 4-Digit PIN (`REGISTRATION_SET_PIN`)**: Hashes transaction PIN using bcrypt/argon2.
6. **Instant NUBAN Provisioning**: Automatically triggers `UserProvisioningService`, creating a dedicated Providus/Fincra bank account and sending an interactive welcome card.

### 2. `WhatsAppTransferHandler` (`WhatsAppTransferHandler.ts`)
Powers instant P2P and Interbank transfers:
1. **Account Entry / Beneficiary Selection (`TRANSFER_ENTER_ACCOUNT`)**: Prompts user for 10-digit NUBAN or saved beneficiary.
2. **Bank Selection & Name Inquiry (`TRANSFER_SELECT_BANK`)**: Resolves account name dynamically against Nigerian interbank clearing switch.
3. **Currency & Amount Entry (`TRANSFER_SELECT_CURRENCY` & `TRANSFER_ENTER_AMOUNT`)**: Selects wallet (NGN, USD, EUR, GBP) and debit amount.
4. **PIN Authorization (`TRANSFER_ENTER_PIN`)**: Verifies 4-digit PIN with brute-force lockout protection.
5. **Atomic Execution**: Calls `FinancialEngine` with distributed Redlock locking, producing an instant digital receipt card on WhatsApp.

### 3. `WhatsAppAirtimeHandler` (`WhatsAppAirtimeHandler.ts`)
1. **Recipient & Network**: Top-up for self or enter 3rd-party number; auto-detects telco (MTN, Airtel, Glo, 9mobile).
2. **Amount / Data Plan Selection**: Dynamic data plan lists retrieved directly from VTU providers.
3. **PIN Authorization & Instant Top-up**: Executes wallet debit and delivers mobile value in seconds.

### 4. `WhatsAppBillPaymentHandler` (`WhatsAppBillPaymentHandler.ts`)
1. **Category Selection**: Electricity (Prepaid / Postpaid), Cable TV (DSTV, GOTV, Startimes), Internet, Betting.
2. **Meter / Smartcard Validation**: Live account lookup verifying meter owner name before taking payment.
3. **PIN Authorization & Token Delivery**: Generates prepaid 20-digit recharge tokens directly in the chat window.

### 5. `WhatsAppKycHandler` (`WhatsAppKycHandler.ts`)
1. **Identity Upgrades**: Enter NIN or upload utility bills via chat to upgrade to Tier 2 and Tier 3.
2. **Multi-Currency Balances**: Instant display of active balances across NGN, USD, EUR, and GBP wallets with recent transaction summaries.

---

## 4.5 Dynamic Response Service (`WhatsAppResponseService`)

The response builder (`src/whatsapp-banking/services/WhatsAppResponseService.ts`) handles rich visual formatting for WhatsApp:

- **Interactive Quick-Reply Buttons**: Renders structured button cards (e.g. `[Transfer Money]`, `[Buy Airtime]`, `[Check Balance]`).
- **Interactive List Sections**: Multi-row selection menus for banks, telcos, and utility providers.
- **Meta WhatsApp Flows**: Supports JSON data exchanges (`/flow/data-exchange`) for complex multi-screen inputs.
- **Rich Receipt Cards**: Formats transaction confirmation cards with timestamp, reference code, beneficiary details, and remaining wallet balance.

---

## 4.6 Real-Time Event Bus & WhatsApp Alerts

The in-memory event bus (`src/events/EventBus.ts`) connects core banking events directly to WhatsApp notifications:

```
[Virtual Account Created] ────► [VirtualAccountCreatedHandler] ────► [Send WhatsApp NUBAN Welcome Card]
[KYC Tier Upgraded]       ────► [KycTierUpgradedHandler]       ────► [Send WhatsApp Tier Alert + Release Holds]
[Transaction Completed]   ────► [NotificationDispatchedHandler] ───► [Send Real-Time WhatsApp Receipt]
```

---

## 4.7 FCM Multi-Platform Push Notification Pipeline

The platform supports real-time push notifications across Android, iOS, and Web devices using Google Firebase Cloud Messaging (FCM) (`src/services/PushNotificationService.ts`).

### Multi-Device Registration & Invalidation Architecture

```
[Mobile / Web Client] ──► POST /user/device-token ──► [Save in `sys_device_tokens`]
                                                               │
                                                               ▼
[Transaction Event Occurs] ──► [PushNotificationService.sendToUser(userId, title, body)]
                                                               │
                                                               ▼
                                             [Firebase Admin SDK Dispatch]
                                                               │
                                         ┌─────────────────────┴─────────────────────┐
                                         ▼                                           ▼
                                 [Device Online]                             [Device Uninstalled]
                                         │                                           │
                                         ▼                                           ▼
                             [Deliver Push Alert]                    [FCM Error: `registration-token-not-registered`]
                                                                                     │
                                                                                     ▼
                                                                     [Auto-deactivate token (`is_active = false`)]
```

### Push Token Data Model (`sys_device_tokens`)

```prisma
model DeviceToken {
  id          BigInt             @id @default(autoincrement())
  user_id     BigInt
  token       String             @unique @db.VarChar(500)
  platform    PushDevicePlatform @default(ANDROID) // WEB, IOS, ANDROID
  device_id   String?            @db.VarChar(100)
  app_version String?            @db.VarChar(50)
  is_active   Boolean            @default(true)
  created_at  DateTime           @default(now()) @db.Timestamptz(6)
  updated_at  DateTime           @updatedAt @db.Timestamptz(6)

  @@index([user_id, is_active])
}
```

### Self-Healing Token Invalidation
When an FCM push dispatch fails with an error code such as `messaging/registration-token-not-registered` or `messaging/invalid-registration-token` (indicating the user uninstalled the app or invalidated the token), `PushNotificationService` automatically sets `is_active = false` for that device token record. This prevents future wasted network calls and optimizes push delivery rates.

---

## 4.8 Multi-Channel Notification Dispatcher

The application includes a unified notification dispatcher (`src/events/handlers/NotificationDispatchedHandler.ts`) that orchestrates alerts across four concurrent channels:

| Notification Channel | Delivery Mechanism | Fallback Handling |
| :--- | :--- | :--- |
| **WhatsApp Chat Alerts** | Active WhatsApp Provider (`IWhatsAppProvider`) | Retried via Transactional Outbox. |
| **FCM Push Notification** | Firebase Admin SDK (`sys_device_tokens`) | Self-healing invalidation on uninstall. |
| **Email SMTP Alert** | Mailpit (Dev) / SendGrid / Brevo (Prod) | Retried automatically via Outbox Queue. |
| **In-App Notification Center** | `Notification` Table in Database | Persisted for in-app inbox display (`isRead = false`). |

---

## 4.9 Summary

By combining compounding Safelock yields, multi-provider WhatsApp conversational banking, Redis session state machines, and FCM self-healing push notifications, Riverbrand delivers a rich, highly resilient multi-channel digital banking experience.

*Next Chapter: [05. Security, Revocation & Auditing](./05-security-compliance-and-auditing.md) — Dual-Token Security, Sidecar Revocation, RBAC & Audit Trails.*
