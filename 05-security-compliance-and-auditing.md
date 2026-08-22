# 📄 Chapter 5: Security, Revocation & Auditing

> **"Enterprise Zero-Trust Security & Instant Session Revocation"**  
> *Technical specification on Dual-Token isolation, sidecar session invalidation, PIN security, multi-channel OTP, RBAC, and non-blocking audit logging.*

---

## 5.1 The "Learn, Unlearn, Relearn" Guide to Banking Security

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🚫 UNLEARN: "Stateless JWT tokens are completely un-revocable until expiry."│
│ If a user loses their phone, an attacker can use the stolen token for hours │
│ or days, draining the account before the expiration timestamp arrives.      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 💡 LEARN: "Token claims can be verified against an atomic version counter." │
│ Every issued JWT embeds a session version (`jv`). On password reset, we     │
│ increment `jwt_version` in DB/Redis in 1 millisecond.                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🚀 RELEARN & MASTER: "Riverbrand's Sidecar Instant Revocation Engine"       │
│ The sidecar table `river_brand_sys_user_session_control` isolates version   │
│ state without altering legacy tables. The moment a password is changed,     │
│ every single active JWT token worldwide is invalidated instantly (`401`).   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.2 Dual-Token Client Type Isolation

To protect mobile clients from web-based cross-site vulnerabilities (and vice versa), Riverbrand enforces **Dual-Token Client Type Isolation** at the authentication middleware layer (`src/api/middleware/auth.ts`).

```
                              [Incoming HTTP Request]
                                         │
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │ Evaluates Headers in auth.ts Middleware   │
                   └───────────────────────────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   [Mobile Native Request Header]                  [Web Console Request Header]
   • `x-local-access-token: <TOKEN>`               • `x-web-access-token: <TOKEN>`
   • OR `x-access-token` + `x-client-type: mobile` • OR `x-access-token` + `x-client-type: web`
                 │                                               │
                 ▼                                               ▼
   [Validate Token against Mobile Auth Schema]     [Validate Token against Web Auth Schema]
```

### Security Benefits of Dual-Token Isolation
1. **Origin Verification**: Prevents token reuse across web and native mobile clients. A token extracted from a web browser console cannot be used to authenticate native mobile API endpoints.
2. **Contextual Expiry Controls**: Web tokens are configured with shorter expiration windows (15 minutes) suitable for browser sessions, while mobile native tokens use long-lived refresh patterns tied to device hardware identifiers.

---

## 5.3 Sidecar Session Control & Instant Token Revocation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🧠 MENTAL MODEL: The Hotel Master Keycard Switch                            │
│                                                                             │
│ Imagine checking into a hotel room. If you lose your keycard, the front     │
│ desk doesn't change the door lock — they increment the keycard version      │
│ number from 1 to 2. The lost keycard (v1) stops opening the door instantly. │
└─────────────────────────────────────────────────────────────────────────────┘
```

```prisma
model river_brand_sys_user_session_control {
  id           BigInt    @id @default(autoincrement())
  userId       BigInt    @unique @map("user_id")
  jwtVersion   Int       @default(1) @map("jwt_version") // Incremented on password change
  lastLogoutAt DateTime? @map("last_logout_at") @db.Timestamptz(6)
  updatedAt    DateTime  @updatedAt @map("updated_at") @db.Timestamptz(6)

  user         user_user @relation(fields: [userId], references: [id], onDelete: Cascade)
}
```

### Instant Revocation Execution Flow (`src/utils/jwt.ts`)

```mermaid
sequenceDiagram
    autonumber
    actor Attacker as Stolen Token / Old Session
    participant Middleware as Fastify Auth Middleware
    participant Sidecar as Session Control Repo
    actor User as User on New Device

    User->>Middleware: POST /user/change-password
    Middleware->>Sidecar: Increment `jwt_version` (1 ➔ 2)
    Sidecar-->>Middleware: Session Version Updated to 2

    Note over Attacker, Middleware: Attacker attempts request with old JWT (jwt_version = 1)
    Attacker->>Middleware: GET /wallet/balance (Header: Bearer JWT v1)
    Middleware->>Sidecar: Compare JWT claim `jv: 1` vs DB `jwtVersion: 2`
    Sidecar-->>Middleware: Mismatch Detected (1 != 2)
    Middleware-->>Attacker: 401 Unauthorized ("Token has been revoked")
