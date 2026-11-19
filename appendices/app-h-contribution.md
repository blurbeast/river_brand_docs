# Appendix H: Contribution and Documentation Standards

This appendix is the process contract for everyone who writes, edits, or reviews the Riverbrand Knowledge Book. It exists because the difference between the First Edition's fourteen-file suite and the Second Edition's textbook is not more words — it is a standard that every page is held to. If you are fixing a typo, skim the checklist at the end. If you are writing or restructuring content, read this appendix in full and the machine-adjacent standard at `scripts/CONTENT-STANDARD.md` before you touch a chapter. The checker enforces much of what follows; the rest is enforced by review.

## What This Standard Covers

Seven things, in the order you will need them: file layout and H1 rules; section numbering; heading and anchor hygiene; the honest-tone standard (what you may not write, and what to write instead); the non-technical jargon ban; figure and cross-link conventions; and the **UNVERIFIED** policy. Then the operational half: glossary-first terminology, regenerating the table of contents and sidebar, running the verifier, and the pull-request checklist.

## File Layout and H1 Rules

The book has three content trees: `front-matter/` (files `f01-title-page` through `f07-list-of-figures`), `chapters/` (`ch01-` through `ch16-`), and `appendices/` (`app-a-` through `app-i-`). Chapter filenames are `chNN-slug.md`, and the number in the filename must equal the number in the document's H1 and in the sidebar label. Chapter H1s take exactly this form: `# Chapter N — Title`. Appendices take `# Appendix X: Title` and live at fixed slugs — never renumber or rename an appendix file without updating every inbound link and the sidebar.

