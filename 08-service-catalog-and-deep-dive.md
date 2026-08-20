# 📄 Chapter 8: Complete Backend Service Catalog & Deep-Dive Specification

> **"Line-by-Line Service Specifications & Integration Reference"**  
> *Exhaustive engineering specification detailing business logic, input/output schemas, database dependencies, external integrations, error handling, and configuration flags for every service in RiverbrandBE.*

---

## 8.1 The "Learn, Unlearn, Relearn" Guide to Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🚫 UNLEARN: "Controllers should write SQL queries directly to tables."      │
│ Bloating HTTP controllers with SQL queries creates unmaintainable code and  │
│ makes testing and swapping external vendors nearly impossible.              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 💡 LEARN: "Services encapsulate pure business domain logic."                │
│ Controllers handle HTTP validation, Services execute business rules and     │
│ transactions, and Repositories handle database persistence.                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🚀 RELEARN & MASTER: "Riverbrand's Dependency-Injected Domain Services"    │
│ We use TypeDI (`typedi`) for constructor-based Dependency Injection. Every │
│ domain service (Auth, Ledger, Savings, WhatsApp, KYC) is isolated, testable,│
│ and emits events asynchronously via the EventBus and Outbox Relay.          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8.2 Overview & Service Architecture Map

The Riverbrand Banking Platform consists of 31+ core domain services grouped into 7 functional categories:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 RIVERBRAND SERVICE CORE                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
  ├── 🛡️ A. Auth & Security      (AuthService, OtpService, SecurityQuestion, Role, Perm)
  ├── 🏦 B. Financial & Wallet    (FinancialEngine, Wallet, Account, Provisioning, Pending)
  ├── 💸 C. Payments & Cards     (Transaction, BillPayment, Flutterwave, Providus, Pin)
  ├── 📈 D. Wealth & Investments (SavingsService - Safelock, Target Savings, AutoSave)
  ├── 🆔 E. KYC & Verification   (User, KycService, Verification, UserDoc, AdminKyc)
  ├── 💬 F. Channels & Messaging (WhatsAppBanking, PushNotification, DeviceToken, Alert)
  └── 📊 G. Governance & Health  (Admin, AdminAccount, Metrics, HealthCheck)