```

---

## 5.4 Single Active Device Login & Session Transfer Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🧠 MENTAL MODEL: The Single Keycard Rule                                    │
│                                                                             │
│ A customer can only hold ONE active master keycard to their bank account at │
│ any time. If they log in on Device A, Device A holds the keycard.           │
│ When someone tries to log in on Device B:                                   │
│ 1. Device B is BLOCKED immediately with HTTP 408 (New Device Detected).     │
│ 2. An OTP is dispatched to the user's verified contact to confirm intent.   │
│ 3. Once Device B submits the valid OTP, Device A's keycard is deactivated   │
│    globally (HTTP 401 on next request) and Device B receives the new token. │
└─────────────────────────────────────────────────────────────────────────────┘
```

```mermaid
sequenceDiagram
    autonumber
    actor DeviceA as Device A (Currently Logged In)
    actor DeviceB as Device B (New Device)
    participant API as Fastify Auth Controller
    participant OTP as OTP Service / Outbox
    participant DB as Postgres + Session Control

    Note over DeviceA, DB: Device A is logged in with token (jv: 1, registered: deviceA)
    
    DeviceB->>API: POST /auth/signin (email, password, deviceId: "deviceB")
    API->>DB: Check registered device for user
    DB-->>API: Registered device is "deviceA" (Mismatch!)
    API->>OTP: Dispatch Device Verification OTP
    API-->>DeviceB: 408 New Device Detected (OTP Sent)

    Note over DeviceB, API: User receives 6-digit OTP on registered phone/email
    DeviceB->>API: POST /auth/verify-device (email, deviceId: "deviceB", otpCode: "123456")
    API->>OTP: Verify OTP Code
    OTP-->>API: OTP Validated ✅
    API->>DB: 1. Increment jwtVersion (1 ➔ 2) in Session Control<br/>2. Update registered device ➔ "deviceB"
    DB-->>API: Session Version Bumped & Device Updated
    API-->>DeviceB: 200 OK (New Token Issued with jv: 2)

    Note over DeviceA, API: Device A attempts any subsequent API request
    DeviceA->>API: GET /wallet/balance (Header: Bearer Token with jv: 1)
    API->>DB: Check JWT jv (1) == Current jv (2)
    DB-->>API: Mismatch Detected (1 != 2)
    API-->>DeviceA: 401 Unauthorized ("Your session has been invalidated. Please log in again.")
```

---

## 5.5 Password & Transaction PIN Security

The platform maintains two distinct authorization factors:

### 1. Account Password Hashing (`src/utils/password.ts`)
- Uses **Argon2id** (with fallback to bcrypt `saltRounds = 12`).
- Provides memory-hard hashing resistant to GPU-accelerated brute-force attacks.

### 2. Transaction PIN Hashing (`src/utils/pinSecurity.ts`)
- Requires a secret 4-digit numeric PIN for high-risk operations (transfers, bill payments, Safelock liquidations).
- Hashed independently of the account password using bcrypt with salt rounds.
- **Lockout Guard**: Blocked after 3 consecutive invalid attempts for 30 minutes in Redis (`wa:lockout:{phone}`) to mitigate brute-force guessing.

---

## 5.6 WhatsApp Webhook Security & Cryptographic Verification

