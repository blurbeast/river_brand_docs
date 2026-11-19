# Appendix C: Data Dictionary

This appendix is the book's single table-by-table reference for the RiverbrandBE persistence layer. Every table the old documentation suite names appears here with its purpose in plain words and in technical terms, the key columns the old docs actually document, and — the part most reference docs skip — who writes each table and who reads it. Where the old documentation does not state a fact, the entry says **UNVERIFIED** rather than guessing. That policy is deliberate: this book was rebuilt from the 2026 documentation suite alone, and a data dictionary that invents column types is worse than one that admits ignorance. Marked entries are tracked in the [UNVERIFIED register](app-g-changelog.md#unverified-register); a marker can only be retired against the live codebase.

## The Prefix Map in One Page

Before the entries, the philosophy. Table names in RiverbrandBE carry their generation in their prefix, and [§3.5 The Schema-Prefix Map](../chapters/ch03-domain-primer.md#35-the-schema-prefix-map) is the canonical map. In brief: `rbp_brand_*` is current domain design — if a table carries this prefix, it is the shape we intend to keep. `river_brand_sys_*` is platform machinery (session control and its kin), deliberately kept out of the domain namespace so legacy tables need not be altered. `savings_*` and `user_user` are legacy names inherited from earlier iterations of the codebase; they are documented here as-is because the code still uses them, and they are flagged to-be-renamed. Finally, a set of un-prefixed Prisma model names — `Wallet`, `Target`, `ExchangeRate`, `GLJournalEntry`, `GLJournalLine`, `GLBalanceSnapshot`, `DeviceToken` — map to wallet, savings, FX, general-ledger, and device tables; they are neither legacy nor `rbp_brand_`-conventional, and the rule for new work is not to add to their number. This appendix follows the prefix map: entries are grouped by domain, not by spelling, but every entry states its naming status.

## How to Read an Entry

Each entry has four beats. **Purpose** gives the plain-language job of the table, then the technical one. **Key columns** lists only columns the old documentation actually names, with the type as documented; anything else is **UNVERIFIED** in the type cell, and columns the docs never name are not invented — their absence is stated. **Written by** names the services or jobs the old docs credit with writes. **Read by** names the consumers. Cross-references point into the engineering chapters where the mechanism is specified.

## Identity and Accounts

### user_user

**Purpose.** In plain words: the customer record — the row that says who you are, the way a bank's register of account holders does. Technically: the legacy identity table that `AuthService.signUp` creates on registration (hashing the password, initializing a default `NGN` wallet, provisioning the session sidecar), that `AuthService.signIn` reads for credential and suspension checks, and that `WhatsAppBankingService` queries to pair an inbound sender's phone number with a verified account. It is a legacy name — flagged to-be-renamed under [§3.5](../chapters/ch03-domain-primer.md#35-the-schema-prefix-map) — kept as-is because altering it would break legacy services.

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| password | **UNVERIFIED** | Hashed credential. The old docs specify the storage model `user_user.password` and the algorithm: Argon2id with memory 64MB, iterations 3, parallelism 4; five failed attempts trigger a 15-minute account lock. |
| (phone identifier) | **UNVERIFIED** | The identifier `WhatsAppBankingService` uses to map a WhatsApp sender to a database user. The old docs describe the pairing but never name the column. |
| (KYC tier) | **UNVERIFIED** | The tier attribute raised from `TIER1` to `TIER2` on successful BVN/NIN verification via the Dojah gateway. Column name not documented. |

**Written by.** `AuthService` at sign-up; `UserService` for profile, avatar, and address updates; `KycService` on tier upgrade. **Read by.** `AuthService.signIn`, `WhatsAppBankingService`, `AccountService`, `TransactionService`, and `KycService`.

### userAccountDetails

**Purpose.** Plain: the record of your dedicated bank account number — the NUBAN you pay money into to fund your wallet. Technically: the virtual-account provisioning table, inserted when `UserProvisioningService.provisionVirtualAccount` obtains a NUBAN from ProvidusBank and, on Providus failure, falls back to the Fincra gateway. The documented insert is `INSERT INTO userAccountDetails (accountNumber, providerName, user_id)`.

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| accountNumber | **UNVERIFIED** | The NUBAN itself (the old docs show examples such as `9920123456` from Providus and `8031234567` from Fincra). |
| providerName | **UNVERIFIED** | Which gateway minted the account — Providus or Fincra — so later deposit webhooks know which rail to expect. |
| user_id | **UNVERIFIED** | Owning customer. Service signatures type `userId` as `bigint` in the old code excerpts, but the column type is not documented. |

**Written by.** `UserProvisioningService`; `WhatsAppRegistrationHandler` at the end of chat onboarding. **Read by.** `AccountService` (dashboard summaries), `WhatsAppBankingService`, deposit-webhook handlers such as `ProvidusTransactionService`.

### riverbrand_sms_otp

**Purpose.** Plain: the one-time codes you receive by SMS or email. Technically: the OTP store written by `OtpService.requestOtp`, which generates a 6-digit cryptographically secure code, persists it with a 10-minute expiry, and routes delivery through the Termii gateway with Twilio as fallback. `OtpService.verifyOtp` validates a candidate code, marks `is_verified = true`, and invalidates consumed codes. Naming note: the security chapter of the old suite spells this store `riverbrandsmsotp` while the service catalog spells it `riverbrand_sms_otp`; the underscored form is used here, and the discrepancy is carried in the [errata](app-g-changelog.md#errata) template as an open naming question.

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| is_verified | **UNVERIFIED** | Flag set to true once a code has been successfully verified. |
| (code / pin) | **UNVERIFIED** | The 6-digit code itself, passed as `pin` in the documented `verifyOtp` signature. Column name not documented. |

**Written by.** `OtpService.requestOtp`. **Read by.** `OtpService.verifyOtp`; the WhatsApp registration flow (`WhatsAppRegistrationHandler`) for email OTP dispatch and validation.

## Wallets and Ledger

### Wallet

**Purpose.** Plain: the money box — one per currency you hold — whose balance you see on the dashboard. Technically: the multi-currency wallet model managed by `WalletService` (NGN, USD, EUR, GBP) and mutated by `FinancialEngine.executeLedgerMovement` inside a single-commit database transaction: decrement the source balance, increment the destination balance, then write the double-entry ledger rows and an outbox event before commit. `AuthService.signUp` initializes a default `NGN` wallet at registration. This is an un-prefixed Prisma model name (see [§3.5](../chapters/ch03-domain-primer.md#35-the-schema-prefix-map)).

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| id | **UNVERIFIED** | Wallet identity; interpolated into the distributed-lock key `lock:wallet:{walletId}` with a 10-second TTL. |
| balance | **UNVERIFIED** | The available balance, mutated only through atomic increment/decrement inside the guarded transaction. Amount parameters in the old service signatures are typed `Decimal`. |

**Written by.** `FinancialEngine` (all atomic movements), `PendingBalanceService.releasePendingBalances` (auto-release after KYC upgrade), `SavingsService` (Safelock debits and maturity payouts). **Read by.** `WalletService.getWalletBalance` (available and pending balances), `WhatsAppBankingService` (balance inquiries across four currencies), and every debit-path limit check.

### WalletCurrency

**Purpose.** Plain: the list of currencies a wallet can hold. Technically: the per-currency wallet model named in `WalletService`'s database dependencies alongside `Wallet` and `ExchangeRate`, supporting the multi-currency semantics (NGN, USD, EUR, GBP) used by transfers, swaps, and WhatsApp balance inquiries.

**Key columns.** The old documentation names no columns for this model — **UNVERIFIED** beyond its role as the per-currency companion to `Wallet`.

**Written by.** `WalletService` at wallet creation — **UNVERIFIED** as to the exact write path. **Read by.** `WalletService` and the multi-currency selection steps of `WhatsAppTransferHandler`.

### ExchangeRate

**Purpose.** Plain: the price list for swapping one currency into another. Technically: the FX rate matrix that `WalletService.convertCurrency` reads to calculate the net conversion value for a `Decimal` amount moving between two currencies. An un-prefixed model name.

**Key columns.** The old documentation names no columns — **UNVERIFIED**. What is documented is the read pattern: fetch the rate from the `ExchangeRate` matrix, then compute the net conversion.

**Written by.** **UNVERIFIED** — the old docs never say who maintains or refreshes the rate matrix. **Read by.** `WalletService.convertCurrency`; currency-swap paths of `FinancialEngine`.

### GLJournalEntry

**Purpose.** Plain: one page in the master ledger book — a single business movement. Technically: the journal header of the double-entry general ledger, written by `GeneralLedgerService` for every money movement alongside its lines. Listed among the un-prefixed ledger model names in [§3.5](../chapters/ch03-domain-primer.md#35-the-schema-prefix-map).

**Key columns.** The old documentation names no columns — **UNVERIFIED** beyond the header role and the invariant that every entry's debits equal its credits.

**Written by.** `GeneralLedgerService`, always inside the same single-commit transaction as the wallet mutations. **Read by.** `GeneralLedgerJob` (daily snapshotting and balance validation), reconciliation and audit paths.

### GLJournalLine

**Purpose.** Plain: one line on that ledger page — a debit or a credit. Technically: the immutable double-entry lines attached to a `GLJournalEntry`, the third layer of the concurrency guard: layer one serializes with a distributed lock, layer two commits atomically, layer three proves the books balance.

**Key columns.** The old documentation names no columns — **UNVERIFIED** beyond the debit/credit role of each line.

**Written by.** `GeneralLedgerService` in the same transaction as the entry header. **Read by.** `GeneralLedgerJob`, auditors (`FINANCIAL_AUDITOR` role reads the audit surface per the RBAC matrix).

### GLBalanceSnapshot

**Purpose.** Plain: a daily photograph of every ledger account. Technically: the snapshot table written by `GeneralLedgerJob` (`src/job/generalLedgerJob.ts`), which takes automated daily snapshots of all GL accounts and validates that total assets equal total liabilities plus equity. An un-prefixed model name.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** `GeneralLedgerJob` on its daily run. **Read by.** Balance validation inside the same job; downstream reporting and audit consumers are **UNVERIFIED** in the old docs.

## Payments and Transactions

### Transaction

**Purpose.** Plain: the receipt book — one row for every movement of money you make. Technically: the transaction-history model named in the database dependencies of `FinancialEngine` and `TransactionService`, covering interbank transfers, peer-to-peer transfers, history queries, and receipt generation. Each movement carries a cryptographic reference (see `rbp_brand_references` below) so a retried request can never move money twice.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** `FinancialEngine` inside the guarded transaction; `WhatsAppTransferHandler` for chat-initiated transfers. **Read by.** `TransactionService` (history and receipts), `ReconciliationJob` (internal-versus-clearing comparison).

### payment_transaction

**Purpose.** Plain: the record of a payment that leaves or arrives through an outside provider. Technically: the provider-side payment model named in `TransactionService`'s dependencies and listed as its primary model in the service summary matrix, used for interbank clearing and card top-ups via Flutterwave, and for inbound deposit validation via Providus.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** `FlutterwaveTransactionService` (card top-ups, payout clearing), `ProvidusTransactionService` (validated inbound deposit webhooks), `BillPaymentService`. **Read by.** `TransactionService`, `BillReconciliationJob` (bill debits audited against vendor responses, with automated refunds for confirmed failures).

### UserCard

**Purpose.** Plain: your saved debit card, stored so you can top up in one tap. Technically: the tokenized card model managed by `FlutterwaveCardService` and `UserCardService`, which store card tokens rather than raw card data for one-click wallet funding.

**Key columns.** The old documentation names no columns — **UNVERIFIED** beyond the tokenization role.

**Written by.** `FlutterwaveCardService` at tokenization. **Read by.** `UserCardService` and the card-funding path of `FlutterwaveTransactionService`.

### rbp_brand_references

**Purpose.** Plain: the unique serial number stamped on every money movement, so the same request processed twice counts once. Technically: the idempotency reference table that `IdempotencyService` deduplicates against, fed by the cryptographic reference generator (`src/utils/referenceGenerator.ts`). The documented `ReferencePurpose` values and their formats are `ACCOUNT_CREATION` (`REF-ACT-20260815-9A8B7C`), `TRANSFER` (`TRF-NGN-20260815-88392011`), `DEPOSIT` (`DEP-PRV-20260815-77182900`), `SAVINGS` (`SAV-FLK-20260815-33411099`), `BILL_PAYMENT` (`BIL-AIR-20260815-44910288`), and `CARD_PAYMENT` (`CRD-FLW-20260815-11029388`). This is a current-domain `rbp_brand_*` table. The mechanism is specified in [§5.3 Idempotency References](../chapters/ch05-engineering-transaction-engine.md#53-idempotency-references).

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| purpose | **UNVERIFIED** (typed `ReferencePurpose` in the old payload interface) | Which kind of operation the reference stamps — one of the six values above. |
| (reference string) | **UNVERIFIED** | The generated reference itself, following the purpose-specific format. Column name not documented. |

**Written by.** The reference generator at the head of every money movement; `UserProvisioningService` inserts one with `purpose: ACCOUNT_CREATION` on NUBAN creation. **Read by.** `IdempotencyService` as the deduplication check inside the guarded transaction.

### rbp_brand_beneficiaries

**Purpose.** Plain: your saved recipients — the people and bills you pay often. Technically: the consolidated beneficiary directory that `BeneficiaryService` maintains across commercial banks, airtime numbers, and peer-to-peer tags.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** `BeneficiaryService` (including the `saveBeneficiary` option on the atomic debit payload). **Read by.** Transfer and bill-payment flows that prefill recipient details.

## Compliance, Limits, and Audit

### rbp_brand_kyc_benefit

**Purpose.** Plain: the rulebook that says how much money a verified customer may move and hold. Technically: the KYC tier ceiling table consulted before inbound deposits are credited, and the table `AdminKycService` edits when staff set daily limits. The documented ceilings are: `TIER1` — ₦50,000.00 daily transfer, ₦300,000.00 maximum wallet balance, phone and email verification; `TIER2` — ₦200,000.00 daily, ₦500,000.00 maximum, BVN or NIN verification via the Dojah gateway; `TIER3` — ₦5,000,000.00 daily, unlimited balance, government photo ID and proof of address.

**Key columns.** The old docs present the ceilings as a documentation table, not a column list. Exact column names for tier, daily transfer limit, maximum wallet balance, and verification requirement are **UNVERIFIED**.

**Written by.** `AdminKycService` (staff daily-limit settings). **Read by.** `PendingBalanceService` when an inbound deposit is checked against the user's tier ceiling.

### rbp_brand_daily_limit_tracker

**Purpose.** Plain: today's tally — how much of your daily allowance you have already used. Technically: the daily velocity tracker named in the automated compliance holding engine alongside `rbp_brand_pending_balance`, and checked inside the atomic debit path by `DailyLimitTrackerService` after the idempotency check and before the balance mutation.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** `DailyLimitTrackerService` as movements commit. **Read by.** `DailyLimitTrackerService` in the same guarded transaction.

### rbp_brand_pending_balance

**Purpose.** Plain: the holding tank — money that has arrived but is above your KYC ceiling, parked safely instead of bouncing. Technically: the quarantine table of the regulatory pending-balance engine. When an inbound deposit exceeds the tier ceiling, the allowed portion credits the wallet and the surplus is locked here under status `QUARANTINED`; when the customer upgrades tier (for example by uploading BVN or NIN), `PendingBalanceService.releasePendingBalances` — triggered by `KycTierUpgradedHandler` — releases the holds into the primary wallet. The mechanism is specified in [§5.6](../chapters/ch05-engineering-transaction-engine.md#56-the-pending-balance-holding-tank-and-kyc-ceilings).

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| (status) | **UNVERIFIED** | Lifecycle marker; the documented value `QUARANTINED` denotes funds held above the ceiling. Column name not documented. |
| (amount, reference) | **UNVERIFIED** | The held amount and its reference string, passed to `holdPendingBalance(userId, amount, reference)`. |

**Written by.** `PendingBalanceService.holdPendingBalance`. **Read by.** `PendingBalanceService.releasePendingBalances` on tier upgrade.

### rbp_brand_pending_balance_audit

**Purpose.** Plain: the notebook beside the holding tank — every hold written down as it happens. Technically: the append-only audit trail of the pending-balance engine; `holdPendingBalance` appends an entry here whenever funds are quarantined, so compliance can see not just the current hold but the history of holds and releases.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** `PendingBalanceService.holdPendingBalance` (and release paths — **UNVERIFIED**). **Read by.** Compliance and audit surfaces; the old docs do not name a specific reader service.

### UserDocument

**Purpose.** Plain: the ID card and proof of address you upload for the top KYC tier. Technically: the Tier 3 document store that `UserDocumentService` handles — government photo ID and proof-of-address uploads feeding the staff verification portal.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** `UserDocumentService` at upload. **Read by.** `AdminKycService` (manual document verification), `KycService` tier decisions.

### AuditUserActivity

**Purpose.** Plain: a tamper-evident diary of what customers do with their accounts. Technically: the asynchronous audit model that records user logins, password resets, PIN updates, and device-token changes. All audit events are written via non-blocking repository patterns so audit writes never increase API latency.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** The auth and account services through the non-blocking audit repository. **Read by.** Audit-log viewers gated by the RBAC matrix (`View Audit Logs`).

### AuditAdminAction

**Purpose.** Plain: the staff diary — every action an operator takes, on the record. Technically: the audit model recording every staff action — user suspensions, manual KYC approvals, fee overrides — with operator ID, IP address, and payload diffs.

**Key columns.** Operator ID, IP address, and payload diffs are documented as recorded content; column names and types are **UNVERIFIED**.

**Written by.** Admin-facing services (`AdminService`, `AdminKycService`) through the non-blocking audit repository. **Read by.** `COMPLIANCE_OFFICER` and `SUPER_ADMIN` roles per the RBAC matrix.

### AuditSystemEvent

**Purpose.** Plain: the machine diary — what the platform itself did. Technically: the audit model tracking system lifecycle events, provider failovers, and outbox dead-letter routing.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** Infrastructure services (provider factory failovers, outbox/DLQ routing). **Read by.** Operations and audit consumers; specific readers are **UNVERIFIED** in the old docs.

## Sessions and Security

### river_brand_sys_user_session_control

**Purpose.** Plain: the master switch for your login sessions — change your password and every open session on every device is cut off at once. Technically: the platform sidecar table (note the `river_brand_sys_` prefix — platform, not domain) that tracks an atomic per-user token version, `jwt_version`, without altering the legacy `user_user` table. `SessionControlRepository` reads the version (15-second Redis cache under `session:jv:{userId}`) and increments it atomically on sign-out or password reset, so every issued token worldwide is invalidated instantly with a `401`. The mechanism is specified in [§9.2](../chapters/ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch).

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| userId | `bigint` or `number` (repository signatures) | The owning user; the upsert key of the sidecar row. |
| jwtVersion | `number` (integer counter) | The session version embedded in each issued JWT as the `jv` claim. Defaults to 1 when no row exists; a fresh row is created at version 2. |
| updatedAt | `Date` (repository update payload) | Touched on every increment. |

**Written by.** `SessionControlRepository.incrementVersion`, called from `AuthService.signOut` and password-reset flows; `AuthService.signUp` provisions the row. **Read by.** `SessionControlRepository.getVersion` during `AuthService.signIn` and on every authenticated request at the auth middleware.

### user_transaction_pin

**Purpose.** Plain: the secret four-digit PIN that authorizes your money movements. Technically: the transaction-PIN store documented in the credential table: bcrypt-hashed at cost factor 12, with three failed attempts triggering a 30-minute Redis lockout. This is a legacy-style un-prefixed name.

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| pin | **UNVERIFIED** | The bcrypt hash of the 4-digit PIN (storage model `user_transaction_pin.pin`). |

**Written by.** `PinService` at PIN set or change (including the chat PIN-capture step of `WhatsAppRegistrationHandler`). **Read by.** `PinService` on authorization; `WhatsAppTransferHandler` and bill/airtime handlers gate execution on PIN verification.

### sys_roles

**Purpose.** Plain: the staff job titles — who is allowed to do what. Technically: the RBAC role table managed by `RoleService`, holding the administrative roles `SUPER_ADMIN`, `COMPLIANCE_OFFICER`, `SUPPORT_AGENT`, and `FINANCIAL_AUDITOR`. Roles and permissions are validated and seeded asynchronously on boot via `seedDefaultPermissions()`.

**Key columns.** Role identity and name are implied by the documented role values; column names and types are **UNVERIFIED**.

**Written by.** `RoleService`; startup seeding. **Read by.** `RoleService`, the auth middleware, and every admin capability check.

### sys_permissions

**Purpose.** Plain: the individual rights that get combined into job titles. Technically: the fine-grained permission table managed by `PermissionService`, with documented permission values such as `MANAGE_USERS`, `MANAGE_TRANSFERS`, `VIEW_REPORTS`, `OVERRIDE_KYC`, and `MANAGE_SYSTEM_CONFIG`.

**Key columns.** Permission identity and name are implied by the documented values; column names and types are **UNVERIFIED**.

**Written by.** `PermissionService`; startup seeding. **Read by.** `PermissionService` and the permission checks behind the RBAC matrix.

### sys_role_permissions

**Purpose.** Plain: the wiring diagram between titles and rights. Technically: the strict many-to-many junction mapping permissions to administrative roles.

**Key columns.** The old documentation names no columns — **UNVERIFIED** beyond the two foreign-key roles.

**Written by.** `RoleService` / `PermissionService` at seeding and maintenance — **UNVERIFIED** as to the exact write path. **Read by.** The RBAC resolution path in `PermissionService`.

### sys_user_roles

**Purpose.** Plain: which staff member holds which title. Technically: the user-to-role assignment table named in the RBAC database set of `RoleService` and `PermissionService`.

**Key columns.** The old documentation names no columns — **UNVERIFIED** beyond the two foreign-key roles.

**Written by.** Staff administration flows — **UNVERIFIED**. **Read by.** The RBAC resolution path.

### rbp_brand_security_question

**Purpose.** Plain: the master list of recovery questions ("what was your first school?"). Technically: the active security-question library that `SecurityQuestionService.getPublicQuestions` fetches and that `AdminSecurityQuestionService` maintains (create, update, delete, add multiple-choice options). A current-domain `rbp_brand_*` table.

**Key columns.** Question text and options are documented as content managed through the admin service; column names and types are **UNVERIFIED**.

**Written by.** `AdminSecurityQuestionService`. **Read by.** `SecurityQuestionService.getPublicQuestions`; recovery workflows.

### rbp_brand_user_security_question_answer

**Purpose.** Plain: your answers to those questions, locked away hashed. Technically: the per-user answer store; `SecurityQuestionService.setUserAnswers` hashes each answer with bcrypt, and `verifyUserAnswer` compares a candidate answer against the stored hash during account recovery.

**Key columns.** The old documentation names the hash-and-compare behaviour but no columns — **UNVERIFIED**.

**Written by.** `SecurityQuestionService.setUserAnswers`. **Read by.** `SecurityQuestionService.verifyUserAnswer` in recovery workflows.

## Savings and Wealth

### Target

**Purpose.** Plain: the savings envelope — a Safelock deposit or a savings goal with its own pot of money. Technically: the savings instrument model where funds are locked with `savingsType = SAFELOCK` after a wallet debit; `currentAmount` is updated by the nightly accrual job, and maturity pays principal plus interest back to the wallet. An un-prefixed model name.

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| savingsType | **UNVERIFIED** | Discriminator; the documented value `SAFELOCK` marks an upfront-capital locked deposit. |
| currentAmount | **UNVERIFIED** | Running principal-plus-accrued-yield balance, updated by the daily accrual. |

**Written by.** `SavingsService.createSafelock` and `processDailyInterestAccrual`. **Read by.** `SavingsService.liquidateMaturedSafelock` at maturity; `SavingsJob`.

### savings_config

**Purpose.** Plain: the settings that govern savings products — tenures, rates, and rules. Technically: a configuration model named among `SavingsService`'s primary models alongside `Target`. The legacy `savings_` prefix marks it to-be-renamed (see [§3.5](../chapters/ch03-domain-primer.md#35-the-schema-prefix-map)).

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** **UNVERIFIED** (the old docs do not name an admin path for savings configuration). **Read by.** `SavingsService` in product and accrual calculations.

### savings_usersavinginterestlog

**Purpose.** Plain: the daily line in your savings passbook showing what your deposit earned. Technically: the interest-accrual log appended by `SavingsJob` (`src/job/savings.ts`), which runs nightly at 00:00 UTC, iterates active locked deposits, calculates the daily compounding yield, updates `currentAmount` on the `Target` record, and records an entry here. Legacy `savings_` prefix — to-be-renamed.

**Key columns.** The old documentation names no columns — **UNVERIFIED** beyond the logged interest amount and its link to the deposit.

**Written by.** `SavingsJob` via `SavingsService.processDailyInterestAccrual`. **Read by.** Savings statements and `SavingsService.liquidateMaturedSafelock` at payout.

## Platform and Async Delivery

### rbp_brand_outbox

**Purpose.** Plain: the guaranteed-courier's mailbag — every message the system owes, written down in the same breath as the money movement itself. Technically: the transactional outbox table of the outbox pattern; financial operations insert events (documented example: `eventType: 'TRANSFER_COMPLETED'` with a JSON `payload`) inside the same single-commit transaction as the balance change, and a background relay delivers them afterwards. `OutboxJob` processes the queue via PostgreSQL `LISTEN/NOTIFY` with a safety cron (`*/5 * * * * *`) and batch sweeps using `FOR UPDATE SKIP LOCKED`. `ArchivalJob` prunes processed events older than 3 days. See [§5.4](../chapters/ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue).

**Key columns.**

| Column | Type as documented | Meaning |
| --- | --- | --- |
| eventType | **UNVERIFIED** | Event name; the documented example is `TRANSFER_COMPLETED`. |
| payload | JSON string (written via `JSON.stringify` in the documented transaction snippet) | Event body handed to the downstream dispatcher. |

**Written by.** `FinancialEngine` and every service that commits a business operation needing a side effect (receipts, alerts, WhatsApp confirmations). **Read by.** `OutboxJob`; `ArchivalJob` for pruning.

### rbp_brand_deadletter

**Purpose.** Plain: the dead-letter holding office — envelopes the courier could not deliver after every retry, kept visible instead of silently dropped. Technically: the dead-letter table of the outbox pipeline; after failed dispatch attempts (the old docs document five attempts with exponential backoff) a record is moved here for operator alerting and automated replay. `DlqJob` sweeps records exceeding max retries on a `*/15 * * * *` cron.

**Key columns.** The old documentation names no columns — **UNVERIFIED** beyond the retried event content.

**Written by.** `OutboxJob` when a downstream provider exhausts retries. **Read by.** `DlqJob` (alerting and replay); `AuditSystemEvent` records DLQ routing.

### DeviceToken and sys_device_tokens

**Purpose.** Plain: the addresses your phone gives us so push notifications reach the right device. Technically: the device-token store for Firebase Cloud Messaging across iOS, Android, and Web. The old docs name the Prisma model `DeviceToken` (written by `POST /user/device-token`) and the table `sys_device_tokens` that `PushNotificationService` self-heals — invalidating tokens on app uninstalls — and that `DeviceTokenService` populates at multi-device registration. Two spellings, one responsibility; both are recorded here rather than silently reconciled.

**Key columns.** The old documentation names no columns — **UNVERIFIED**.

**Written by.** `DeviceTokenService` via the device-token endpoint. **Read by.** `PushNotificationService` (FCM dispatch and invalidation).

## Keeping This Dictionary Honest

Three habits keep this appendix trustworthy. First, every column type is quoted only where the old documentation states it — service signatures and repository excerpts count as statements; everything else is **UNVERIFIED**. Second, two known naming duality (`riverbrand_sms_otp` versus `riverbrandsmsotp`, and `DeviceToken` versus `sys_device_tokens`) are recorded rather than resolved, because this book may not invent a reconciliation the codebase has not made. Third, when the live schema is finally inspected, corrections land as errata in [Appendix G](app-g-changelog.md) and the corresponding **UNVERIFIED** markers are retired — never edited away silently. For the API surface these tables serve, see [Appendix D: API and Endpoint Reference](app-d-api-reference.md); for the vocabulary of terms used here, see [Appendix A: Glossary](app-a-glossary.md).
