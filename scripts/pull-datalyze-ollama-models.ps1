# Pull Ollama models for Datalyze (12GB VRAM floor — fits both team PCs).
# Prereq: Ollama installed and `ollama serve` running in another terminal.

$ErrorActionPreference = "Stop"

$models = @(
  "qwen2.5:14b",
  "llama3.2:3b",
  "nomic-embed-text"
)

foreach ($m in $models) {
  Write-Host "Pulling $m ..."
  ollama pull $m
}

Write-Host "All Datalyze models pulled."
