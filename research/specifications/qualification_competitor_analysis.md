# Qualification Engine — Competitor Identity Forensic Analysis

**Status:** Documentation only. Forensic Evidence Mode — no production code, interfaces, or tests. This document re-searches every source category the audit itself asked for; it does not repeat `qualification_evidence.md`'s general survey, it drills into the single remaining blocker: QUAL-007, the competitor identity.

**Sources searched this pass** (beyond what `qualification_evidence.md` already covered): `TRADINGVIEW_HIDDEN_RULES.md`, `INVESTIGATIONS.md` (all closed investigations, full text), `CHANGELOG.md`, `SPECIFICATION.md`, `REQUIREMENTS_TRACEABILITY_MATRIX.md`, `docs/MATHEMATICAL_SPECIFICATION.md`, `docs/RULE_INDEX.md`, `docs/GAP_ANALYSIS.md`, `BUSINESS_ARCHITECTURE.md`, `BUSINESS_EVENT_FLOW.md`, `BUSINESS_SEQUENCE_DIAGRAM.md`, the raw `research/transcripts/TR-001.md` transcript text (not just its analysis document), `orb_levels.db`'s table schema, every `.xlsx` file in the repository, and a repository-wide check for image files (none exist beyond vendored library assets). No new document, transcript, database field, or export was found beyond what earlier sprints already catalogued.

---

## 1. What exactly is TP High compared against?

**Field-level answer (confirmed):** `Top Strike CE > competitor PE Low` AND `Top Strike PE < competitor CE High` (`STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7).

**Strike-identity answer:** Not resolved by any source. The comparison *fields* (PE Low, CE High) are named; the *strike* those fields belong to ("competitor") is never identified.

## 2. What exactly is TP Low compared against?

**Field-level answer (confirmed):** `Bottom Strike CE > competitor PE High` AND `Bottom Strike PE < competitor CE Low` — the mirror of TP High (§7).

**Strike-identity answer:** Same gap as TP High — unresolved.

## 3. Does the competitor change during replay?

**No evidence found, in either direction.** No source states whether the competitor strike is fixed for the session or re-evaluated per candle/update cycle. This question cannot even be answered "no evidence, defaults to X" — there is no default stated anywhere.

## 4. Is the competitor Weekly Future / Top Strike / Bottom Strike / Reference Level / Premium / ORB / something else?

**No source identifies the TP-stage competitor as any of these.** Specifically:

- **Weekly Future** — never described as a comparison target for TP; Weekly Future feeds Strike Selection (already resolved), not TP qualification.
- **Top Strike / Bottom Strike** — these are the subjects *being tested* (§7's own wording: "Top Strike CE > competitor..."), not the competitor itself. A strike cannot be its own competitor per the stated test shape.
- **Reference Level** — the reference ladder supplies CE/PE High/Low for *every* strike in the 13-level ladder (already built by `ReferenceBuilder`), but no source states which of the other 12 levels — if any — is "the competitor."
- **Premium** — "Premium" is used generically throughout the source material to mean any option's own price; it is not itself a candidate for "which strike."
- **ORB** — no source connects Opening Range Breakout to the TP competitor concept in any way.
- **Something else** — the only "competitor" concept confirmed *anywhere* in this repository is the Exit Engine's own (`STRATEGY_FUNCTIONAL_SPECIFICATION.md` Rule 2, CONFIRMED): for a Winner at strike S, the Exit-stage competitor is `PE(S-1)` (CE side) or `CE(S+1)` (PE side) — the same-anchor, opposite-side, adjacent-rung strike. This is explicitly a **post-Winner, Exit-monitoring** concept. Three independent sources each state, unprompted, that this must **not** be assumed to define the pre-Winner TP competitor:
  - `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7: "TP High/TP Low's competitor... is not stated to use the same S±1 pattern, and this document does not assume it does."
  - `BUSINESS_ARCHITECTURE.md` §3 (TPEngine): "explicitly not the same as `ExitEngine`'s already-confirmed competitor mapping (Specification Rule 2); that mapping is for a different purpose... and must not be assumed to generalize here."
  - `REQUIREMENTS_TRACEABILITY_MATRIX.md`: separates "TP Calculation" (competitor identity: missing) from "Position Monitoring"/"Exit" (competitor mapping: confirmed) as two distinct rows with two distinct evidence states.

  Legacy code (`strategy/exit_signal.py`, examined via `INVESTIGATIONS.md` #9, #11, #13) confirms this same Exit-stage competitor is "SAME-anchor, OPPOSITE-side ladder" and is used exclusively for exit-triggering on an already-open trade — never for a pre-entry qualification decision. This is real, load-bearing evidence about what "competitor" means in the one context it *is* defined — but that context is Exit, not Qualification, and every source that mentions both concepts in the same breath does so specifically to warn against conflating them.

## 5. How is the competitor selected?

**No evidence found.** No selection rule, formula, or worked example exists anywhere in the audited source material for the TP-stage competitor. (The Exit-stage competitor's selection rule — adjacent rung by strike, S±1 — is fully confirmed, but per §4 above, applying it here would be assuming a transfer the evidence explicitly warns against.)

## 6. Is there more than one competitor?

**No evidence found, in either direction.** No source states whether TP High and TP Low share a single competitor or have distinct competitors from each other. No source states whether a strike could have more than one simultaneous competitor.

## 7. Sources supporting each answer

| Question | Supporting sources |
|---|---|
| Field-level comparison (Q1, Q2) | `research/specification/STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7; `BUSINESS_ACCEPTANCE_SPECIFICATION.md` §4-5; `research/specifications/QUALIFICATION_ENGINE_EVIDENCE_REQUIREMENTS.md` §1 |
| Cadence/change-during-replay (Q3) | No source — absence confirmed across all files searched |
| Candidate identities considered and ruled out (Q4) | `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §7; `BUSINESS_ARCHITECTURE.md` §3, §4; `REQUIREMENTS_TRACEABILITY_MATRIX.md`; `INVESTIGATIONS.md` #9, #11, #13 (Exit-stage competitor's own definition, confirmed for a different purpose) |
| Selection rule (Q5) | No source for the TP-stage competitor; Exit-stage competitor's rule is in `STRATEGY_FUNCTIONAL_SPECIFICATION.md` §11/Rule 2 (not transferable per Q4) |
| Multiple competitors (Q6) | No source — absence confirmed |

---

## Confidence

**UNKNOWN for the competitor's identity itself** — not Low, not Medium: there is no partial statement anywhere to assign even a Low confidence to. **HIGH confidence that this gap is genuine and has been exhaustively searched for** — every document category the forensic prompt named was checked this pass, and the result is consistent with, not merely repeated from, the earlier audit: silence on the TP-stage competitor, combined with three independent, explicit warnings not to substitute the Exit-stage competitor in its place.
