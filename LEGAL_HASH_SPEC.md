# Legal Hash Specification (Research Core)

Updated on 16 October 2026 to the decisions locked before Phase 2 (`DECISIONS.md` D39 to D56). English documents only.

## 1. Goal

Given a sealed original document and a candidate copy (any format: PDF, scan, phone photo), decide one of four verdicts and explain the differences:

- **Identical** : exact same file
- **Equivalent (Format)** : same content, only capture or format differs
- **Tampered** : content changed (Major or Minor), with a list of changes, plus a "could not verify" list for any unreadable fields
- **Inconclusive** : no clear change found, but some critical fields could not be read; needs human review

Redacted copies are not supported in v1: verification stops with a clear message and no verdict.

The candidate can be verified **without access to the original file**, using only the stored or QR-embedded fingerprint.

## 2. Why hybrid

A purely learned embedding is smooth by design. "12/03/2026" and "13/03/2026" produce nearly the same vector, so a learned hash alone can miss the most important tampering. Pure rules break on blurry photos and OCR noise. So the Legal Hash has three parts that cover each other:

| Part | Method | Catches | Ignores |
|---|---|---|---|
| **F: Field and entity fingerprint** | Extract, normalize, hash each critical field and each narrative entity (dates, times, names, numbers, amounts, vehicle and section numbers inside the narrative) with HMAC-SHA-256 | Any change to a key fact, even one digit, in the header or in the narrative | Formatting of the same value |
| **N: Narrative hash** | Transformer encoder + projection + binary hash layer, trained with triplet loss (encoder chosen in Phase 12, see section 7) | Wording changes in the rest of the free text, including negation flips | OCR noise, scan and photo artefacts |
| **V: Visual region hashes** | Detect stamp and signature regions, perceptual hash per region | Swapped or removed stamps and signatures | Lighting, small rotation, scale |

Plus **S: SHA-256** of the exact file bytes for the Identical verdict and for the BSA Section 63 certificate.

## 3. Pipeline

```
Input file
  -> SHA-256 (exact bytes)
  -> Preprocess (deskew, perspective correction, denoise, page split)
  -> OCR (text + boxes + per-token confidence)
  -> Redaction check (stop with a message if the copy is redacted)
  -> Field extraction (rules + regex first, then a token tagger)
  -> Narrative entity extraction (dates, times, names, numbers, amounts, vehicle and section numbers)
  -> Normalization
  -> F: per-field and per-entity HMAC fingerprints
  -> N: rest of the narrative text -> encoder -> binary hash (per chunk), plus a negation check per chunk
  -> V: stamp/signature regions -> perceptual hash
  -> Fingerprint record (signed)
```

## 4. Critical fields

The final list of 31 rows (rows 28 to 31 added for evidence and custody, D96), with types and comparison rules, is in `docs/CRITICAL_FIELDS.md`. Each field has a name, a type (date, time, number, name, place, section, id, text), and whether it is critical. Narrative entities are listed in section 2 of that document.

## 5. Normalization rules (examples)

The full rules are in `docs/CRITICAL_FIELDS.md` section 3. Summary:

- Indian number formats: "5,00,000", "500000", "5 lakh" (if detectable) to one canonical integer
- Dates: "12/03/2026", "12-03-2026", "12 March 2026", "12th Mar 2026" to ISO `2026-03-12`
- Section references: "u/s 303(2) BNS", "Section 303 (2) of BNS" to `BNS:303(2)`. Sections compare as a set
- Names: Unicode NFC normalization, whitespace collapse, case fold, honorifics removed for matching (raw text stored)
- Spacing: spacing between words and lines is format; inside an ID, number or date only the standard separators for that type are format, any other space is content
- Remove zero-width characters (with a warning). Detect and **flag** mixed-script homoglyphs instead of silently fixing them (homoglyph swapping is an attack)

Normalization must be tested with an "equivalence traps" test set. These must never produce Tampered.

## 6. Field fingerprint (F)

- `F_i = HMAC-SHA-256(k_field, field_name || ":" || normalized_value)` for each field, and the same for each narrative entity, with `field_name` set to `narr:<type>:<position>`
- Key `k_field` is held in OpenBao (D57). HMAC (not plain hash) stops guessing attacks on short values like dates.
- Stored per document as an ordered map of field name to fingerprint, plus the field's page and bounding box.
- The QR contains a compact signed form (see section 10).

Comparison: any field fingerprint mismatch means that field changed. Missing or extra fields are also changes.

## 7. Narrative hash (N)

N covers the narrative text after the narrative entities (section 6) have been taken out and replaced by typed placeholders (for example `<DATE>`, `<NAME>`). This keeps N from having to notice one-digit changes, which F already catches exactly.

