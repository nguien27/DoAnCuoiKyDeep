# QA REPORT - ViMedGraph Full Extraction v0.1

## Overall
- Diseases: 36
- Patterns parsed: 159
- Entities: 1227
- Explicit relations: 1982
- Derived relations: 572
- Candidate/unresolved mentions: 464

## Mapping
- SRC_001 unique disease mappings: 18/20
- SRC_001 ambiguous disease mappings: 2/20
- SRC_002 unmapped disease mappings: 16/16

## Integrity gates
- Duplicate entity IDs: 0
- Duplicate relations: 0
- Dangling relation endpoints: 0
- Invalid page ranges: 0
- Source-support failures: 0

## Conservative decisions
- Viêm khớp dạng thấp chapter is not assigned one serostatus code automatically because the source chapter title is generic.
- Đau dây thần kinh liên sườn / Hiếp thống retains two possible official code candidates.
- SRC_002 chapters are not forced into older codes from different modern diseases.
- Formula-herb `GỒM` relations are created only when an official formula is normalized and the ingredient is found inside a formula-local text span.

## Source-reference anomaly flags
- `1` used symptom row(s) carry a source/reference quality flag. See `reference_quality_flags_used.csv`. These are preserved, not silently corrected.
