param(
  [Parameter(Mandatory=$true)]
  [string]$Neo4jImportDir
)

$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Copying ViMedGraph CSV files to Neo4j import directory..."
Get-ChildItem $Here -Filter "*.csv" | Copy-Item -Destination $Neo4jImportDir -Force

Write-Host ""
Write-Host "Done."
Write-Host "Next:"
Write-Host "1) Start your Neo4j database."
Write-Host "2) Open Neo4j Browser."
Write-Host "3) Run neo4j_import.cypher statement by statement."
Write-Host "4) Run neo4j_qa.cypher and compare with expected counts."
