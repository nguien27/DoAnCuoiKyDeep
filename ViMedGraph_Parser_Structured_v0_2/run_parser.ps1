$ParserDir = $PSScriptRoot
$ProjectRoot = Split-Path $ParserDir -Parent

python "$ParserDir\extract_structured_appendices_v0_2.py" `
  --data-dir "$ProjectRoot\Data\raw" `
  --gold-dir "$ProjectRoot\ViMedGraph_Pilot_Gold_v0_3" `
  --out-dir "$ProjectRoot\Data\processed\structured_v0_2"
