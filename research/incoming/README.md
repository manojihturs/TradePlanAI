# incoming/

Drop zone for new, not-yet-analyzed strategy evidence: transcripts, PDFs, screenshots, notes, or any other source material as it's found.

**Workflow:** place a new source file here → run the strategy-evidence-extraction prompt against it (produces `NEW_STRATEGY_EVIDENCE.md`, `NEW_WORKED_EXAMPLES.md`, `SPECIFICATION_CHANGES.md`) → once the extraction is reviewed and accepted, move the source file to `research/verified/`. If the material turns out to be irrelevant, duplicate, or unusable, move it to `research/rejected/` instead, with a one-line note on why.

Nothing in this folder should be treated as confirmed evidence until it has moved to `verified/`.
