# 📄 Chapter 3: Core Banking & Financial Engine

> **"Financial Ledger, Money Movement & Double-Spending Prevention"**  
> *Deep-dive technical specification on atomic ledger debits, distributed locking, virtual NUBAN generation, pending balance locks, and daily limit tracking.*

---

## 3.1 The "Learn, Unlearn, Relearn" Guide to Money Movement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🚫 UNLEARN: "A database transaction alone is enough to stop double spending"│
│ If a user clicks 'Transfer ₦10k' from two phone tabs at the exact same     │
│ millisecond, both read `balance = ₦10k` before either commits, leading to   │
│ negative balances and irreversible bank loss.                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 💡 LEARN: "Concurrency in distributed systems requires two layers of guards"│
│ Layer 1: Distributed lock in memory (Redis Redlock) to serialize requests.  │
│ Layer 2: ACID row-level locking & single-commit database transactions.      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🚀 RELEARN & MASTER: "Riverbrand's Quantum Ledger Engine"                   │
│ Every debit acquires a 10s Redis mutex lock on `lock:wallet:{walletId}`,    │
│ validates daily limits, mutates balance, writes double-entry ledger rows,   │
│ queues the outbox event, and commits in one atomic step.                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3.2 Double-Spending Prevention & Atomic Balance Locking

```
[Incoming Debit Request] 
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ TIER 1: Distributed Redis Lock (utils/lock.ts)          │
│ Lock Key: `lock:wallet:{walletId}` (TTL: 10 Seconds)    │
└─────────────────────────────────────────────────────────┘
         │
         ├──► [Acquired Lock Successfully]
         │          │
         │          ▼
         │  ┌──────────────────────────────────────────────────────────┐
         │  │ TIER 2: Database Isolation Transaction ($transaction)    │
         │  │  1. Check Daily Limit: totalDebits + amount <= limit     │
         │  │  2. SELECT balance FROM "Wallet" WHERE id = walletId;   │
         │  │  3. Verify: balance >= debitAmount                      │
         │  │  4. UPDATE "Wallet" SET balance = balance - debitAmount │
         │  │  5. INSERT INTO "transactions" (...)                    │
         │  │  6. INSERT INTO "outbox" (...)                          │
         │  │  7. COMMIT TRANSACTION                                  │
         │  └──────────────────────────────────────────────────────────┘
         │          │
         │          ▼
         │  [Release Redis Lock] ──► [Return 200 OK Response]
         │
         └──► [Lock Rejected / Busy] ──► [Return 409 Conflict Response]
```

### 1. Redis Distributed Lock (`src/utils/lock.ts`)
- Before mutating balances, the engine invokes `acquireLock(`wallet:${walletId}`, 10000)`.
- If another process holds the lock, incoming concurrent requests are blocked or cleanly rejected with `HTTP 409 Conflict` (*"A transaction is already in progress on this account"*).

### 2. Prisma Database Transaction Isolation (`$transaction`)
- Balance deduction executes inside `prisma.$transaction(async (tx) => { ... })`.
- Balances are decremented atomically with SQL consistency, guaranteeing that ledger totals strictly match wallet balances.

---

## 3.3 Virtual Account Provisioning Lifecycle

Dedicated virtual bank accounts (NUBANs) allow customers to fund their Riverbrand wallets by transferring money from any commercial bank in Nigeria.

### Gateway Architecture (`src/services/userProvisioning.ts`)

```mermaid
sequenceDiagram
    autonumber
    actor User as Registered Customer
    participant API as Fastify API Server
    participant DB as PostgreSQL Database
    participant Providus as ProvidusBank API
    participant Fincra as Fincra Gateway API

    User->>API: POST /user/provision-virtual-account
    API->>DB: Check if Virtual Account already exists
    alt Account Exists
        DB-->>API: Return existing NUBAN details
        API-->>User: 200 OK (Virtual Account Details)
    else Account Does Not Exist
        API->>Providus: Request NUBAN Generation (BVN / Name / Email)
        alt Providus Success
            Providus-->>API: Return NUBAN (e.g. 9920123456)
        else Providus Failure / Fallback
            API->>Fincra: Request Virtual Account Generation
            Fincra-->>API: Return NUBAN (e.g. 8031234567)
        end
        API->>DB: INSERT INTO user_account_details (accountNumber, providerName, user_id)
        API->>DB: INSERT INTO rbp_brand_references (purpose: ACCOUNT_CREATION)
        API-->>User: 201 Created (Dedicated Virtual Account Numbers)
    end
```

