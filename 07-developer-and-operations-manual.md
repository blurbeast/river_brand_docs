# 📄 Chapter 7: Developer & Operations Manual

> **"Engineering & Operations Playbook"**  
> *A step-by-step technical setup, container orchestration, environment variable catalog, and operational troubleshooting guide.*

---

## 7.1 Local Environment Setup & Prerequisites

### Required Infrastructure & Tools

- **Node.js**: `v20.x LTS` or higher
- **Package Manager**: `npm` (v10+)
- **Containerization**: `Docker Engine` (v24+) & `Docker Compose` (v2.20+)
- **Database Tools**: `Prisma CLI` (v5.x) & `psql` (PostgreSQL Client v15)
- **Version Control**: `Git` (v2.40+)

---

## 7.2 Repository Setup & Installation

### Step 1: Clone Application Repository

```bash
git clone git@github.com:RiverBank-Partners/RiverbrandBE.git
cd RiverbrandBE
npm install
```

### Step 2: Configure Master Environment File (`.env`)

Create a `.env` file in the root of `RiverbrandBE`:

```env
# Server Port & Environment Mode
PORT=8010
NODE_ENV=development
APP_STAGE=DEV

# Database Connections
DATABASE_URL="postgresql://riverbrand:riverbrand_secret_2026@postgres:5432/riverbank_prod_db?schema=public"
REDIS_URL="redis://redis:6379"

# Dual-Token Authorization Secrets
LOCAL_ACCESS_TOKEN="local-dev-secret-token"
WEB_ACCESS_TOKEN="web-dev-secret-token"
JWT_SECRET="riverbrand-jwt-secret-key-2026"

# Email SMTP Delivery (Mailpit Dev Server)
SMTP_HOST=mailpit
SMTP_PORT=1025
MP_SMTP_AUTH_ALLOW_INSECURE=1

# Firebase Admin Push Credentials
FIREBASE_PROJECT_ID="riverbrand-d806f"
FIREBASE_CLIENT_EMAIL="firebase-adminsdk-fbsvc@riverbrand-d806f.iam.gserviceaccount.com"
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# Third-Party Gateway API Credentials
DOJAH_API_KEY="prod_dojah_api_key_here"
DOJAH_APP_ID="prod_dojah_app_id_here"
PROVIDUS_CLIENT_ID="providus_client_id_here"
FINCRA_SECRET_KEY="fincra_secret_key_here"
FLUTTERWAVE_SECRET_KEY="FLWSECK_TEST-xxx-X"
TERMII_API_KEY="termii_api_key_here"
```

---

## 7.3 Docker Orchestration & Production Stack Execution

Riverbrand includes Docker Compose configurations for both local development and production containerized stacks.

### Launch Local Stack with Docker Compose

```bash
# Start Docker Container Stack (Postgres, Redis, Mailpit, Fastify API)
npm run docker:up

# Alternatively, run Production Docker Compose Stack
docker compose -f docker-compose.prod.yml up --build -d
```

### Verify Container Status

```bash
docker compose ps
```

Expected Output:
```
NAME                    IMAGE                       STATUS         PORTS
riverbank_postgres_1    postgres:15-alpine          Up (healthy)   0.0.0.0:5432->5432/tcp
riverbank_redis_1       redis:7-alpine              Up (healthy)   0.0.0.0:6379->6379/tcp
riverbank_mailpit_1     axllent/mailpit             Up             0.0.0.0:1025->1025/tcp, 0.0.0.0:8026->8025/tcp
riverbank_api_1         riverbrand-backend:latest   Up             0.0.0.0:8010->8010/tcp
```

---

## 7.4 Database Migrations & Prisma Management

### Apply Database Schema Push & Generate Client

```bash
# Push Prisma Schema to PostgreSQL Database
npm run prisma:push

# Generate Type-Safe Prisma Client Artifacts
npx prisma generate
```

### Pull Live Database Schema Updates (Reverse Engineering)

```bash
npm run prisma:pull
```

---

## 7.5 Interactive API Documentation & Local Web UI Services

When the Docker stack is running, access the local developer services:

| Web Interface / Endpoint | Local URL | Description |
| :--- | :--- | :--- |
| 📖 **Swagger UI Documentation** | [http://localhost:8010/documentation](http://localhost:8010/documentation) | Interactive OpenAPI 3.0 route testing interface. |
| ⚡ **Scalar Modern API Reference** | [http://localhost:8010/reference](http://localhost:8010/reference) | Modern interactive API reference interface. |
| 📄 **Raw OpenAPI 3.0 JSON Spec** | [http://localhost:8010/documentation/json](http://localhost:8010/documentation/json) | Complete OpenAPI JSON specification. |
| ✉️ **Mailpit Email Inbox** | [http://localhost:8026](http://localhost:8026) | Visual web dashboard capturing all outgoing dev emails. |
| 📊 **Prometheus Metrics Endpoint** | [http://localhost:9095/metrics](http://localhost:9095/metrics) | Live metric telemetry for Prometheus scraping. |

---

## 7.6 Testing & Health Verification Commands

### Execute TypeScript Build Verification

```bash
npx tsc --noEmit
```

### Test Application Liveness & Readiness Endpoints

```bash
# Liveness Check
curl -i http://localhost:8010/health/liveness

# Readiness Check (Pings Postgres, Redis, Mailpit)
curl -i http://localhost:8010/health/readiness
```

---

## 7.7 Operational Troubleshooting Playbook

### Problem A: Database Connection Refused (`P1001`)
- **Symptom**: `PrismaClientInitializationError: Can't reach database server at postgres:5432`.
- **Solution**: Ensure PostgreSQL container is running:
  ```bash
  docker compose restart postgres
  ```

### Problem B: Redis Distributed Lock Timeout (`RedlockError`)
- **Symptom**: `HTTP 409 Conflict: A transaction is already in progress on this account`.
- **Solution**: Check if a previous transaction stalled or stuck in a deadlock. Inspect Redis active lock keys:
  ```bash
  docker exec -it riverbank_redis_1 redis-cli KEYS "lock:wallet:*"
  ```
  To flush a dead lock key manually during dev:
  ```bash
  docker exec -it riverbank_redis_1 redis-cli DEL "lock:wallet:123"
  ```

### Problem C: Invalid Token Claims (`401 Unauthorized`)
- **Symptom**: `Token has been revoked or has invalid version`.
- **Solution**: The user's `jwt_version` in `river_brand_sys_user_session_control` was incremented due to a password reset. Re-authenticate via `POST /auth/login` to obtain a fresh JWT containing the updated `jv` claim.

---

## 7.8 Summary

This manual provides developers and SREs with complete operational control to install, migrate, run, document, observe, and troubleshoot the Riverbrand Enterprise Digital Banking Platform.

*End of Documentation Suite.*