Chapter skeleton order is fixed: epigraph, then `## Recap` (three bullets: Unlearn / Learn / Relearn, rewritten to be specific to your chapter's arc), then the numbered sections, then `## Key Takeaways` (four to six bullets), then `## Frequently Asked Questions` (four to five questions, each question an H3), then `## Where to Go Next` with its twin cross-link. Word floors by chapter class: chapters 1–3 and 16 at least 2,500 words; non-technical twins (4, 6, 8, 10, 12, 14) at least 2,800; technical twins (5, 7, 9, 11, 13, 15) at least 3,500. Aim for the middle of the target range, not the floor.

## Section Numbering

Inside a chapter, H2s are numbered `N.M Section Title`, where N is the chapter number and M increments. Never reuse a `N.M` number inside a file — a duplicated `7.8` is a checker error, not a style slip. Unnumbered H2s are reserved for the recurring structural beats: `## Recap`, `## Key Takeaways`, `## Frequently Asked Questions`, `## Where to Go Next`. Appendices are exempt from chapter numbering: use unnumbered H2/H3 headings, or the lettered style (`## F.1 …`, `## C.1 …`) where a numbered sub-structure genuinely helps. Two rules apply everywhere: no duplicate heading text at the same level within a file, and for recurring beats like "What We Built", use bold paragraphs instead of repeated headings.

## Headings and Anchors

Headings must be ASCII anchor-safe: no emoji in headings, and the derived anchor must match `[a-z0-9-]+`. Punctuation like `&` is tolerated by the slug rule but "and" reads better and slugifies cleaner. The anchor of a heading is computed the docsify way: lowercase, strip inline markup and all punctuation, collapse whitespace to hyphens. So `## 5.4 The Outbox and Dead-Letter Queue` becomes `#54-the-outbox-and-dead-letter-queue`, and `## 3.5 The Schema-Prefix Map` becomes `#35-the-schema-prefix-map`. When you link a section, compute the anchor with that rule or copy it from the generated table of contents — never guess from memory.

## The Honest-Tone Standard

The book's voice is evidence over hype. Where you cannot cite a test, a measurement, or a documented mechanism, write "designed to…" or "verified in…", never a claim of perfect outcomes. The checker enforces a ban list on every file in the repository — chapters, appendices, and front matter alike. The patterns live in `scripts/check_structure.py` (`HYPE_WORDS`) and the boardroom summary is this: you may not write

1. the closed compound of "bullet" and "proof" promising perfect hardness;
2. "military grade" (the hyphenated form) as a strength claim;
3. the "un-" + "breakable" compound;
4. any "absolute … guarantee" formula, including the "mathematical" variant;
5. any "100%" claim about security, safety, or uptime;
6. bare availability figures floated without evidence (the "four nines" trope).

We describe the list rather than print it because the checker scans this appendix too — and a standard that exempts itself is not a standard. Spellings that dodge the regular expression (spacing, hyphenation) are still banned by policy; reviewers will catch them. What to write instead: name the mechanism ("every debit acquires a per-wallet distributed lock"), cite the verification you have ("verified in the end-to-end test runner"), and state the residual risk plainly ("if a server dies mid-transfer the lock expires on its own and safety rests on the database transaction").

## The Non-Technical Jargon Ban

Non-technical chapters (4, 6, 8, 10, 12, 14) never contain implementation identifiers. The checker rejects, in those files only: `rbp_brand_*` and `river_brand_*` table names, `jwt_version`, `.ts` file paths, the `x-local-access-token` and `x-web-access-token` header names, `prisma.$transaction`, `FOR UPDATE SKIP LOCKED`, and handler class names such as `KycTierUpgradedHandler`. Four words are allowed on first use, each defined in one line: NUBAN, KYC, ledger, wallet. Everything else gets the house treatment: explain by analogy first, formal name second in a single line — *"engineers call this the outbox pattern — see §5.4"* — and link rather than expand. The canonical analogies live once, in [Appendix F](app-f-analogy-atlas.md): cite and link them; do not retell them at length. Technical chapters have no such ban — that is where the table names, interfaces, and lock keys belong.

## Figures and Diagrams

Diagrams are content, not decoration. Two formats are sanctioned:

- **Mermaid** for live rendering in the web book: fenced ```mermaid blocks (sequenceDiagram, stateDiagram-v2, or graph TD). Each block is preceded by a bold caption on its own line: `**Figure N.M — Title.**` Figure numbers follow the chapter's `N.M` scheme and are listed in the list of figures.
- **Custom SVG** for the later production phase: insert a marker on its own line, never a link to an image file that does not exist. Marker format: `![Figure 5.2 — The Redlock guard](../images/fig-ch05-redlock-guard.svg)`.

Naming is fixed: `fig-chNN-slug.svg` — figure prefix, two-digit chapter number, kebab-case slug matching the figure's subject. Placeholder markers are how a chapter "orders" artwork before the asset exists; a raw markdown image link to a missing file is a defect.

## Cross-Links and Section References

Relative links only — `../chapters/ch05-engineering-transaction-engine.md#54-the-outbox-and-dead-letter-queue` style, never absolute filesystem paths or assumed hostnames. Every link and every anchor must resolve; the checker verifies both and fails the build when they do not. Cross-references to other parts of the book use the section sign form `§N.M` and are hyperlinked on first mention in a section. Chapters cross-link to their twins at the end ("Where to Go Next"); appendices link into chapters for mechanism depth and sideways into sibling appendices for vocabulary and process. When you move or rename a heading, search the repository for its old anchor before merging.

## The UNVERIFIED Policy

Any fact not grounded in the old documentation suite — the fourteen 2026 files in the repository root — gets an inline **UNVERIFIED** marker at the claim, not in a footnote. The rule is absolute because this repository contains no application source code: what the old docs do not say, the book does not know. Consequences for writers: never invent a column type, a status code, a route, or a performance number to make a passage flow; write `**UNVERIFIED**` and move on. Consequences for reviewers: an unmarked claim without a source is a review-blocking defect. Marked claims are counted in the [UNVERIFIED register](app-g-changelog.md#unverified-register) and retired only through an errata entry that cites its evidence. Appendix writers should remember that reference appendices (C and D) are the heaviest users of the marker by design — a data dictionary that guesses is worse than one that admits ignorance.

## Glossary-First Terminology

New terms land in [Appendix A: Glossary](app-a-glossary.md) before they are used in a chapter. The glossary is the book's single home for definitions; chapters define a term in one line at first use and link to Appendix A rather than keeping private definitions. Naming follows the branding rules: "Riverbrand Banking System" for the product and book, "RiverbrandBE" for the codebase, "RBP" only after first definition. Table prefixes are documented as-is (see [§3.5](../chapters/ch03-domain-primer.md#35-the-schema-prefix-map)); legacy names (`savings_*`, `user_user`) are flagged to-be-renamed wherever they appear. If you introduce a term and forget the glossary entry, the reviewer will send it back.

## Regenerating the Table of Contents and Sidebar

The book's navigation is generated from live headings — never edit it by hand.

- **Table of contents**: run `make toc`. This writes `front-matter/f06-table-of-contents.md` from the checker's heading scan (`./scripts/check-structure.sh --toc`). Run it after any heading change.
- **Sidebar**: run `make sidebar`. This runs `python3 scripts/gen_sidebar.py` and rewrites `_sidebar.md`. The checker asserts that every book file appears in the sidebar and that every chapter label carries its chapter number.

Both outputs are committed with your change so the rendered book and the repository never disagree.

## Verifying Your Work

Run `make verify` (which invokes `./scripts/check-structure.sh`) before every commit. It checks: the expected file set (front matter f01–f07, chapters ch01–ch16, appendices app-a…app-i); chapter filename number versus H1 versus sidebar label; `N.M` section numbering against the chapter number and duplicate section numbers; ASCII-safe heading slugs; duplicate headings within a file; that every relative link and anchor resolves; word-count floors per chapter class; the banned-tone list; the jargon ban in non-technical chapters; and sidebar completeness. While a chapter is still a skeleton, run `./scripts/check-structure.sh --no-wordcount` to check everything except word floors. Zero errors is the merge bar; warnings (for example duplicate headings) are treated as errors in review even though the checker counts them separately.

## Pull Request Checklist

Every PR that touches book content walks this list in order:

1. **Facts grounded.** Every claim is traceable to the old documentation suite, or carries an inline **UNVERIFIED** marker.
2. **No banned tone.** The honest-tone list above is clear in the diff — including in headings, captions, and tables.
3. **Jargon quarantined.** Non-technical chapters contain no implementation identifiers; new terms are defined by analogy first and glossed in Appendix A.
4. **Structure legal.** H1 format correct, `N.M` numbers unique within the file, no duplicate headings, skeleton order preserved for chapters.
5. **Anchors and links resolve.** Relative links only; moved headings have no dangling inbound anchors.
6. **Figures conform.** Mermaid blocks carry bold `**Figure N.M — Title.**` captions; artwork placeholders use `<!-- FIGURE: fig-chNN-slug.svg | … -->` markers and never link missing image files.
7. **Navigation regenerated.** `make toc` and `make sidebar` have been run and their outputs committed.
8. **Checker green.** `make verify` reports zero errors (or `--no-wordcount` during skeleton phase, with the shortfall noted in the PR).
9. **Errata honored.** Factual corrections add a row to [Appendix G](app-g-changelog.md) errata; retired **UNVERIFIED** markers cite their evidence there.
10. **Twin alignment.** If you changed a mechanism, its non-technical twin still describes the same behaviour — cross-the-aisle drift is how the First Edition became unreadable.

Reviewers verify the checklist rather than re-deriving the standard from scratch. That is the point of writing it down.
