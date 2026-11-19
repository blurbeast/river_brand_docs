# Appendix I: Engineer 30-Day Onboarding Checklist

This is the companion to [Chapter 16](../chapters/ch16-engineer-onboarding.md), written as checkboxes because onboarding is a project, not a reading list. Print it or copy it into your team's tracker, tick items as you finish them, and review it with your onboarding buddy at the end of week 2 and with your manager at day 30. Every item links to the chapter or section that teaches it — when an item feels vague, the link is the answer. The pace assumes you are also doing normal team work; the checklist is the floor, not the ceiling.

## Days 1-2: Environment and Vocabulary

The goal of the first two days is one thing: a working stack and the words the team uses. Nothing you build this month is trustworthy until the engine runs on your own machine.

- [ ] Install the five required tools — Node.js v20.x LTS+, npm v10+, Docker Engine v24+ with Compose v2.20+, Prisma CLI v5.x with psql v15, and Git v2.40+ ([§16.1](../chapters/ch16-engineer-onboarding.md#161-day-one-environment)).
- [ ] Clone RiverbrandBE, run `npm install`, and create your local `.env` from the environment catalog — not from a teammate's file ([§11.1](../chapters/ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose)).
- [ ] Bring the stack up with `npm run docker:up` and confirm all four containers are healthy in `docker compose ps` ([§11.1](../chapters/ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose)).
- [ ] Push the Prisma schema (`npm run prisma:push`) and generate the typed client (`npx prisma generate`) ([§11.1](../chapters/ch11-engineering-operations-manual.md#111-prerequisites-environment-and-docker-compose)).
- [ ] Get both health checks green — `/health/liveness` and `/health/readiness` on port 8010 — and know which dependencies readiness actually pings ([§11.2](../chapters/ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation)).
- [ ] Open Swagger at `/documentation` and Scalar at `/reference`, and run one harmless request against the live API ([§11.2](../chapters/ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation)).
- [ ] Read the domain primer through §3.4: double-entry, NUBAN/NIP/NIBSS/BVN/NIN, wallets and the five currencies, KYC tiers ([§3.1–§3.4](../chapters/ch03-domain-primer.md#31-double-entry-in-plain-words)).
- [ ] Learn the four ports you will use daily — 8010 API, 8026 Mailpit, 6432 PgBouncer, 9095 Prometheus — and check Mailpit captures one outgoing dev email ([§11.2](../chapters/ch11-engineering-operations-manual.md#112-ports-health-and-api-documentation)).

## Week 1 (Days 3-5): The Engine Under Your Feet

Week one is about the money path. By Friday you should be able to narrate one transfer through the system without notes — that narration is the acceptance test for this week.

- [ ] Read the transaction-engine chapters on the concurrency guard, the double-entry ledger, idempotency references, and the outbox ([§5.1–§5.4](../chapters/ch05-engineering-transaction-engine.md#51-the-two-tier-concurrency-guard)).
- [ ] Trace one transfer end to end with your own example amount — in a debugger, with log lines, or on paper — naming the lock key, the tables written inside the commit, and the outbox row ([§16.3](../chapters/ch16-engineer-onboarding.md#163-trace-one-transfer-end-to-end)).
- [ ] Read the failure-mode matrix once while nothing is on fire, and mark the two failures you would least want to debug at 2 a.m. ([§5.7](../chapters/ch05-engineering-transaction-engine.md#57-failure-mode-matrix)).
- [ ] Read the service catalog entry for the service you expect to touch first — its purpose, methods, and tables ([Chapter 13](../chapters/ch13-engineering-service-catalog.md), using the reading guide in [§13.1](../chapters/ch13-engineering-service-catalog.md#131-how-to-read-a-service-entry)).
- [ ] Look up that service's tables in the data dictionary and confirm which schema prefix each name belongs to ([Appendix C](app-c-data-dictionary.md), [§3.5](../chapters/ch03-domain-primer.md#35-the-schema-prefix-map)).
- [ ] Walk the service-map routing table and find the entry for the kind of change your team is discussing this sprint ([§16.5](../chapters/ch16-engineer-onboarding.md#165-the-service-map-and-where-to-change-what)).
- [ ] Ship one small change through the normal review path — a documentation fix, a missing test, or a clearer log message in code you now understand ([§16.6](../chapters/ch16-engineer-onboarding.md#166-first-week-checklist)).
- [ ] Whiteboard the transfer trace for a teammate, without notes, and collect their questions as your reading list for week two ([§16.3](../chapters/ch16-engineer-onboarding.md#163-trace-one-transfer-end-to-end)).

## Week 2: Channels, Security, and the Jobs Fleet

Now widen from the engine to the doors customers arrive through and the work that runs while they sleep. Week two is where "it works on my machine" becomes "I know what happens when a dependency does not".

- [ ] Trace one WhatsApp session end to end: webhook on port 8010, signature verification, provider factory, session state machine, domain handler, ledger, and reply ([§16.4](../chapters/ch16-engineer-onboarding.md#164-trace-one-whatsapp-session)).
- [ ] Run the simulated WhatsApp test suite (`npx ts-node scratch/test_whatsapp_banking.ts`) and watch a full conversational transfer with PIN authorization ([§11.5](../chapters/ch11-engineering-operations-manual.md#115-whatsapp-webhook-debugging)).
- [ ] Break one thing on purpose in dev — a wrong webhook secret, a stale lock key — and recover it using the troubleshooting playbook ([§11.6](../chapters/ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook)).
- [ ] Read the provider-factory and state-machine sections, and explain out loud why switching WhatsApp vendors is a configuration change ([§7.2–§7.3](../chapters/ch07-engineering-channel-fabric.md#72-the-whatsapp-provider-factory)).
- [ ] Read the security architecture on dual-token isolation, the sidecar `jwt_version` kill-switch, PIN and password protection, and RBAC ([§9.1–§9.4](../chapters/ch09-engineering-security-architecture.md#91-dual-token-client-isolation)).
- [ ] Trigger a session revocation in dev — sign out or reset a password — and watch the old token fail its next request ([§9.2](../chapters/ch09-engineering-security-architecture.md#92-sidecar-session-control-and-the-kill-switch)).
- [ ] Learn the background jobs fleet: what `OutboxJob`, `DlqJob`, `SavingsJob`, `ReconciliationJob`, `BillReconciliationJob`, `ArchivalJob`, and `GeneralLedgerJob` each own and when they run ([§11.3](../chapters/ch11-engineering-operations-manual.md#113-the-background-jobs-fleet)).
- [ ] Read how reliability is framed for customers — the jobs that run while you sleep and what reliability honestly means — so you can translate incidents into business language ([§10.2–§10.3](../chapters/ch10-for-everyone-reliability.md#102-jobs-that-run-while-you-sleep)).
- [ ] Open the metrics endpoint (`http://localhost:9095/metrics`) and find one latency histogram and one outbox gauge ([§11.4](../chapters/ch11-engineering-operations-manual.md#114-observability-and-metrics)).

## Weeks 3-4: Ownership, On-Call, and Teaching

The last two weeks are about belonging to the system rather than touring it. The exit criteria are simple: you carry a change, you carry a pager shadow, and you carry a room's attention for ten minutes.

- [ ] Own one small feature or bug fix from ticket to production (or to the team's staging environment), including tests and review ([§16.5](../chapters/ch16-engineer-onboarding.md#165-the-service-map-and-where-to-change-what)).
- [ ] Sit an on-call shadow shift with the current rota holder: watch how alerts arrive, how the runbooks are used, and how incidents are communicated ([§11.6](../chapters/ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook), [§11.4](../chapters/ch11-engineering-operations-manual.md#114-observability-and-metrics)).
- [ ] Write down the three questions you would ask at 3 a.m. and find where each is answered — a runbook, a metric, or a table query ([§11.6](../chapters/ch11-engineering-operations-manual.md#116-runbooks-and-troubleshooting-playbook)).
- [ ] Present the money-movement flow to the team: one transfer, all four guards, the ledger write, and the outbox — ten minutes at a whiteboard, questions included ([§16.3](../chapters/ch16-engineer-onboarding.md#163-trace-one-transfer-end-to-end)).
- [ ] Read the upgrade roadmap far enough to know which parts of the system are frozen by design and which are expected to change ([Chapter 15](../chapters/ch15-engineering-roadmap.md)).
- [ ] Improve one piece of onboarding itself: fix an error in this book, add a missing test around a trap you hit, or extend a runbook with what you learned ([Appendix H](app-h-contribution.md)).
- [ ] Review this checklist with your manager, tick the definition below together, and agree what "on your own" means for month two.

## Definition of Onboarded

You are onboarded when all of the following are true — not "read about", but demonstrably true:

- **Environment:** you can bring the full stack from clean clone to green health checks in under an hour ([§16.1](../chapters/ch16-engineer-onboarding.md#161-day-one-environment)).
- **Vocabulary:** you can explain double-entry, NUBAN, KYC tiers, and the schema prefixes to a new hire without opening a doc ([§3.1–§3.5](../chapters/ch03-domain-primer.md#31-double-entry-in-plain-words)).
- **The money path:** you can trace one transfer end to end and name what each of the four guards prevents ([§16.3](../chapters/ch16-engineer-onboarding.md#163-trace-one-transfer-end-to-end)).
- **The channel path:** you can trace one WhatsApp session and say why the chat layer never moves money itself ([§16.4](../chapters/ch16-engineer-onboarding.md#164-trace-one-whatsapp-session)).
- **Routing:** given a change request, you can name the service file and the chapter section to read before you touch code ([§16.5](../chapters/ch16-engineer-onboarding.md#165-the-service-map-and-where-to-change-what)).
- **Shipped:** at least one change of yours is merged through normal review ([§16.6](../chapters/ch16-engineer-onboarding.md#166-first-week-checklist)).
- **Operational empathy:** you have shadowed on-call and know where the runbooks and metrics live ([§11.4–§11.6](../chapters/ch11-engineering-operations-manual.md#114-observability-and-metrics)).
- **Teaching:** you have presented the money-movement flow to the team and survived the questions ([§16.3](../chapters/ch16-engineer-onboarding.md#163-trace-one-transfer-end-to-end)).

When those eight are ticked, hand this page back, buy your buddy a coffee, and go break something small and interesting on purpose.
