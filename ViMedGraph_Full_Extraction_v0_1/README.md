# ViMedGraph Full Extraction v0.1

## Scope
- SRC_001: 20 disease chapters
- SRC_002: 16 disease chapters
- Total: 36 disease chapters

## Safety policy
This package uses conservative normalization. It does not invent codes.
- SRC_001: official 2025 terminology registries can normalize many diseases/patterns/symptoms/formulas.
- SRC_002: the current terminology files in this project predate the late-2025 Tập II guide; disease codes are therefore kept unmapped unless a safe modern-condition match exists. In v0.1 all 16 SRC_002 diseases remain unmapped.
- Ambiguous mappings stay ambiguous and are listed in `disease_mapping.csv` / `pattern_mapping.csv`.
- Unresolved named treatments and raw symptom paragraphs are preserved in `candidate_mentions.csv`.

## Graph-ready files
- `full_entities.csv`
- `full_relations.csv`

## Mapping / QA files
- `disease_mapping.csv`
- `pattern_mapping.csv`
- `formula_mapping.csv`
- `candidate_mentions.csv`
- `candidate_formula_mentions.csv`
- `candidate_symptom_text.csv`
- `disease_mapping_review.csv`
- `pattern_mapping_review.csv`
- `quality_flags.csv`
- `source_support_failures.csv`
- `extraction_summary.csv`
- `pilot_regression.csv`
- `qa_summary.json`

## Important
This is a high-confidence rule-based baseline, not expert-reviewed final medical knowledge. Do not treat unnormalized candidates as verified KG facts.

## Source-reference anomaly flags
- `1` used symptom row(s) carry a source/reference quality flag. See `reference_quality_flags_used.csv`. These are preserved, not silently corrected.
