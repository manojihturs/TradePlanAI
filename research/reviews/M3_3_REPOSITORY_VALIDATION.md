# Milestone 3.3 — Repository-Wide Consistency Review

Validation only. No repository document was modified while producing
this report. Every issue below is documented with an explanation and
a suggested fix — no fix was applied.

## Scope reviewed

`docs/TRADINGVIEW_STRATEGY_BIBLE.md` · `docs/RULE_INDEX.md` ·
`docs/EVIDENCE_MATRIX.md` · `docs/TRACEABILITY_MATRIX.md` ·
`docs/DOMAIN_MODEL.md` · `docs/TERMINOLOGY.md` ·
`docs/STATE_MACHINE.md` · `research/transcripts/TR-001.md` ·
`research/analysis/TR-001_ANALYSIS.md`

---

## 1. Executive Summary

The Milestone 3.2 changes themselves (Evidence Count/Confidence
updates for the 6 Bible rules, the 5 new Candidate entities, the IVL
Level Unknown Concept) are **internally consistent and correctly
isolated** — no candidate was accidentally promoted into the Bible,
Domain Model, or State Machine, and no duplicate ID exists anywhere in
the reviewed documents.

The review did surface one significant **pre-existing structural
gap**, not introduced by Milestone 3.2 but not previously caught
either: `DOMAIN_MODEL.md`, `TERMINOLOGY.md`, and `STATE_MACHINE.md`
have never actually assigned the `ENT-NNN`/`TERM-NNN`/`SM-NNN` ID
labels that `EVIDENCE_MATRIX.md` and `TRACEABILITY_MATRIX.md` use to
reference them throughout. Those three source documents identify their
entries by name only (`### Strike`, `### Trend Point Low (TP Low)`,
`### STATE: STRIKE_SELECTED`), so every `ENT-`/`TERM-`/`SM-` reference
in the two matrices resolves by name-matching, not by an ID actually
present in the target document. This is the single highest-priority
finding in this review.

A handful of minor cosmetic inconsistencies were also found (Section
4), plus one orphaned artifact (`STATE-001` in the Bible, tracked
nowhere else).

---

## 2. Passed Checks

| # | Checklist item | Result |
|---|---|---|
| 1 | Every Rule ID exists consistently across Bible / RULE_INDEX.md / EVIDENCE_MATRIX.md / TRACEABILITY_MATRIX.md | **PASS** — all 8 rule rows (STRIKE-001, TREND-001/002/003, OPPONENT-001/002/003, REVERSAL-001) present and matching in all four documents |
| 5 (partial) | Evidence Count identical across Bible / RULE_INDEX.md / EVIDENCE_MATRIX.md for the 6 TR-001-backed rules | **PASS** — all read 2 |
| 6 (partial) | Confidence identical across Bible / RULE_INDEX.md / EVIDENCE_MATRIX.md for the 6 TR-001-backed rules | **PASS** — all read Medium |
| 7 | Candidate entities NOT promoted into Strategy Bible / Domain Model / State Machine | **PASS** — searched all three for "Weekly Future," "Mid Point," "Trigger Point," "Sellers' Perspective," "Opening Range" — none found outside the matrices |
| 8 | Unknown Concepts remain isolated; IVL Level not a defined entity or rule | **PASS** — "IVL" appears only in `EVIDENCE_MATRIX.md`/`TRACEABILITY_MATRIX.md` (as `UNK-001`) and in `TR-001_ANALYSIS.md` (as a flagged gap) — absent from `DOMAIN_MODEL.md`, `TERMINOLOGY.md`, and the Bible |
| 11 | No duplicate IDs | **PASS** — `ENT-001`–`014`, `TERM-001`–`007`, `SM-001`–`005`, `EVID-001`–`007`, `UNK-001`, and all 8 rule IDs are each used exactly once, sequential, no gaps or collisions |
| Depends On / Referenced By consistency | Bible vs. RULE_INDEX.md | **PASS** — every rule's `Depends On`/`Referenced By` pair matches exactly between the two documents |
| Transcript file existence | `research/transcripts/TR-001.md` and `research/analysis/TR-001_ANALYSIS.md` | **PASS** — both files exist; spot-checked 2 of the analysis's line-number citations (line 33–38 for STRIKE-001, line 45 for the IVL Level reference) against the actual transcript content — both accurate |

