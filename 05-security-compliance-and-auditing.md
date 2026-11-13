# ⚙️ Chapter 5: Technical Security, Sidecar Revocation & Auditing

> **"Enterprise Zero-Trust Security & Instant Session Revocation"**  
> *A comprehensive technical specification on Dual-Token isolation, sidecar session invalidation, PIN security, memory guards, RBAC matrices, and non-blocking audit logging.*

---

## 🧭 5.1 The "Learn, Unlearn, Relearn" Guide to Banking Security

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

## 🛡️ 5.2 Dual-Token Client Type Isolation

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

### Production Environment Enforcement
On application startup, if `environment.appStage === "PROD"` or `"PRODUCTION"`, the server strictly mandates that both `LOCAL_ACCESS_TOKEN` and `WEB_ACCESS_TOKEN` are configured. If either is missing, the server performs a fatal shutdown (`process.exit(1)`), preventing insecure deployments.

---

## 🔑 5.3 Sidecar Session Management & Instant Token Revocation

The core session revocation logic resides in `SessionControlRepository` (`src/database/repository/sessionControl.ts`):

```typescript
@Service()
export class SessionControlRepository {
  private readonly CACHE_TTL_SECONDS = 15; // 15-second TTL for hot session version cache

  private getCacheKey(userId: bigint | number): string {
    return `session:jv:${userId}`;
  }

  async getVersion(userId: bigint | number): Promise<number> {
    const uId = BigInt(userId);
    const cacheKey = this.getCacheKey(uId);

    // 1. Fast Path: Check Hot Redis Cache
    const redis = getRedis();
    const cached = await redis.get(cacheKey);
    if (cached !== null) return parseInt(cached, 10);

    // 2. Slow Path: Read from Sidecar Table
    const record = await prisma.river_brand_sys_user_session_control.findUnique({
      where: { userId: uId },
      select: { jwtVersion: true },
    });
    const version = record?.jwtVersion ?? 1;

    // 3. Populate Redis Cache
    await redis.set(cacheKey, version.toString(), "EX", this.CACHE_TTL_SECONDS);
    return version;
  }

  async incrementVersion(userId: bigint | number): Promise<void> {
    const uId = BigInt(userId);
    // Atomic Database Increment
    await prisma.river_brand_sys_user_session_control.upsert({
      where: { userId: uId },
      update: { jwtVersion: { increment: 1 }, updatedAt: new Date() },
      create: { userId: uId, jwtVersion: 2 },
    });
    // Invalidate Redis Cache Key immediately
    await getRedis().del(this.getCacheKey(uId));
  }
}
```

---

## 🔒 5.4 PIN & Password Cryptographic Protection

| Credential Type | Hashing Algorithm | Salt & Work Factor | Storage Model | Lockout Policy |
| :--- | :--- | :--- | :--- | :--- |
| **User Password** | **Argon2id** | Memory: 64MB, Iterations: 3, Parallelism: 4 | `user_user.password` | 5 failed attempts ➔ 15m account lock |
| **Transaction PIN** | **bcrypt** | Cost Factor 12 | `user_transaction_pin.pin` | 3 failed attempts ➔ 30m Redis lock |
| **SMS / Email OTP** | **CSPRNG 6-digit** | Cryptographically secure random | `riverbrandsmsotp` | 10-minute expiry TTL |

---

## 👥 5.5 Granular Role-Based Access Control (RBAC)

Administrative security is governed by `PermissionService` and `RoleService`:
- **Granular Permissions (`Permission`)**: Fine-grained permissions (e.g., `MANAGE_USERS`, `MANAGE_TRANSFERS`, `VIEW_REPORTS`, `OVERRIDE_KYC`, `MANAGE_SYSTEM_CONFIG`).
- **Role Permissions (`RolePermission`)**: Strict many-to-many junction mapping permissions to specific administrative roles (`SUPER_ADMIN`, `COMPLIANCE_OFFICER`, `SUPPORT_AGENT`, `FINANCIAL_AUDITOR`).
- **Startup Seeding**: System permissions and roles are automatically validated and seeded asynchronously on boot via `seedDefaultPermissions()`.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              RBAC PERMISSION MATRIX                                    │
├─────────────────────┬──────────────┬──────────────────┬───────────────┬────────────────┤
│ Permission Scope    │ Super Admin  │ Compliance Lead  │ Support Agent │ Financial Audit│
├─────────────────────┼──────────────┼──────────────────┼───────────────┼────────────────┤
│ View Dashboard Stats│ ✅ Full      │ ✅ Full          │ ⚠️ Limited    │ ✅ Full        │
│ User Management     │ ✅ Full      │ ⚠️ View Only     │ ⚠️ View Only  │ ❌ None        │
│ Suspend / Unsuspend │ ✅ Full      │ ✅ KYC Reasons   │ ❌ None       │ ❌ None        │
│ Approve Tier 3 KYC  │ ✅ Full      │ ✅ Full          │ ❌ None       │ ❌ None        │
│ Transfer Overrides  │ ✅ Full      │ ❌ None          │ ❌ None       │ ❌ None        │
│ View Audit Logs     │ ✅ Full      │ ✅ Full          │ ❌ None       │ ✅ Full        │
│ Fee Structure Config│ ✅ Full      │ ❌ None          │ ❌ None       │ ⚠️ Read Only   │
└─────────────────────┴──────────────┴──────────────────┴───────────────┴────────────────┘
```

---

## 📜 5.6 Non-Blocking Enterprise Audit Trail

All audit events are recorded asynchronously via non-blocking repository patterns so that audit writes never increase API latency:
- **`AuditUserActivity`**: Records user logins, password resets, PIN updates, and device token changes.
- **`AuditAdminAction`**: Records every staff action (user suspensions, manual KYC approvals, fee overrides) with operator ID, IP address, and payload diffs.
- **`AuditSystemEvent`**: Tracks system lifecycle events, provider failovers, and outbox DLQ routing.

---

*Continue to: [Chapter 06: Technical Complete Backend Service Catalog](./08-service-catalog-and-deep-dive.md)*
