# ViMedGraph Full Extraction v0.2

## What changed from v0.1
v0.2 does NOT guess or invent mappings. It performs a conservative review of all 464 candidate mentions and creates a KG-core subset safe for later Neo4j import.

## Candidate review result
- 464/464 candidates reviewed.
- 216 generic treatment markers closed as non-entity text markers.
- 248 candidates remain active:
  - 158 named formula mentions.
  - 90 raw symptom paragraphs.
- 0 candidate was automatically assigned a new official code.
- 41 formula names also occur somewhere in the current formula registry, but are NOT mapped because the exact clinical context is different or unresolved.
- 117 named formulas have no exact-name entry in the current formula registry.

## Mapping backlog
- 18 disease mappings remain unresolved/ambiguous.
- 92 pattern mappings remain unresolved/ambiguous.
- SRC_002 is kept source-grounded but not assigned official codes without an official terminology source.

## KG core
`kg_core_entities.csv` and `kg_core_relations_*.csv` contain only:
- official-coded entities, and
- dược liệu normalized by exact name/explicit alias from verified source data.

Derived relations are kept separate from explicit relations.

## Files added
- candidate_resolution.csv
- candidate_mentions_closed.csv
- candidate_mentions_active.csv
- candidate_review_summary.csv
- mapping_backlog.csv
- kg_core_entities.csv
- kg_core_relations_explicit.csv
- kg_core_relations_derived.csv
- official_registry_check.md

## Safety policy
No code is inferred from semantic similarity alone.
No ambiguous disease/pattern is forced to one candidate code.
No named formula is mapped to a code from another clinical pattern merely because the formula name is the same.
