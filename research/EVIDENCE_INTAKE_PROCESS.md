# Evidence Intake Process

**Purpose:** a repeatable process for handling every future piece of strategy source material (YouTube videos, transcripts, PDFs, images, screenshots, handwritten notes, chat messages, spreadsheets) so each is analyzed the same way the existing evidence (`research/transcripts/TR-001.md`) already has been. This document describes process only — it contains no trading rules, no code, and modifies no existing document.

**Status:** the framework (`v0.4.1-framework-stable`) is complete; the project is in Phase 2 (Strategy Recovery), waiting on external evidence. This process governs how that evidence gets handled once it arrives.

---

## Section 1 — Evidence Lifecycle

```
Incoming
   │  new material is dropped in research/incoming/, untouched, as received
   ▼
Extraction
   │  every explicit statement is pulled out verbatim (quote + exact source
   │  location — line number, timestamp, page, filename) with nothing
   │  paraphrased away and nothing filled in
   ▼
Verification
   │  each extracted statement is checked against Section 3's checklist —
   │  is it explicit, is it complete, is it internally consistent?
   ▼
Cross-check
   │  every extracted statement is compared against every existing evidence
   │  document (Section 4's list) — does it agree, conflict, or add new
   │  information nobody had before?
   ▼
Classification
   │  every statement is tagged with exactly one of Section 2's six
   │  categories
   ▼
Specification Update
   │  ONLY statements that pass verification and cross-check as either
   │  "CONFIRMS EXISTING" or "NEW" (and are classified Confirmed Rule or
   │  Worked Example) are used to update research/specification/ documents;
   │  everything else stays recorded but does not change the specification
   ▼
Implementation Approval
      the specification update is reviewed by the user; only after that
      review does Section 6's Implementation Gate apply and a blocked
      Sprint (5-9) may reopen
```

No step may be skipped, and no step may run ahead of the one before it — in particular, nothing moves to Specification Update without first passing through Verification and Cross-check, and nothing reaches Implementation Approval without Specification Update.

---

## Section 2 — Evidence Classification

Every extracted statement is tagged with exactly one of the following. These mirror the categories already used in `WeeklyFuture_Specification_v1.md` and the "Research & Reconstruct" workflow, applied consistently going forward.

| Category | Criteria |
|---|---|
| **Confirmed Rule** | Stated explicitly, in plain language or arithmetic, with no contradiction anywhere else in the same source or any cross-checked existing document. A rule is "confirmed" by consistency, not by how confidently it's spoken. |
| **Worked Example** | A specific, numbered instance of a calculation — concrete inputs, concrete steps, concrete outputs — as opposed to a general statement of a rule. Recorded verbatim, including any arithmetic mistakes the source itself makes; never corrected. |
| **Contradiction** | Two or more statements (within one source, or across sources) that cannot both be true — different values for the same fact, or a rule applied inconsistently. Both/all versions are recorded side by side; none is picked as "the real one" during extraction. |
| **Unknown** | A question the source material could reasonably be expected to answer but doesn't address at all — no statement exists either way. |
| **Assumption** | A statement whose truth depends on unstated context, or that the source itself flags as approximate/inferred rather than as a fixed rule (e.g., "this is normally around..." rather than "this is always..."). Assumptions are recorded but never promoted to Confirmed Rule without independent confirmation. |
| **Open Question** | A specific, answerable question that would resolve an Unknown or a Contradiction if the source (or its author) could be asked directly — written as a question, not a guess at the answer. |

**A statement never moves between categories by reinterpretation.** If new evidence resolves a Contradiction or answers an Unknown, that's a new intake pass producing a new classification — the old record stays as-is, for audit purposes.

---

## Section 3 — Verification Checklist

Before any extracted statement proceeds past Verification, confirm all of the following:

- [ ] **Quoted verbatim** — the extraction is an exact quote (or, for non-text media, an exact transcription/description), not a paraphrase.
- [ ] **Source location is precise** — line number (transcript), timestamp (video/audio), page number (PDF), or filename+description (image/screenshot) is recorded, not just "somewhere in the material."
- [ ] **No arithmetic has been corrected.** If the source made a calculation error, the error is recorded as spoken/written, not fixed.
- [ ] **No gap has been filled.** If the source doesn't state something, it is marked Unknown — never inferred from general trading knowledge or "what the author probably meant."
- [ ] **Internal consistency has been checked.** The same source has been scanned for every other mention of the same fact/rule before concluding it's unambiguous within that source alone.
- [ ] **Confidence is stated**, using the same High/Medium/Low scale already used in `WeeklyFuture_Specification_v1.md` and `WEEKLY_FUTURE_EVIDENCE_TABLE.md` — High only when the statement is unambiguous and (if a worked example) arithmetically self-consistent.

