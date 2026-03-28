"""
Ollama model configuration for Datalyze.

Hardware floor: Machine B — RTX 4070 12GB VRAM, Ryzen 7 7700X, 32GB RAM.
All models must run comfortably on both team systems.
"""

from typing import TypedDict


class OllamaModelEntry(TypedDict):
    id: str
    tier: str
    notes: str


HARDWARE_SUMMARY = (
    "Machine A: i9-12900K, 64GB RAM, 16GB VRAM | "
    "Machine B: Ryzen 7 7700X, 32GB RAM, RTX 4070 12GB VRAM. "
    "All models chosen to fit 12GB VRAM single-model GPU inference."
)

DEFAULT_HEAVY_MODEL = "qwen2.5:14b"
DEFAULT_LIGHT_MODEL = "llama3.2:3b"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"

MODELS: list[OllamaModelEntry] = [
    {
        "id": "qwen2.5:14b",
        "tier": "heavy",
        "notes": "Primary heavy model for orchestration, synthesis, insights, and summaries.",
    },
    {
        "id": "llama3.2:3b",
        "tier": "light",
        "notes": "Primary light model for routing, tagging, cleaning, and low-latency sub-agents.",
    },
    {
        "id": "nomic-embed-text",
        "tier": "embedding",
        "notes": "Embedding model for pgvector / retrieval agents.",
    },
]


def pull_commands() -> list[str]:
    return [f"ollama pull {m['id']}" for m in MODELS]
