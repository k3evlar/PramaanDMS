# Novelty, Research Questions and Hypotheses

Phase 1 deliverable, updated on 16 October 2026 to the decisions locked before Phase 2 (English only, Tampered with Major or Minor severity).

## 1. The gap

Existing integrity methods are either exact (cryptographic hashes and signatures), so every rescan looks tampered, or tolerant (fuzzy, perceptual and semantic hashes), so small content edits can slip through and no method names the fact that changed. Document forgery detectors find suspicious regions in one image but do not compare against a sealed original or name the changed legal field, and none of the cited work explains changes in terms of the legal fields of police documents. Tamper-evident logs protect the action history but are not linked to content verification, so they cannot show when a document changed or who had access at that time.

This is based on the gap table in `LITERATURE.md` (79 verified sources). It must be rechecked against a wider search before the paper is submitted.

## 2. Our contributions

We are honest about what is new. AES-256-GCM, SHA-256, HMAC, Ed25519, RFC 3161 timestamps, Merkle trees, MuRIL, triplet loss and perceptual hashing all exist already. Our novelty is in the tampering definition, in how we combine and apply these parts to legal documents, in the dataset, and in tamper window detection.

| # | Contribution | What is new | What we reuse |
|---|---|---|---|
| C1 | A legal-domain **tampering definition** | Four verdicts (Identical, Equivalent, Tampered with Major or Minor severity, Inconclusive) that separate format and capture changes from content changes, with a strict "reworded is Tampered" rule, "clear edit beats unreadable field" ordering, and 51 worked examples (`TAMPERING_DEFINITION.md`). | The general idea of separating content from presentation, used in robust and perceptual hashing work. |
| C2 | The **hybrid field-aware Legal Hash** | One fingerprint that combines exact keyed fingerprints of normalized critical fields (F), a learned binary hash of the narrative (N) and perceptual hashes of stamps and signatures (V), and returns which part changed and where. | HMAC-SHA-256, MuRIL, triplet loss, learning to hash, pHash or dHash, OCR engines. |
| C3 | The **FIR-Tamper dataset** | Synthetic English FIRs, witness statements and charge sheets with labelled tampering, equivalence traps (number and date formats, separators, reflow, fonts, honorifics), adversarial edits, and a real phone capture set. We have not found an existing dataset of this kind in our search (`LITERATURE.md`). | Standard data generation, rendering and augmentation methods. |
| C4 | **Tamper window detection** | Linking fingerprint checkpoints (every verify, export and copy issue) to an RFC 6962-style transparency log, so that a Tampered result narrows down when the change happened and who had access in that window. | Merkle trees, signed tree heads, inclusion and consistency proofs (Certificate Transparency). |
| C5 | A **benchmark with published error rates** | The first comparison (to our knowledge, see `LITERATURE.md`) of SHA-256, ssdeep, TLSH, whole-page pHash, OCR text diff and plain embedding similarity against the Legal Hash on the same legal document test set, per capture condition and per tamper type. | The baseline methods themselves and standard metrics. |

