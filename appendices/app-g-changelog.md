# Appendix G: Changelog and Errata

This appendix records the editions of the Riverbrand Knowledge Book, the corrections applied to it, and the register of facts still awaiting confirmation against the live codebase. A book about a banking engine that cannot say what changed — or what it got wrong — is not a knowledge record; it is a brochure. Everything here follows the book's honest-tone standard: editions are described as they were, errata are published rather than quietly patched, and uncertainty is registered, not hidden.

## Versioning Policy for This Book

The book uses semantic versioning for its own text. The **major** number changes on restructure — a new architecture of chapters, tracks, or appendices. The **minor** number changes when substantive content is added (new sections, new appendices, new figures) without rearranging the whole. The **patch** number changes for errata: corrections of fact, broken links, naming fixes, and retired **UNVERIFIED** markers. Every published change lands in the edition log below with its version, date, author, and a plain description of what moved.

## Edition 1.0.0 — Original Documentation Suite (2026)

The first edition was not a book; it was the engineering documentation suite that grew alongside the Riverbrand Banking Engine during its build. Its shape: a flat set of fourteen markdown files in one directory — eight technical documents numbered 01 through 08 (executive overview; architecture and design; core banking and the financial engine; savings, investments, and channels; security, compliance, and auditing; the future upgrade roadmap; the developer and operations manual; and the service catalog deep-dive) paired with six non-technical companion documents covering core banking, savings and channels, security and governance, the future roadmap, operations and reliability, and the product catalog.

What that edition did well: it was written close to the code by the engineers who built the system, so its technical facts — table names, job schedules, port numbers, gateway fallbacks, the sidecar revocation design — were concrete and checkable. What it did not do well: it was dense where it should have been clear, thin where it should have been rich, and it made sweeping security claims where it should have shown evidence. The same explanation was often repeated across three or four files with small inconsistencies (a table name spelled two ways, an analogy retold with different details). There was no shared standard for tone, no glossary, no figure program, and no way to tell a confirmed fact from an aspiration.

The old suite remains in the repository root as the source of record for the Second Edition. It is read-only input to this book; the Second Edition supersedes it for readers.

## Edition 2.0.0 — The Second Edition (This Restructure)

The Second Edition is a full restructure of the original suite into a textbook: continuous chapter numbering 1–16, front matter (title page, authors, copyright, preface, how to read, table of contents, list of figures), and nine consolidated appendices. Its distinguishing commitments:

- **Paired tracks.** Every mechanism chapter has a non-technical twin covering the same ground in plain language, and each pair cross-links to the other. Chapters 1–3 and 16 are shared foundations and engineering onboarding.
- **Consolidated appendices.** Reference material that the old suite scattered is gathered once: the glossary (Appendix A), the data dictionary (Appendix C), the API and endpoint reference (Appendix D), and — a deliberate consolidation — the five canonical explanatory analogies, which the old docs retold in several places with drifting details, now live only in [Appendix F](app-f-analogy-atlas.md) and are cited elsewhere rather than retold.
- **A figure program.** Mechanisms are shown, not just described: Mermaid diagrams render live in the web book under bold `**Figure N.M — Title.**` captions, and custom SVGs are slotted in through named markers (`fig-chNN-slug.svg`) in a later production phase.
- **The honest-tone standard.** A written and machine-enforced content standard (`scripts/CONTENT-STANDARD.md`): banned hype phrasings, jargon quarantined out of the non-technical track, evidence-over-hypothesis wording ("designed to", not "guaranteed to"), and the **UNVERIFIED** marker for any fact not grounded in the old documentation. The structure checker (`scripts/check-structure.sh`) enforces most of it on every change.
- **Process support.** A contribution standard ([Appendix H](app-h-contribution.md)), a generated table of contents and sidebar, an onboarding checklist for new engineers, and this changelog.

**Authors and co-authors.** The book is a collective record of the people who designed, built, and run the platform: **Osas** (Chief Technology Officer — author; technical vision and system architecture); **Samuel (wezard)** (co-author; platform engineering and documentation architecture); **Olalekan (AlicSystems)** (co-author; systems integration and channel engineering); and **Abednego (Geekycoder)** (co-author; product engineering and reliability). Author roles are recorded in full in the front matter.

**Edition log.**

| Version | Date | Change | Author |
| --- | --- | --- | --- |
| 2.0.0 | Second Edition publication | Full restructure: 16-chapter paired-track textbook, front matter, nine appendices (glossary, FAQ, data dictionary, API reference, competitive matrix, analogy atlas, changelog, contribution standards, onboarding checklist), figure program, honest-tone standard, generated TOC and sidebar. | Osas; Samuel (wezard); Olalekan (AlicSystems); Abednego (Geekycoder) |

## Errata

**Status: no open errata.** This section is the book's public correction ledger. When a reader or an audit finds a factual error — a wrong table name, a wrong port, a wrong status code, a broken cross-link — it is recorded here when the fix is merged, not deleted from history.

An errata entry uses this template:

| Field | Content |
| --- | --- |
| ID | `E-YYYYMMDD-NN` |
| Date reported | Date the report was filed |
| Location | File and section (e.g. `app-c-data-dictionary.md — riverbrand_sms_otp`) |
| Wrong text | What the book said before the fix |
| Corrected text | What the book says after the fix |
| Evidence | Source of the correction (codebase line, run output, provider dashboard) |
| Reporter | Who found it |
| Status | Open → Fixed in version X.Y.Z |

**How to report.** Open a pull request against this repository with the correction and an entry added to this table (see [Appendix H](app-h-contribution.md) for the contribution workflow and checklist). If you cannot open a PR, raise the issue with any maintainer named in the author list; the maintainer files the entry on your behalf with you credited as reporter. Small fixes (typos that do not change meaning) may be corrected without an errata row; anything that changes a fact, a number, a name, or a claim gets a row.

## UNVERIFIED Register

The **UNVERIFIED** marker is this book's admission policy: any fact not grounded in the old documentation suite carries the marker inline, and this register is where those markers are counted and retired. The Second Edition was written from the 2026 suite alone — this repository contains no application source code — so whole categories of fact are honestly unknown: exact column types in the data dictionary ([Appendix C](app-c-data-dictionary.md)), the full HTTP surface in the API reference ([Appendix D](app-d-api-reference.md)), and any behaviour added to RiverbrandBE after the suite was written.

Current register contents:

| Area | What is pending | Retired when |
| --- | --- | --- |
| Appendix C, column types and unnamed columns | Every `**UNVERIFIED**` type cell and every "column name not documented" note. | The live Prisma schema or database is inspected and an errata entry publishes the real types. |
| Appendix C, writer/reader attribution | Services the old docs never name as writers or readers of a table. | Codebase traces confirm or correct the attribution. |
| Appendix D, routes not named in the old docs | The entire non-webhook, non-login REST surface. | Generated from the live OpenAPI spec at `/documentation/json` and re-verified. |
| Appendix D, error-code semantics | Status codes for failure modes described only narratively. | Observed in the running stack or read from the codebase. |
| Naming dualities | `riverbrand_sms_otp` versus `riverbrandsmsotp`; `DeviceToken` versus `sys_device_tokens`. | The codebase declares one canonical spelling and the errata adopts it. |

**Retirement procedure.** A marker is never edited away silently. The correction lands as an errata row citing its evidence, the **UNVERIFIED** marker is removed in the same change, and the version bumps at patch level. This keeps the book's uncertainty auditable: a reader of Edition 2.0.0 can see exactly what the documentation suite knew, and exactly what it did not.