```

---

## 8.3 Category A: Authentication & Security Services

### 1. `AuthService` (`src/services/auth.ts`)
- **Business Purpose**: Core authentication orchestrator managing user sign-up, sign-in validation, JWT access token generation, password resets, and sidecar session control.
- **Key Methods**:
  - `signUp(dto: SignUpDTO)`: Creates new user in `user_user`, hashes password using Argon2id/bcrypt, initializes default wallet (`NGN`), provisions sidecar session record in `river_brand_sys_user_session_control`, and emits `UserRegistered` event.
  - `signIn(dto: SignInDTO)`: Validates credentials, checks account suspension status, verifies client token type (`x-client-type: mobile` vs `web`), fetches `jwtVersion` from sidecar table, and issues signed JWT access tokens containing `jv` claim.
  - `signOut(userId: bigint)`: Increments `jwtVersion` in sidecar table `river_brand_sys_user_session_control`, instantly revoking active access tokens across all user devices.
- **Database Tables**: `user_user`, `river_brand_sys_user_session_control`, `Wallet`.
- **Error Handlers**: `INVALID_CREDENTIALS` (401), `USER_SUSPENDED` (403), `ACCOUNT_ALREADY_EXISTS` (409).

### 2. `OtpService` (`src/services/otp.ts`)
- **Business Purpose**: Generates, stores, delivers, and validates 6-digit cryptographically secure One-Time Passwords (OTPs) across SMS and email.
- **Key Methods**:
  - `requestOtp(userId: bigint, phone: string, context: string)`: Generates a 6-digit random code, inserts record into `riverbrand_sms_otp` (TTL 10 mins), and routes SMS via Termii primary gateway or Twilio fallback.
  - `verifyOtp(userId: bigint, phone: string, pin: string, context: string)`: Validates active OTP pin code, marks `is_verified = true`, and invalidates consumed PINs.
- **Dependencies**: Termii API Client (`termiiClient.ts`), Twilio API Client (`twilioClient.ts`).
- **Database Tables**: `riverbrand_sms_otp`.

### 3. `SecurityQuestionService` (`src/services/securityQuestion.ts`)
- **Business Purpose**: Manages customer recovery security questions and answer verification.
- **Key Methods**:
  - `getPublicQuestions()`: Fetches active security question library (`rbp_brand_security_question`).
  - `setUserAnswers(userId: bigint, answers: SecurityAnswerDTO[])`: Hashes user answers using bcrypt and stores them in `rbp_brand_user_security_question_answer`.
  - `verifyUserAnswer(userId: bigint, questionId: bigint, answer: string)`: Compares candidate answer against stored hash during account recovery workflows.
- **Database Tables**: `rbp_brand_security_question`, `rbp_brand_user_security_question_answer`.

### 4. `AdminSecurityQuestionService` (`src/services/adminSecurityQuestion.ts`)
- **Business Purpose**: Allows administrative staff to manage master security questions and multiple-choice options.
- **Methods**: `createQuestion()`, `updateQuestion()`, `deleteQuestion()`, `addOption()`.

### 5. `RoleService` (`src/services/RoleService.ts`) & `PermissionService` (`src/services/PermissionService.ts`)
- **Business Purpose**: Manages Role-Based Access Control (RBAC) definitions and staff permission matrices.
- **Database Tables**: `sys_roles`, `sys_permissions`, `sys_role_permissions`, `sys_user_roles`.

---

## 8.4 Category B: Core Financial & Wallet Engines

### 6. `FinancialEngine` (`src/services/monetary/financialEngine.ts`)
- **Business Purpose**: Master double-entry accounting engine handling low-level atomic ledger entries, balance additions, deductions, and cross-currency conversions.
- **Key Methods**:
  - `executeLedgerMovement(params: LedgerMovementDTO)`: Executes atomic SQL balance mutations within `$transaction` blocks while evaluating Redis distributed lock keys (`lock:wallet:{walletId}`).
- **Database Tables**: `Wallet`, `Transaction`, `payment_transaction`.

### 7. `WalletService` (`src/services/monetary/wallet/wallet.ts`)
- **Business Purpose**: Manages multi-currency customer wallets (NGN, USD, EUR, GBP), fetching balances, exchange rates, and wallet creation.
- **Key Methods**:
  - `getWalletBalance(userId: bigint, currency: string)`: Returns available and pending balances.
  - `convertCurrency(amount: Decimal, fromCurrency: string, toCurrency: string)`: Fetches rate from `ExchangeRate` matrix and calculates net conversion value.
- **Database Tables**: `Wallet`, `WalletCurrency`, `ExchangeRate`.

### 8. `AccountService` (`src/services/monetary/account/account.ts`)
- **Business Purpose**: Manages virtual NUBAN account records and dashboard summary displays.
- **Database Tables**: `userAccountDetails`, `user_user`.

### 9. `UserProvisioningService` (`src/services/userProvisioning.ts`)
- **Business Purpose**: Automated provisioning of dedicated virtual NUBAN bank accounts upon user registration.
- **Key Methods**:
  - `provisionVirtualAccount(userId: bigint)`: Requests NUBAN generation from ProvidusBank API. If Providus experiences an outage, automatically falls back to Fincra Gateway. Writes result to `userAccountDetails` and tracks reference in `rbp_brand_references`.
- **External Dependencies**: ProvidusBank API, Fincra API.

### 10. `PendingBalanceService` (`src/services/monetary/pendingBalance.ts`)
- **Business Purpose**: Enforces KYC daily transaction ceilings by holding excess deposit funds in `rbp_brand_pending_balance` and auto-releasing them upon identity tier upgrade.
- **Key Methods**:
  - `holdPendingBalance(userId: bigint, amount: Decimal, reference: string)`: Places funds in pending hold and appends entry to `rbp_brand_pending_balance_audit`.
  - `releasePendingBalances(userId: bigint)`: Triggered by `KycTierUpgradedHandler`. Releases held funds into primary wallet balance.
- **Database Tables**: `rbp_brand_pending_balance`, `rbp_brand_pending_balance_audit`.

### 11. `IdempotencyService` (`src/services/monetary/idempotency.ts`)
- **Business Purpose**: Deduplicates financial operations using cryptographic references (`rbp_brand_references`).

---

## 8.5 Category C: Payment & Transaction Services

### 12. `TransactionService` (`src/services/monetary/transaction/transaction.ts`)
- **Business Purpose**: Interbank transfers, P2P transfers, transaction history queries, and receipt generation.
- **Database Tables**: `Transaction`, `payment_transaction`, `user_user`.

### 13. `BillPaymentService` (`src/services/monetary/transaction/BillPaymentService.ts`)
- **Business Purpose**: Airtime, mobile data, Electricity, and Cable TV bill payments. Validates customer meter/card numbers before executing wallet debits.

### 14. `FlutterwaveTransactionService` (`src/services/monetary/transaction/flutterwaveTransaction.ts`)
- **Business Purpose**: Handles Flutterwave debit card top-ups, webhook verifications, and external payout clearing.

### 15. `ProvidusTransactionService` (`src/services/monetary/transaction/providusTransaction.ts`)
- **Business Purpose**: Validates inbound ProvidusBank deposit webhooks, verifying transaction signatures before crediting user wallets.

### 16. `FlutterwaveCardService` & `UserCardService`
- **Business Purpose**: Tokenizes saved debit cards (`UserCard`) for one-click wallet funding.

### 17. `PinService` (`src/services/monetary/pin/pin.ts`)
- **Business Purpose**: Manages 4-digit secret transaction PINs, bcrypt hashing, and temporary lockouts after 3 invalid attempts.

---

## 8.6 Category D: Wealth & Investment Services

### 18. `SavingsService` (`src/services/monetary/savings/savings.ts`)
- **Business Purpose**: Manages Safelock fixed deposits, Target Savings goals, AutoSave sweeps, and daily compounding interest accrual.
- **Key Methods**:
  - `createSafelock(userId: bigint, amount: Decimal, tenureDays: int)`: Debits wallet and locks funds in `Target` table (`savingsType = SAFELOCK`).
  - `processDailyInterestAccrual()`: Executed by nightly cron job (`src/job/savings.ts`). Accrues daily yield and writes interest logs to `savings_usersavinginterestlog`.
  - `liquidateMaturedSafelock(safelockId: bigint)`: Payouts principal + interest to user wallet on maturity date.

---

## 8.7 Category E: KYC, Verification & User Services

### 19. `UserService` (`src/services/user.ts`)
- **Business Purpose**: User profile management, avatar uploads to S3/Cloudinary, address updates, and account deletion requests.

### 20. `KycService` (`src/services/kyc.ts`) & `VerificationService` (`src/services/verification.ts`)
- **Business Purpose**: Verifies BVN and NIN identity details via Dojah Identity Gateway and Mono API. Upgrades user to Tier 2 upon success.

### 21. `UserDocumentService` (`src/services/userDocument.ts`)
- **Business Purpose**: Handles Tier 3 proof of address and government photo ID document uploads (`UserDocument`).

### 22. `AdminKycService` (`src/services/adminKyc.ts`)
- **Business Purpose**: Staff manual document verification portal and daily limit settings (`rbp_brand_kyc_benefit`).

### 23. `BeneficiaryService` (`src/services/beneficiary.ts`)
- **Business Purpose**: Consolidated beneficiary directory (`rbp_brand_beneficiaries`) across commercial banks, airtime numbers, and P2P tags.

---

## 8.8 Category F: Communication, WhatsApp & Messaging Services

### 24. `WhatsAppBankingService` (`src/whatsapp-banking/services/WhatsAppBankingService.ts`)
- **Business Purpose**: Core conversational banking orchestrator. Receives normalized inbound messages from `WhatsAppController`, queries/updates Redis conversational state via `WhatsAppSessionService`, pairs sender phone numbers to `user_user` accounts, and delegates input execution to specialized domain step handlers.
- **Key Methods**:
  - `handleIncomingMessage(parsedMessage: ParsedWhatsAppMessage)`: Ingestion pipeline that deduplicates message IDs, checks 30-minute brute-force lockout status, maps phone numbers to verified database users, detects global navigation keywords (`HI`, `MENU`, `CANCEL`, `RESET`), and dispatches to registered `stepHandlers`.
  - `handleIdleStep(to: string, command: string, session: WhatsAppUserSession)`: Renders contextual interactive menus based on authentication status (Guest Onboarding Menu vs Authenticated Dashboard Menu).
- **Database Tables**: `user_user`, `Wallet`, `userAccountDetails`.
- **Cache**: Redis (`wa:session:*`, `wa:lockout:*`, `wa:msg:*`).

### 25. `WhatsAppSessionService` (`src/whatsapp-banking/services/WhatsAppSessionService.ts`)
- **Business Purpose**: Manages in-memory stateful conversational sessions across WhatsApp chat turns without database overhead.
- **Key Methods**:
  - `getSession(phoneNumber: string)`: Retrieves or initializes `WhatsAppUserSession` with 30-minute TTL.
  - `saveSession(session: WhatsAppUserSession)`: Persists step state, dynamic step data (`sessionData`), and updates TTL.
  - `isDuplicateMessage(messageId: string)`: Deduplicates webhook retries using 24-hour Redis key markers.
  - `recordFailedPinAttempt(phoneNumber: string)`: Increments failed attempt counter; triggers 30-minute lockout when count reaches 3.
  - `clearSession(phoneNumber: string)`: Resets session back to `WhatsAppStep.IDLE`.

### 26. `WhatsAppResponseService` (`src/whatsapp-banking/services/WhatsAppResponseService.ts`)
- **Business Purpose**: Visual and interactive message formatting engine for WhatsApp.
- **Key Methods**:
  - `sendInteractiveButtons(to, bodyText, buttons, footerText)`: Sends WhatsApp interactive button message cards.
  - `sendInteractiveList(to, title, bodyText, buttonText, sections)`: Sends multi-section selectable list menus (e.g. bank lists, telco plans).
  - `sendTopLevelMenu(to, userFullName, isAuthenticated)`: Generates dynamic home screen menus with emoji headers.
  - `sendReceiptCard(to, receiptDetails)`: Generates clean monospaced financial receipt cards.

### 27. `WhatsAppProviderFactory` (`src/whatsapp-banking/providers/WhatsAppProviderFactory.ts`)
- **Business Purpose**: Dependency Injection factory dynamically resolving the active WhatsApp gateway adapter (`IWhatsAppProvider`) based on environment configuration (`meta`, `twilio`, `termii`, `wati`, `interakt`, `360dialog`).

### 28. `WhatsAppRegistrationHandler` (`src/whatsapp-banking/services/handlers/WhatsAppRegistrationHandler.ts`)
- **Business Purpose**: End-to-end chat onboarding workflow. Captures customer name, dispatches and validates email OTP, verifies BVN with Dojah, captures photo selfie, hashes secret 4-digit transaction PIN, and triggers automatic Providus/Fincra NUBAN provisioning.

### 29. `WhatsAppTransferHandler` (`src/whatsapp-banking/services/handlers/WhatsAppTransferHandler.ts`)
- **Business Purpose**: Conversational money movement. Manages NUBAN account entry, live bank account name resolution, multi-currency wallet selection (NGN, USD, EUR, GBP), PIN authorization, distributed `Redlock` acquisition, and atomic ledger execution.

### 30. `WhatsAppAirtimeHandler` (`src/whatsapp-banking/services/handlers/WhatsAppAirtimeHandler.ts`)
- **Business Purpose**: Chat-based mobile top-up and data bundle purchase across MTN, Airtel, Glo, and 9mobile with PIN authentication.

### 31. `WhatsAppBillPaymentHandler` (`src/whatsapp-banking/services/handlers/WhatsAppBillPaymentHandler.ts`)
- **Business Purpose**: Utility bill payments (Electricity prepaid token generation, postpaid settlement, DSTV/GOTV smartcard renewals).

### 32. `WhatsAppKycHandler` (`src/whatsapp-banking/services/handlers/WhatsAppKycHandler.ts`)
- **Business Purpose**: Chat-based KYC verification (NIN submission, selfie document capture) and real-time multi-currency wallet balance inquiries.

### 33. `PushNotificationService` (`src/services/PushNotificationService.ts`)
- **Business Purpose**: FCM multi-platform push notification dispatcher with self-healing invalidation on app uninstalls (`sys_device_tokens`).

### 34. `DeviceTokenService` (`src/services/DeviceTokenService.ts`)
- **Business Purpose**: Multi-device FCM token registration across iOS, Android, and Web platforms.

### 35. `NotificationService` (`src/services/notification.ts`)
- **Business Purpose**: In-app inbox notifications and dispute ticket submissions.

### 36. `AlertDispatcherService` (`src/services/alerting/AlertDispatcherService.ts`)
- **Business Purpose**: Pluggable alert dispatcher for broadcasting platform alerts to Slack, Email, and Webhook receivers.

---

## 8.9 Category G: Governance & Observability Services

### 37. `AdminService` (`src/services/AdminService.ts`) & `AdminAccountService` (`src/services/adminAccount.ts`)
- **Business Purpose**: Executive platform dashboard metrics, user suspension/unsuspension, and financial liability stats.

### 38. `MetricsService` (`src/services/metrics/metricsService.ts`)
- **Business Purpose**: Prometheus counter, gauge, and histogram metric collection (`prom-client`) served on port `9095`.

### 39. `HealthCheckService` (`src/services/health/healthCheckService.ts`)
- **Business Purpose**: System health diagnostics pinging PostgreSQL, Redis, Mailpit SMTP, and Outbox queues (`/health/liveness` & `/health/readiness`).

---

## 8.10 Summary Matrix: Services & Dependencies

| Service Name | Primary Model / Table | External Gateway Dependency | Key Security Mechanism |
| :--- | :--- | :--- | :--- |
| **`AuthService`** | `user_user`, `session_control` | None | Argon2id + Sidecar `jwtVersion` |
| **`OtpService`** | `riverbrand_sms_otp` | Termii SMS / Twilio SMS | 6-Digit Random + 10m Expiry |
| **`FinancialEngine`** | `Wallet`, `Transaction` | None | Redis Lock + SQL `$transaction` |
| **`UserProvisioningService`** | `userAccountDetails` | ProvidusBank / Fincra | NUBAN Gateway Failover |
| **`PendingBalanceService`** | `rbp_brand_pending_balance` | None | Audit Trail (`pending_audit`) |
| **`TransactionService`** | `payment_transaction` | Interbank Clearing | Reference Idempotency |
| **`SavingsService`** | `Target`, `savings_config` | None | Daily Compound Yield Math |
| **`KycService`** | `user_user` | Dojah Gateway / Mono API | BVN & NIN Verification |
| **`WhatsAppBankingService`** | `user_user`, `Wallet` | Meta / Twilio / Termii / WATI | HMAC Signature + PIN Auth |
| **`WhatsAppSessionService`** | Redis (`wa:session:*`) | In-Memory Redis 7 | 30m TTL + 3-Attempt Lockout |
| **`WhatsAppTransferHandler`** | `Wallet`, `Transaction` | Interbank Clearing | Distributed Redlock + PIN |
| **`WhatsAppRegistrationHandler`** | `user_user`, `userAccountDetails` | Dojah / Providus / Fincra | OTP Email + BVN Match |
| **`PushNotificationService`** | `sys_device_tokens` | Google Firebase FCM | Self-Healing Token Invalidation |

---

*End of Chapter 8 Backend Service Catalog.*