"To our knowledge" and "we have not found" mean: not found in the sources in `LITERATURE.md`. The literature search must be widened before the paper makes these claims final (TODO: verify in the paper's related work).

## 3. Research questions

| # | Research question | Experiment that answers it |
|---|---|---|
| RQ1 | Can a hybrid field-aware Legal Hash separate format and capture changes from content edits on English legal documents better than existing integrity and similarity methods? | Run the Legal Hash and all six baselines on the FIR-Tamper test split and the real capture set (Phase 11 and Phase 27). Compare false alarm rate on Equivalent copies and Tampered recall, per capture condition. |
| RQ2 | Does a contrastively trained binary narrative hash detect small wording edits while ignoring OCR and capture noise, and what does each part (F, N, V) add? | Train N (Phase 12). Compare with MuRIL mean-pooled cosine similarity on narrative edits. Ablation of F, N, F+N, F+N+V on validation (Phase 15) and test (Phase 27). |
| RQ3 | Can linking fingerprint checkpoints to a transparency log reliably narrow when a change happened and who had access? | Scripted scenarios with several users, copies and edits (Phase 24). Measure whether the true edit falls inside the reported window and how many users and events the window contains. |

## 4. Hypotheses

All numbers come from real runs. Thresholds are chosen on validation only. The test split is used once, in Phase 27.

| # | Hypothesis | Metric that tests it | Compared with |
|---|---|---|---|
| H1 | The Legal Hash has a lower false alarm rate on Equivalent copies (rescans, phone photos, reprints, format traps) than byte-level and similarity hashes. | False alarm rate on Equivalent copies, per capture condition. | SHA-256 (flags every non-identical copy by design), ssdeep, TLSH, whole-page pHash. |
| H2 | The Legal Hash catches critical field edits more reliably than OCR text diff and whole-page methods, at the same or lower false alarm rate. | Recall on Major changes at a fixed false alarm rate. Field-level change localization accuracy. | OCR text diff, whole-page pHash, plain embedding cosine. |
| H3 | The trained narrative hash N detects narrative edits better than an untrained embedding at the same false alarm rate. | Narrative edit recall and false alarm rate on validation (Phase 12), then test (Phase 27). | MuRIL mean-pooled cosine similarity. |
| H4 | Combining F, N and V gives higher overall Tampered recall than any single part, without a large rise in false alarms. | Ablation table: Tampered recall (Major and Minor) and false alarm rate for F, N, F+N, F+N+V. | Each part alone. |
| H5 | The Legal Hash keeps a usable Inconclusive rate on real phone photos. | Inconclusive rate per capture condition. | No baseline has this verdict. Reported as a trade-off curve against c_min. |
| H6 | In scripted scenarios, the true edit always falls inside the reported tamper window, and the window lists fewer users than the full custody history. | Fraction of scenarios where the edit is inside the window. Number of users and events in the window versus in the full history. | Full custody history with no window (the naive approach). |

The target values for these metrics (for example a maximum acceptable false alarm rate) are set in `docs/REQUIREMENTS.md` in Phase 2, not here.

## 5. What counts as a negative result, and how we report it

Each of these would be a negative result. We will report every one that happens, with error analysis. A clear negative result with analysis is still a valid finding.

| Negative result | How we would report it |
|---|---|
| N does not beat plain embedding cosine on narrative edits (H3 fails). | Report both numbers. Show which edit types N misses (for example punctuation, single word swaps). State that F still catches all critical field changes and that N is a partial result. |
| False alarm rate on phone photos is not lower than a baseline (H1 fails for some conditions). | Report per capture condition. Show where it fails (low light, folds, angle) and how many failures come from OCR versus the hash. |
| Results on real phone photos are much worse than on simulated captures. | Report per capture source. Separate OCR errors from hash errors. State the limit in `LIMITATIONS.md`. |
| Combining parts raises false alarms more than it raises recall (H4 fails). | Report the full ablation. Recommend the best combination for each use case. |
| Too many Inconclusive results on photos (H5 fails). | Publish the trade-off curve between Inconclusive rate and false alarm rate. |
| Tamper windows are too wide to be useful (H6 partly fails). | Report window sizes. Explain how more checkpoints (periodic re-checks) would narrow them. |
| Adversarial edits (homoglyphs, zero-width characters, small pixel edits) get through. | List each attack and its success rate in `RESULTS.md` and `LIMITATIONS.md`. |

We will not change thresholds on the test set after seeing results, drop failing conditions from tables, or report only the best run. Every result table records the git commit, dataset hash and command that produced it.

## 6. Paper-worthy points (kept up to date from Phase 2)

Each point says what is new, what will be measured, and what it is compared against. Results come from real runs only (Phase 27).

| # | Point | What is new | What is measured | Compared against |
|---|---|---|---|---|
| P1 | Legal tampering taxonomy with ordered decision rules | Four verdicts plus a "could not verify" list, where a clear edit always beats unreadable fields (D41), so blur cannot hide an edit | Share of tampered samples with an unreadable field that are still reported as Tampered | The spec's earlier order (blur first, D41 replaced it) and SHA-256 |
| P2 | Exact fingerprints for narrative entities inside free text | Dates, names, numbers, amounts and section numbers inside the narrative are HMAC-fingerprinted like fields (D45); the rest of the narrative stays semantic | Recall on narrative entity edits; false alarms on Equivalent copies | Narrative hash alone (N), plain embedding cosine, OCR text diff |
| P3 | Deterministic negation check beside a learned hash | Negation flips are Major and caught by a rule that does not depend on the model (D42) | Recall on negation flips with and without the rule | Narrative hash alone; SimCSE-style embeddings (literature 7.6) |
| P4 | Value-type-aware spacing rule | Standard separators are format, but a space that splits a value inside an ID, number or date is content (D40) | False alarms on separator traps; recall on split-value edits | OCR text diff with whitespace collapsing; TLSH |
| P5 | Public verification that reveals nothing | QR-sealed copies checked by anyone, with one fixed message and no field names, values or locations (D51) | Information leaked per response (by design: none); verify latency on a phone | Copy-detection QR codes (literature 9.7), which reject all copies |
| P6 | Tamper window from a transparency log | Fingerprint checkpoints linked to an RFC 6962-style log narrow when a change happened and who had access | Window width and correctness in scripted scenarios | Full custody history without a window |
| P7 | Threat model that includes attacks on the AI and on verification | 59 threats with a phase and a test each, including model swap, threshold change, blur-to-hide and redaction-to-hide | Share of threats with a passing test at Phase 27 | ASVS 5.0.0 Level 2 coverage (`ASVS_CHECKLIST.md`) |
| P8 | Licence-clean, reproducible stack | Every component checked against its official licence; byte-identical dataset rebuilds from a seed | Rebuild hash equality; licence table with no blockers | Typical student stacks using Vault, MinIO, Redis or Surya (all flagged in `LICENCES.md`) |
| P9 | Security-by-default evidence stack from the first build | Least-privilege database roles, internal-only service network, generated secrets with no defaults, read-only non-root app containers, and one CI script that runs every scanner identically on a laptop and in CI (Phase 3, D67 to D75) | Share of ASVS 5.0.0 Level 2 items met at each phase (23 of 253 after Phase 3); scanner findings per phase; time to a healthy stack | A plain FastAPI and Docker Compose starter (superuser database account, published service ports, no scanners), described from its configuration |
| P10 | Rule-checked labels | Ground truth is computed twice (model diff and per-class declaration) and then checked by a validator that encodes each locked rule as a named check (D77 to D80) | Label-rule violations per dataset version (the v0 dataset, labelled before the rules were locked, had 1,860 violations in 2,700 rows); share of a human 10% re-check that agrees with the labels | Datasets labelled by hand or by a single script with no independent rule check |
| P11 | Write-once intake with an accounted failure path | The SHA-256 is taken over the exact received bytes before any parser runs; the original goes to S3 Object Lock in compliance mode under a server key built from IDs and the hash; the database stores the exact storage version ID; and because a locked object cannot be rolled back, a failed database write leaves a `storage.orphaned` custody event instead of an untracked file (D83, D84) | Share of stored objects with a matching database row or orphan event (target: all); overwrite and delete attempts refused by the storage itself, per attempt type (app path, raw PUT, version delete, retention shortening, plain delete); intake latency per MB | A plain upload to a filesystem or an unlocked bucket, where an admin can replace or delete a file and the database cannot tell |