```
[Inbound Webhook Request] ──► [Fastify Pre-Handler Hook]
                                       │
                                       ▼
                     ┌───────────────────────────────────┐
                     │ Evaluate Provider-Specific Secret │
                     └───────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
 [Meta Webhook Request]                                [Twilio Webhook Request]
 • Header: `x-hub-signature-256`                       • Header: `X-Twilio-Signature`
 • Algorithm: HMAC-SHA256(payload, APP_SECRET)         • Algorithm: HMAC-SHA1(url + params, AUTH_TOKEN)
            │                                                     │
            └──────────────────────────┬──────────────────────────┘
                                       │
                                       ▼
                     ┌───────────────────────────────────┐
                     │ Match Computed Hash == Header?    │
                     └───────────────────────────────────┘
                                       │
                     ├──► [MATCH]   ──► [Process Banking Logic]
                     │
                     └──► [MISMATCH] ─► [Reject HTTP 403 Forbidden]
```

### 1. Meta Webhook Verification (`MetaWhatsAppProvider.ts`)
- **Subscription Handshake**: Validates `hub.verify_token` against `WHATSAPP_VERIFY_TOKEN` and returns `hub.challenge`.
- **Payload HMAC Verification**: Computes `crypto.createHmac('sha256', APP_SECRET).update(rawBody).digest('hex')` and verifies against `x-hub-signature-256`.

### 2. Twilio Signature Verification (`TwilioWhatsAppProvider.ts`)
- Validates the `X-Twilio-Signature` header using Twilio's cryptographic HMAC-SHA1 protocol.

---

## 5.7 Multi-Channel OTP Architecture

```
[OTP Trigger Event (e.g. Password Reset)]
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│ Generate Cryptographic 6-Digit PIN                     │
│ Store Record in `riverbrand_sms_otp` (TTL: 10 Minutes) │
└────────────────────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
[Primary SMS Gateway]     [Backup SMS Gateway]
• Termii API Client        • Twilio API Client
         │                   │
         └─────────┬─────────┘
                   │
                   ▼
[Also Dispatch via Email SMTP (Mailpit / SendGrid)]
```

### SMS Provider Failover (`src/utils/sms/index.ts`)
- Primary Gateway: **Termii** (Local telecommunication routes in Nigeria).
- Backup Gateway: **Twilio** (Global fallback route).
- If Termii returns a non-200 HTTP response or times out, the system automatically falls back to Twilio.

---

## 5.8 Non-Blocking Asynchronous Audit Logging

To ensure audit logging never degrades HTTP response times, audit entries are written asynchronously (`src/utils/auditLogger.ts`):

1. **`audit_user_activity`**: Retail customer actions (`USER_LOGIN`, `PASSWORD_CHANGE`, `TRANSFER_INITIATED`, `WHATSAPP_TRANSFER`), IP address, user agent, before/after payloads.
2. **`audit_admin_action`**: Staff console operations (`USER_SUSPENDED`, `TIER_UPGRADED`), target user ID, changes, IP address.
3. **`audit_system_event`**: Core system events (`OUTBOX_FLUSH`, `RECONCILIATION_JOB`, `WHATSAPP_DISPATCH_FAILURE`).

---

## 5.9 Role-Based Access Control (RBAC) Permission Matrix

| System Role (`sys_roles`) | Module Permissions (`sys_permissions`) | Scope of Action |
| :--- | :--- | :--- |
| **`Super Admin`** | `*` (All Permissions) | Full administrative access, role assignment, system configuration. |
| **`Compliance Officer`** | `kyc:read`, `kyc:verify`, `kyc:reject`, `audit:view` | Inspect user KYC documents, approve/reject tier upgrades, view audit trails. |
| **`Finance Manager`** | `financial:view_stats`, `pending_balance:release`, `reconciliation:read` | View bank liabilities, manage provider reserve totals, inspect pending balances. |
| **`Customer Support`** | `user:read`, `user:unsuspend`, `notification:send` | View user profiles, reset security questions, dispatch support push alerts. |

---

*Next Chapter: [06. Future Strategic Upgrade Roadmap](./06-future-upgrade-roadmap.md) — How It Can Be Upgraded (Strategic Architectural & Enterprise Evolution Plan).*
