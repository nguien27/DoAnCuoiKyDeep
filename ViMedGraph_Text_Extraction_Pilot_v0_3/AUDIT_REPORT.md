# AUDIT REPORT - Text Extraction Pilot v0.3

## QA gate
- Gold entities: 323
- Predicted entities: 323
- Gold explicit relations: 543
- Predicted explicit relations: 543
- Gold derived relations: 140
- Predicted derived relations: 140

## Integrity
- Duplicate predicted entity IDs: 0
- Duplicate predicted relations: 0
- Predicted dangling relation endpoints: 0
- Invalid predicted page ranges: 0
- Semantic/source support failures: 0
- Raw PDF entity support failures: 0

## Evaluation
- Entity P/R/F1: 1.000/1.000/1.000
- Explicit relation P/R/F1: 1.000/1.000/1.000

## Data findings
- 1 reference-vs-corpus mismatch is preserved in `error_analysis.csv`.
- 1 named formula candidate (`Tam tý thang`) is kept without inventing an official code.
- 5 uncoded `Đối pháp lập phương` mentions are preserved in `unmapped_mentions.csv` and are not promoted to coded BÀI_THUỐC nodes.

## Version note
v0.2 exposed a serialization defect in `text_entities.csv` during QA: entity IDs were lost when exporting rows taken from an indexed DataFrame.
The relation extraction itself was not affected. v0.3 rebuilds and rechecks entity output; dangling endpoints are now zero.