---

## 3.4 Transaction Processing & Reference Tracking

Every money movement operation is assigned a cryptographically unique reference to enforce **idempotency** and prevent duplicate billing across retries.

### Reference System Architecture (`src/utils/referenceGenerator.ts`)

| Purpose (`ReferencePurpose`) | Format Example | Description |
| :--- | :--- | :--- |
| `ACCOUNT_CREATION` | `REF-ACT-20260815-9A8B7C` | Dedicated NUBAN virtual account creation reference. |
| `TRANSFER` | `TRF-NGN-20260815-88392011` | Interbank or P2P transfer reference. |
| `DEPOSIT` | `DEP-PRV-20260815-77182900` | Inbound deposit webhook reference from Providus/Fincra. |
| `SAVINGS` | `SAV-FLK-20260815-33411099` | Safelock or Target Savings deposit lock reference. |
| `BILL_PAYMENT` | `BIL-AIR-20260815-44910288` | Airtime, Data, Electricity, or Cable TV bill payment ref. |
| `CARD_PAYMENT` | `CRD-FLW-20260815-11029388` | Debit card funding transaction reference. |

---

## 3.5 Pending Balance Holding & Release Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🧠 MENTAL MODEL: The Holding Escrow                                         │
│                                                                             │
│ If a Tier 1 customer (daily limit ₦50k) receives a ₦500k transfer, we do    │
│ NOT reject the money. We credit ₦50k to their main wallet, and hold ₦450k   │
│ safely in `rbp_brand_pending_balance`. As soon as they verify their BVN,     │
│ the held ₦450k is automatically unlocked into their available balance!       │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
[Inbound Deposit Webhook (e.g. ₦500,000)]
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│ Check User KYC Tier Daily Ceiling (rbp_brand_kyc_benefit)│
│ Current User Tier: TIER 1 (Daily Limit: ₦50,000)       │
└────────────────────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
[Within Limit: ₦50,000]   [Exceeds Limit: ₦450,000]
         │                   │
         ▼                   ▼
[Credit Main Wallet]     [Lock in `rbp_brand_pending_balance`]
                             │
                             ▼
                         [Log Audit Trail (`rbp_brand_pending_balance_audit`)]
                             │
                             ▼
       [Customer Uploads BVN / NIN ➔ Upgraded to TIER 2]
                             │
                             ▼
             [Pending Balance Auto-Released to Main Wallet]
```

### Technical Workflow (`src/services/monetary/pendingBalance.ts`)
1. **Limit Evaluation**: Compares total debits/credits for the current calendar day against the tier limit.
2. **Pending Hold Insertion**: Any excess balance is written to `rbp_brand_pending_balance` with status `PENDING`.
3. **Audit Log Trail**: An entry is appended to `rbp_brand_pending_balance_audit` recording `action = INITIAL_HOLD`.
4. **Automated Tier Upgrade Trigger (`src/events/handlers/KycTierUpgradedHandler.ts`)**: When Dojah validates the user's BVN or NIN, `releasePendingBalances(userId)` is triggered, releasing held funds into available balance automatically.

---

## 3.6 Daily Limits & Tier Compliance Tracking

The system tracks daily transaction volume per user using `rbp_brand_daily_limit_tracker`:

```prisma
model rbp_brand_daily_limit_tracker {
  id          String    @id @default(uuid()) @db.Uuid
  userId      BigInt    @map("user_id")
  date        String    @db.VarChar(10) // Format: "YYYY-MM-DD"
  totalDebits Decimal   @default(0) @map("total_debits") @db.Decimal(20, 2)
  updatedAt   DateTime  @updatedAt @map("updated_at") @db.Timestamptz(6)

  @@unique([userId, date])
}
```

### KYC Tier Ceilings (`rbp_brand_kyc_benefit`)

| User KYC Tier | Daily Transfer Limit | Maximum Wallet Balance | Required Verification Items |
| :--- | :--- | :--- | :--- |
| **`TIER1`** | ₦50,000.00 | ₦300,000.00 | Verified Phone Number & Email |
| **`TIER2`** | ₦200,000.00 | ₦500,000.00 | BVN or NIN Verification via Dojah Gateway |
| **`TIER3`** | ₦5,000,000.00 | Unlimited | Government Photo ID & Proof of Address Upload |

---

*Next Chapter: [04. Savings, WhatsApp & Channels](./04-savings-investments-and-channels.md) — Wealth Engine, WhatsApp Banking & FCM Notifications.*
