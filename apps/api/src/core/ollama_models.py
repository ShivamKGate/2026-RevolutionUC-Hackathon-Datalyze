"""
Model configuration for Datalyze.

Current default provider: Featherless (remote inference).
"""

from typing import TypedDict


class OllamaModelEntry(TypedDict):
    id: str
    tier: str
    notes: str


HARDWARE_SUMMARY = (
    "Featherless remote inference enabled. Local GPU VRAM is no longer the primary model-size constraint."
)

DEFAULT_HEAVY_MODEL = "Kimi-K2.5"
DEFAULT_HEAVY_ALT_MODEL = "DeepSeek-V3.2"
DEFAULT_LIGHT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"

MODELS: list[OllamaModelEntry] = [
    {
        "id": DEFAULT_HEAVY_MODEL,
        "tier": "heavy",
        "notes": "Orchestrator-only: planning, coordination, dispatch (HEAVY_MODEL).",
    },
    {
        "id": DEFAULT_HEAVY_ALT_MODEL,
        "tier": "heavy_alt",
        "notes": "Non-orchestrator heavy work: aggregation, insights, SWOT, exec summary (HEAVY_ALT_MODEL).",
    },
    {
        "id": DEFAULT_LIGHT_MODEL,
        "tier": "light",
        "notes": "Fast sub-agents: routing, tagging, cleaning, and bulk steps (LIGHT_MODEL).",
    },
    {
        "id": DEFAULT_EMBEDDING_MODEL,
        "tier": "embedding",
        "notes": "Embedding model for pgvector / retrieval (configure separately if not on Featherless).",
    },
]


def pull_commands() -> list[str]:
    return ["No local pull required (Featherless remote models)."]