- **Encoder:** chosen in Phase 12 by validation results. Candidates, all with licences that allow commercial use (`docs/LICENCES.md`): MuRIL base (`google/muril-base-cased`, Apache-2.0), `intfloat/e5-base-v2` (MIT), `bert-base-uncased` (Apache-2.0), `sentence-transformers/all-MiniLM-L6-v2` (Apache-2.0). Documents are English only (D39).
- **Chunking:** split narrative into sentence windows (for example 3 sentences, stride 1) under 512 tokens.
- **Head:** projection layer to d dimensions (for example 256), then a binary hashing layer (tanh during training, sign at inference) giving a 256-bit code per chunk.
- **Training:** triplet loss with margin. Anchor = clean text. Positive = same text after OCR noise from a print or photo capture. Negative = same text with a real wording edit. Use **hard negatives** (single word swap, negation added, sentence reworded).
- Add a quantization loss so tanh outputs stay near plus or minus 1.
- **Comparison:** Hamming distance per aligned chunk. Chunks are aligned by sequence alignment over chunk order. Distance above threshold `t_N` marks a changed chunk. The changed chunk text is shown in the diff to authenticated users with access to the case.
- **Negation check (deterministic):** for each aligned chunk pair, count negation cues per clause (`not`, `n't`, `no`, `never`, `nor`, `neither`, `none`, `nothing`, `without`) after OCR clean-up. A different count in an aligned clause is a negation flip, which is **Major** (D42). This rule does not depend on the learned model, so a model miss cannot hide a negation flip.
- **Thresholds** are chosen on a validation set, never on the test set.

## 8. Visual region hashes (V)

- Detect stamp, seal and signature regions (simple colour and shape heuristics first; a small detector is optional).
- Perceptual hash (pHash or dHash) per region after alignment.
- Region missing, extra, or Hamming distance above `t_V` means change.
- Visual changes report as Tampered (Major) with the region location.
- Unsealed annotations (ink or pencil marks with no seal) are found as new marks after page alignment. Outside any critical field they are Minor and flagged; overlapping a critical field's box they are Major (D46).

## 9. Verdict logic

```
if SHA256(candidate) == S:            return Identical
if candidate is a redacted copy:      stop: "Redacted copies are not supported in this version."
run pipeline on candidate
unreadable = critical fields and narrative entities with OCR confidence < c_min
changes    = clear field diffs + entity diffs + narrative chunk diffs + negation flips
             + visual diffs + page changes + annotations
if changes:                           return Tampered(severity(changes), changes, could_not_verify = unreadable)
if unreadable:                        return Inconclusive(could_not_verify = unreadable)
return Equivalent
```

`severity(changes)` is Major if any change is: a critical field change (value changed, added or removed, including law sections), a narrative entity change, a negation flip, a page added, removed or reordered, a visual region change, or an annotation overlapping a critical field. Otherwise it is Minor (wording, punctuation, name order, non-critical field, annotation outside critical fields). The full rule and 51 worked examples are in `docs/TAMPERING_DEFINITION.md`.

Every verdict record stores: verdict, changes, the "could not verify" list, confidences, thresholds, model version, OCR engine and version, normalization rules version, code version (git commit), timestamp. This makes results **repeatable**: a stored verdict can be re-run and must give the same answer.

## 10. Fingerprint record and QR-sealed copy

- Fingerprint record = { doc_id, version, S, F map (fields and narrative entities), N codes, V hashes, page count, model_version, rules_version, created_at, RFC 3161 token reference }.
- Signed with the system Ed25519 key.
- A **QR-sealed copy** is a printed or PDF copy issued by a Supervisor (D50). It carries a QR with: doc_id, version, a short hash of the full record, and the signature. The verify page fetches the full record by doc_id. The QR payload holds no document content.
- The full original file is never needed for public verification.
- **Public output (D51):** the public verify page shows one fixed message per outcome. For a Major change the message is "A critical field was changed." It never shows field names, values or locations. Authenticated staff with access to the case see the full change list.

## 11. Robustness and security of the model

- **Model integrity:** the model file is hashed and signed. The service refuses to load a model whose hash does not match the registry.
- **Data integrity:** training data is versioned (hash of each dataset split recorded).
- **Adversarial tests:** homoglyphs, zero-width characters, single-character swaps, white-out style image edits, small pixel edits on digits, re-photographing a screen.

## 12. Evaluation

Metrics, per tamper type and per capture condition (clean PDF, scan, phone photo, bad lighting, folded):

- Tampered recall (catch rate), split Major and Minor
- False alarm rate on Equivalent copies (most important for trust)
- Inconclusive rate
- Field-level change localization accuracy
- Latency per page

Baselines: SHA-256, ssdeep (evaluation only, GPL), TLSH, pHash (whole page), OCR text diff, plain embedding cosine similarity.

Ablations: F only, N only, F+N, F+N+V.

All numbers come from real runs. Report the **known error rate** clearly.
