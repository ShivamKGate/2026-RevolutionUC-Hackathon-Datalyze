# Featherless migration note:
# Datalyze now defaults to Featherless remote inference, so no local pull is required.
# This script is kept as an optional fallback for local Ollama testing.

$ErrorActionPreference = "Stop"

$models = @("qwen2.5:14b", "llama3.2:3b", "nomic-embed-text")

foreach ($m in $models) {
  Write-Host "Pulling $m ..."
  ollama pull $m
}

Write-Host "Optional Ollama fallback models pulled."