A statement that fails any box stays in Verification (or drops back to Extraction for another look) — it does not proceed to Cross-check incomplete.

---

## Section 4 — Cross-Reference Process

Every statement that passes Verification is compared, one by one, against each of the following existing documents:

- `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md`
- `research/specification/WeeklyFuture_Specification_v1.md`
- `research/analysis/WEEKLY_FUTURE_EVIDENCE_TABLE.md`
- `research/analysis/WEEKLY_FUTURE_VERIFICATION.md`
- `WEEKLY_FUTURE_BLOCKER_REPORT.md`
- `BUSINESS_RULE_INTEGRATION_GUIDE.md`
- Any other document under `research/specification/` or `research/analysis/` relevant to the topic the new evidence addresses (not limited to Weekly Future once other rules are being recovered)

For each comparison, tag the result as one of:

- **NEW** — no existing document addresses this fact at all.
- **CONFIRMS EXISTING** — an existing document already states the same thing, and the new source agrees.
- **CONTRADICTS EXISTING** — an existing document states something different, and the new source disagrees with it.

`CONTRADICTS EXISTING` findings are never silently resolved in favor of either source during this process — they are recorded as a Contradiction (Section 2) and require an explicit user decision, not an automatic "newer source wins" or "majority wins" rule.

---

## Section 5 — Decision Matrix

| Evidence outcome | Decision |
|---|---|
| At least one **Confirmed Rule** or internally-consistent **Worked Example**, classified **NEW** or **CONFIRMS EXISTING**, with **no unresolved Contradiction** on the same specific fact | **ACCEPTED** — proceeds to Specification Update |
| Every extracted statement is a **Contradiction**, an **Assumption**, or fails Section 3's checklist | **REJECTED** — moves to `research/rejected/` with a one-line reason; does not update the specification |
| Some statements are usable (Confirmed Rule / Worked Example) but do not, on their own, resolve the specific gap being investigated (e.g., confirms the rule's *shape* but not a clean numeric example) | **NEEDS MORE EVIDENCE** — moves to `research/verified/` (the usable parts are real, verified evidence) but the specification's `MISSING INFORMATION`/blocker status is not changed; document what specifically would still be needed |

This mirrors exactly the standard already applied to `TR-001.md` itself in `WEEKLY_FUTURE_VERIFICATION.md`: that source produced real, verified evidence (rule shape, input definitions) that is currently sitting at "NEEDS MORE EVIDENCE," not "REJECTED" — it was not thrown away, but it also didn't clear the bar to update the specification's blocked status.

---

## Section 6 — Implementation Gate

A recovered business rule may only move from "specification updated" to "approved for implementation" (i.e., a blocked Sprint 5–9 may reopen) when **all** of the following hold:

1. The rule has an explicit, unambiguous statement in at least one verified source (Section 5: **ACCEPTED**).
2. At least three independently worked examples exist that are each internally consistent (no self-contradiction) and mutually consistent with each other (same formula produces the same kind of result across all three) — matching the bar `WEEKLY_FUTURE_VERIFICATION.md` already established and found unmet for Weekly Future. For a rule with no natural "worked example" concept (e.g., a purely definitional/structural rule), this criterion is satisfied instead by the rule being stated identically, without variation, across at least three independent mentions.
3. Every `CONTRADICTS EXISTING` finding touching this rule (Section 4) has been explicitly resolved by the user, not by this process's own judgment.
4. The relevant `research/specification/` document has been updated to reflect the confirmed rule, with every remaining `MISSING INFORMATION`/`UNKNOWN` item for that rule either resolved or explicitly re-confirmed as still open.
5. The user has reviewed the updated specification and explicitly approved moving to implementation — this process produces a recommendation, never an automatic unblock.

Until all five hold, the corresponding Sprint stays exactly where it is today: a `typing.Protocol` stub in `src/interfaces/` raising `UnresolvedBusinessRuleError`, per `BUSINESS_RULE_INTEGRATION_GUIDE.md`'s existing convention.
