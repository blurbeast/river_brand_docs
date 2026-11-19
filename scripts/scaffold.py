#!/usr/bin/env python3
"""Generate chapter/appendix shells for the Riverbrand Knowledge Book (idempotent: skips non-shells)."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

CHAPTERS = [
    (1, "riverbrand-story", "The Riverbrand Story: Vision, Market, and Product Map", "shared", [
        "Why This Book", "The Problem with Core Banking Today", "What Riverbrand Is: The Product Map",
        "The Dual-Track Promise", "Success Metrics, Honestly Stated"]),
    (2, "learn-unlearn-relearn", "Learn, Unlearn, Relearn: A Method for Banking Systems", "shared", [
        "The Pedagogy", "What Bankers and Builders Must Unlearn", "What Engineers Relearn", "The Recap-Block Convention"]),
    (3, "domain-primer", "Domain Primer: Ledgers, NUBANs, KYC, and Rails", "shared", [
        "Double-Entry in Plain Words", "NUBAN, NIP, NIBSS, BVN, and NIN", "Wallets and the Five Currencies",
        "KYC Tiers and Limits", "The Schema-Prefix Map"]),
    (4, "for-everyone-how-money-moves", "For Everyone: How Money Moves", "nontech", [
        "Amina's Salary Lands: A Persona Story", "The Bank-Vault Airlock", "Nothing Gets Counted Twice",
        "The Quarantined Balance", "The Guaranteed Courier", "What We Built, Why, and Where It Goes"]),
    (5, "engineering-transaction-engine", "Engineering: The Transaction Engine", "tech", [
        "The Two-Tier Concurrency Guard", "The Immutable Double-Entry Ledger", "Idempotency References",
        "The Outbox and Dead-Letter Queue", "Virtual NUBAN Lifecycle", "The Pending-Balance Holding Tank and KYC Ceilings",
        "Failure-Mode Matrix"]),
    (6, "for-everyone-wealth-and-channels", "For Everyone: Wealth Building and 24/7 WhatsApp Banking", "nontech", [
        "Safelock, Target Savings, and AutoSave Stories", "Compounding Made Tangible", "Banking in a Chat Window",
        "When a Provider Fails", "What We Built, Why, and Where It Goes"]),
    (7, "engineering-channel-fabric", "Engineering: Savings Products and the Channel Fabric", "tech", [
        "SavingsJob and the Compounding Math", "The WhatsApp Provider Factory", "The Conversation State Machine",
        "Push Notifications and the Notification Matrix", "Multi-Currency Wallet Semantics"]),
    (8, "for-everyone-safety-and-compliance", "For Everyone: Safety, Privacy, and Compliance", "nontech", [
        "The Hotel-Keycard Story", "Two Doors for Two Devices", "What a KYC Tier Means for a Customer",
        "The Audit Trail", "Regulatory Posture and Governance", "What We Built, Why, and Where It Goes"]),
    (9, "engineering-security-architecture", "Engineering: Security Architecture", "tech", [
        "Dual-Token Client Isolation", "Sidecar Session Control and the Kill-Switch", "PIN and Password Protection",
        "Role-Based Access Control", "The Non-Blocking Audit Trail", "Threat-Model Summary"]),
    (10, "for-everyone-reliability", "For Everyone: How the Bank Stays Online", "nontech", [
        "The Airport-Tower View", "Jobs That Run While You Sleep", "What Reliability Honestly Means",
        "An Incident Story", "What We Built, Why, and Where It Goes"]),
    (11, "engineering-operations-manual", "Engineering: Developer and Operations Manual", "tech", [
        "Prerequisites, Environment, and Docker Compose", "Ports, Health, and API Documentation",
        "The Background Jobs Fleet", "Observability and Metrics", "WhatsApp Webhook Debugging",
        "Runbooks and Troubleshooting Playbook"]),
    (12, "for-everyone-product-catalog", "For Everyone: The Product Catalog", "nontech", [
        "How to Read This Menu", "Identity, Accounts, and Virtual Numbers", "Everyday Money Movement and Bills",
        "Wealth and Compounding Savings", "Global Multi-Currency Wallets", "24/7 WhatsApp Banking",
        "Enterprise Governance and Admin"]),
    (13, "engineering-service-catalog", "Engineering: The Service Catalog", "tech", [
        "How to Read a Service Entry", "Authentication and Security Services", "Core Financial and Wallet Engines",
        "Payment and Transaction Services", "Wealth and Investment Services", "KYC, Verification, and User Services",
        "Communication, WhatsApp, and Messaging Services", "Platform, Admin, and Job Services"]),
    (14, "for-everyone-future-roadmap", "For Everyone: The Future of Autonomous Global Banking", "nontech", [
        "From Chat Bank to Autonomous Bank", "New Rails: Pan-African and Cross-Border", "Open Banking and Banking-as-a-Service",
        "What Customers Will Notice", "Three Strategic Horizons"]),
    (15, "engineering-roadmap", "Engineering: The Upgrade Roadmap", "tech", [
        "The Event Backbone", "Geo-Distributed SQL", "Kubernetes and GitOps", "OpenTelemetry and Observability",
        "Multi-Agent AI and Fraud Detection", "Open Banking, Passkeys, and Post-Quantum Crypto",
        "Phased Timeline and Target Benchmarks"]),
    (16, "engineer-onboarding", "New Engineer Onboarding: From Zero to First Deploy", "tech", [
        "Day-One Environment", "The Thirty-Thousand-Foot Mental Model", "Trace One Transfer End to End",
        "Trace One WhatsApp Session", "The Service Map and Where to Change What", "First-Week Checklist"]),
]

APPENDICES = [
    ("app-a-glossary", "Appendix A: Glossary"),
    ("app-b-faq", "Appendix B: Frequently Asked Questions"),
    ("app-c-data-dictionary", "Appendix C: Data Dictionary"),
    ("app-d-api-reference", "Appendix D: API and Endpoint Reference"),
    ("app-e-competitive-matrix", "Appendix E: Consolidated Competitive Matrix"),
    ("app-f-analogy-atlas", "Appendix F: Analogy Atlas"),
    ("app-g-changelog", "Appendix G: Changelog and Errata"),
    ("app-h-contribution", "Appendix H: Contribution and Documentation Standards"),
    ("app-i-onboarding-checklist", "Appendix I: Engineer 30-Day Onboarding Checklist"),
]

TRACK_TWIN = {4: 5, 5: 4, 6: 7, 7: 6, 8: 9, 9: 8, 10: 11, 11: 10, 12: 13, 13: 12, 14: 15, 15: 14}

RECAPS = {
    "shared": ("The simple story you were told about banking systems", "the real forces: ledgers, limits, and rails", "how Riverbrand answers them"),
    "nontech": ("the idea that banking features are just screens and balance numbers", "the real journeys, rules, and risks behind each feature", "what Riverbrand actually built for people, and why it holds"),
    "tech": ("the naive implementation you would write first", "the failure modes and race conditions that break it", "the architecture Riverbrand ships instead"),
}

for num, slug, title, track, sections in CHAPTERS:
    path = ROOT / "chapters" / f"ch{num:02d}-{slug}.md"
    if path.exists() and not path.read_text().startswith("# Chapter"):
        continue
    if path.exists() and len(path.read_text().split()) > 100:
        continue  # already has real content
    u, l, r = RECAPS[track]
    lines = [f"# Chapter {num} — {title}", ""]
    lines += [f"> *Unlearn {u}. Learn {l}. Relearn {r}.*", "", "## Recap", "",
              f"- **Unlearn:** {u.capitalize()}.",
              f"- **Learn:** {l.capitalize()}.",
              f"- **Relearn:** {r.capitalize()}.", ""]
    for i, sec in enumerate(sections, 1):
        lines += [f"## {num}.{i} {sec}", "", "<!-- TODO: content -->", ""]
    lines += ["## Key Takeaways", "", "<!-- TODO: content -->", ""]
    lines += ["## Frequently Asked Questions", "", "<!-- TODO: content -->", ""]
    twin = TRACK_TWIN.get(num)
    if twin:
        twin_title = [t for n, s, t, k, se in CHAPTERS if n == twin][0]
        twin_slug = [s for n, s, t, k, se in CHAPTERS if n == twin][0]
        if track == "tech":
            lines += ["## Where to Go Next", "", f"*For everyone, see [Chapter {twin} — {twin_title}](ch{twin:02d}-{twin_slug}.md).*", ""]
        else:
            lines += ["## Where to Go Next", "", f"*For engineers, see [Chapter {twin} — {twin_title}](ch{twin:02d}-{twin_slug}.md).*", ""]
    else:
        lines += ["## Where to Go Next", "", "<!-- TODO: cross-links -->", ""]
    path.write_text("\n".join(lines))
    print("wrote", path.relative_to(ROOT))

for slug, title in APPENDICES:
    path = ROOT / "appendices" / f"{slug}.md"
    if path.exists() and len(path.read_text().split()) > 100:
        continue
    path.write_text(f"# {title}\n\n<!-- TODO: content -->\n")
    print("wrote", path.relative_to(ROOT))