---

## 3. Failed Checks

| # | Checklist item | Result | Explanation |
|---|---|---|---|
| 2 | Every Entity ID exists consistently across all documents | **FAIL** | `ENT-001` through `ENT-009` are used throughout `EVIDENCE_MATRIX.md` and `TRACEABILITY_MATRIX.md`, but `DOMAIN_MODEL.md` — the document these IDs are supposed to trace to — never assigns them. Its entries are headed only by name (`### Strike`, `### First Candle`, etc.), with no `ENT-NNN` label anywhere in the file. |
| — (same root cause) | Terminology ID consistency | **FAIL** | Same pattern: `TERM-001`–`007` are used in the two matrices but never appear in `TERMINOLOGY.md` itself (headed by name only: `### First Candle`, `### Strike`, etc.). |
| — (same root cause) | State ID consistency | **FAIL** | Same pattern again: `SM-001`–`005` are used in the two matrices but never appear in `STATE_MACHINE.md` itself (headed `### STATE: STRIKE_SELECTED`, etc., no `SM-NNN` label). |
| 10 | Every Traceability row references an existing artifact | **FAIL (partial)** | As a direct consequence of the above: every `TRACEABILITY_MATRIX.md` row citing an `ENT-`/`TERM-`/`SM-` ID references an artifact that is only resolvable by name-matching against `DOMAIN_MODEL.md`/`TERMINOLOGY.md`/`STATE_MACHINE.md`, not by an ID that actually exists in those files. The artifact itself exists (by name); the ID does not, in its source document. |

**Suggested fix (not applied):** Add the corresponding `ENT-NNN` /
`TERM-NNN` / `SM-NNN` label to each entry's heading in
`DOMAIN_MODEL.md`, `TERMINOLOGY.md`, and `STATE_MACHINE.md` (e.g.
`### ENT-001 — Strike` instead of `### Strike`), so the ID scheme
invented in the matrices is actually backed by a real label in the
source documents it claims to trace to.

---

## 4. Warnings

These are not failures — no data is wrong or inconsistent in meaning —
but are formatting/presentation gaps worth cleaning up.

1. **`OPPONENT-002`/`OPPONENT-003` don't follow the Bible's own rule
   lifecycle template.** The template (`TRADINGVIEW_STRATEGY_BIBLE.md`,
   "Rule lifecycle fields" section) requires every rule to show
   `Confidence`, `Evidence Count`, `Transcript Sources`, etc. The two
   placeholder rules show only `Title:` and `Status: Awaiting
   Evidence`. `RULE_INDEX.md` and `EVIDENCE_MATRIX.md` both separately
   record `Evidence Count = 0`/`Confidence = Unknown` for these two
   rules, so the *information* is consistent — it's just absent from
   its primary source (the Bible entry itself).
   **Suggested fix:** add the full template fields to OPPONENT-002/003
   in the Bible, with `Evidence Count: 0` and `Confidence: Unknown`
   made explicit rather than implied by omission.

2. **Confidence placeholder symbol differs for OPPONENT-002/003
   between `RULE_INDEX.md` (`-`) and `EVIDENCE_MATRIX.md` (`Unknown`).**
   Same meaning, different literal value — a strict string comparison
   between the two documents would flag this as a mismatch even though
   no one reading both would be confused.
   **Suggested fix:** standardise on one placeholder symbol (`Unknown`
   is recommended, since it matches the Confidence Policy's own
   0-evidence-count label) across both documents.

3. **Naming-scheme collision risk: `STATE` (Bible rule category) vs.
   `SM-` (State Machine artifact prefix).** The Bible's fixed category
   taxonomy includes `STATE` as a category that rules can belong to
   (implying rule IDs like `STATE-001`, `STATE-002`...), while
   `STATE_MACHINE.md`'s actual state artifacts use a completely
   different prefix (`SM-001`...`SM-005`). These are two different ID
   namespaces for adjacent concepts (a *rule about* a state vs. the
   *state itself*), which is workable but not self-evidently
   distinguished to a new reader.
   **Suggested fix:** add a one-line clarifying note in
   `TRADINGVIEW_STRATEGY_BIBLE.md`'s category taxonomy section
   explaining that `STATE`-category rules and `SM-`-prefixed state
   artifacts are deliberately separate namespaces.

---

## 5. Orphan References

| Artifact | Found in | Missing from | Explanation |
|---|---|---|---|
| `STATE-001` | `TRADINGVIEW_STRATEGY_BIBLE.md` (`## STATE` section, bare `Description:` / `Possible Transitions:` stub, no content filled in) | `RULE_INDEX.md`, `EVIDENCE_MATRIX.md`, `TRACEABILITY_MATRIX.md` | This is a leftover template stub, predating the Analysis Version 2 lifecycle-field refactor (it doesn't even use the current template — no `Confidence`/`Evidence Count`/etc. fields). It is not tracked as a rule in any of the three ledger documents, and has no content. |

**Suggested fix (not applied):** Either (a) populate `STATE-001` with
real content and add it to the three ledger documents once evidence
exists, or (b) remove the empty stub from the Bible until there is
something to record, noting its removal in the Refactor/Changelog
section so the deletion itself stays traceable.

No other orphan references were found. Every `ENT-`, `TERM-`, `SM-`,
`EVID-`, and rule-ID reference inside `EVIDENCE_MATRIX.md` and
`TRACEABILITY_MATRIX.md` corresponds to a real (if unlabeled — see
Section 3) entry somewhere in the source documents.

---

## 6. Duplicate IDs

**None found.** Checked: all 8 rule IDs, `ENT-001`–`014`,
`TERM-001`–`007`, `SM-001`–`005`, `EVID-001`–`007`, `UNK-001`. Every
sequence is strictly sequential with no repeated number, no skipped
number, and no cross-type collision (e.g. no `ENT-001` also used as a
`TERM-001`-equivalent under a different type).

---

## 7. Confidence Consistency

| Rule | Bible | RULE_INDEX.md | EVIDENCE_MATRIX.md | Match? |
|---|---|---|---|---|
| STRIKE-001 | Medium | Medium | Medium | ✓ |
| TREND-001 | Medium | Medium | Medium | ✓ |
| TREND-002 | Medium | Medium | Medium | ✓ |
| TREND-003 | Medium | Medium | Medium | ✓ |
| OPPONENT-001 | Medium | Medium | Medium | ✓ |
| OPPONENT-002 | (absent — see Warning 1) | `-` | Unknown | ✗ cosmetic mismatch (Warning 2) |
| OPPONENT-003 | (absent — see Warning 1) | `-` | Unknown | ✗ cosmetic mismatch (Warning 2) |
| REVERSAL-001 | Medium | Medium | Medium | ✓ |

Candidates (`ENT-010`–`014`) and `UNK-001`: all show `Low (Derived
from TR-001 only)` in `EVIDENCE_MATRIX.md`, matching the instruction
exactly. These have no Confidence field in `DOMAIN_MODEL.md`/
`TERMINOLOGY.md` since they were correctly not added there.

---

## 8. Evidence Consistency

| Rule | Bible Evidence Count | RULE_INDEX.md | EVIDENCE_MATRIX.md | TRACEABILITY_MATRIX.md (Evidence ID count) | Match? |
|---|---|---|---|---|---|
| STRIKE-001 | 2 | 2 | 2 | 2 (EVID-001, EVID-007) | ✓ |
| TREND-001 | 2 | 2 | 2 | 2 (EVID-002, EVID-007) | ✓ |
| TREND-002 | 2 | 2 | 2 | 2 (EVID-003, EVID-007) | ✓ |
| TREND-003 | 2 | 2 | 2 | 2 (EVID-004, EVID-007) | ✓ |
| OPPONENT-001 | 2 | 2 | 2 | 2 (EVID-005, EVID-007) | ✓ |
| OPPONENT-002 | (absent) | 0 | 0 | 0 (none) | ✓ (consistent by omission) |
| OPPONENT-003 | (absent) | 0 | 0 | 0 (none) | ✓ (consistent by omission) |
| REVERSAL-001 | 2 | 2 | 2 | 2 (EVID-006, EVID-007) | ✓ |

**Note on Evidence ID resolvability:** `EVID-001` through `EVID-006`
resolve only to "user conversational statement (session 2026-07-27) -
not saved to `/research`" — a description, not a re-checkable file.
This is consistently and honestly disclosed everywhere it appears
(not a hidden gap), so it is not counted as a Failed Check, but it
does mean 6 of the 7 Evidence IDs in the project are not independently
verifiable against a stored artifact. Only `EVID-007` (TR-001)
resolves to an actual file (`research/transcripts/TR-001.md`),
confirmed to exist.

EVID-007 is correctly counted as **one** source across all 6 rules
(not one per daily segment within TR-001) — verified consistent in
both `EVIDENCE_MATRIX.md` and `TRACEABILITY_MATRIX.md`.

---

## 9. Candidate Promotion Check

Searched `docs/TRADINGVIEW_STRATEGY_BIBLE.md`, `docs/DOMAIN_MODEL.md`,
and `docs/STATE_MACHINE.md` in full for each of the 5 Milestone 3.2
candidates and for "IVL":

| Candidate | In Bible? | In Domain Model? | In State Machine? |
|---|---|---|---|
| Weekly Future | No | No | No |
| Mid Point | No | No | No |
| Trigger Point | No | No | No |
| Sellers' Perspective | No | No | No |
| Opening Range | No | No | No |
| IVL Level | No | No | No |

**Result: PASS on all counts.** No candidate or unknown concept has
been accidentally promoted into any of the three protected documents.
All 5 candidates and the 1 unknown concept exist exclusively in
`EVIDENCE_MATRIX.md` and `TRACEABILITY_MATRIX.md`, correctly marked
`Candidate`/`Unknown Concept` status and not cross-referenced by any
existing Rule's `Depends On`.

---

## 10. Reviewer Recommendation

1. **Priority fix (structural):** Back-fill `ENT-NNN`/`TERM-NNN`/
   `SM-NNN` ID labels into `DOMAIN_MODEL.md`, `TERMINOLOGY.md`, and
   `STATE_MACHINE.md` headings. This is the one finding that actually
   undermines the traceability system's core promise ("every artifact
   traceable from evidence to implementation") — right now the IDs
   only exist in the ledger, not in the things they claim to identify.
   This is pre-existing debt from before Milestone 3.2, not something
   introduced by it, but it should be the next priority before the
   project accumulates more artifacts on top of an unlabeled
   foundation.
2. **Low priority (cosmetic):** Resolve Warnings 1–3 (OPPONENT-002/003
   template completeness, `-` vs `Unknown` placeholder symbol,
   STATE/SM naming clarification) whenever convenient — none affect
   data correctness.
3. **Low priority (cleanup):** Decide the fate of the orphaned
   `STATE-001` stub (populate or remove, per Section 5).
4. **No action needed** on Candidate/Unknown Concept isolation or
   duplicate IDs — both are clean.
5. Milestone 3.2's actual approved changes (Evidence Count/Confidence
   propagation, the 5 candidates, IVL Level) were applied **correctly
   and consistently** everywhere they were supposed to be applied. The
   process worked as designed for this round.

---

## Overall Repository Health Score: **80 / 100**

**Basis:** No duplicate IDs, no accidental candidate/unknown-concept
promotion, and 100% internal consistency for everything Milestone 3.2
actually changed (Evidence Count, Confidence, the new candidates) —
these are the highest-risk items for this milestone and all passed
cleanly. The score is held below 90 by one real, systemic
pre-existing gap (ID labels missing from `DOMAIN_MODEL.md`/
`TERMINOLOGY.md`/`STATE_MACHINE.md` themselves) that affects
traceability verifiability across the whole project, plus a small
number of minor cosmetic inconsistencies and one orphaned stub. No
issue found rises to a data-correctness or evidence-fabrication
problem.
