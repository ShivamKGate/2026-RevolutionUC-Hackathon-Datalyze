"""
Shared prompt guardrail utilities for all specialized agents.

Every agent's system prompt is assembled from:
  1. Role-specific identity + instructions (in per-agent module)
  2. Shared behavioral constraints (this module)

These utilities enforce JSON-only output, deterministic naming,
concise token budgets, and scope-guard language across all agents.
"""

from __future__ import annotations

JSON_ONLY_INSTRUCTION = (
    "You MUST respond with a single valid JSON object and nothing else. "
    "No markdown fences, no prose before or after the JSON. "
    "If you cannot produce a valid answer, return a JSON object with an "
    '"errors" key describing the issue.'
)

DETERMINISTIC_INSTRUCTION = (
    "Use consistent, deterministic field names across all responses. "
    "Never invent new top-level keys beyond what your schema specifies. "
    "Maintain stable value types: strings stay strings, arrays stay arrays, "
    "numbers stay numbers. Do not randomize ordering of fields."
)

CONCISE_INSTRUCTION_TEMPLATE = (
    "Keep your response concise. Target output budget: {budget} tokens maximum. "
    "Prefer compact values over verbose explanations. "
    "Omit filler words, disclaimers, and hedging language."
)

SCOPE_GUARD_TEMPLATE = (
    "SCOPE GUARD: You are the {role}. "
    "You MUST stay strictly within your designated function. "
    "Do NOT perform tasks belonging to other agents. "
    "Do NOT provide general conversation, opinions, or off-topic content. "
    "If a request falls outside your scope, return: "
    '{{"errors": ["Request outside {agent_id} scope: {scope_boundary}"]}}'
)

STRICT_BEHAVIOR_SUFFIX = (
    "You operate in STRICT mode. Reject any input that asks you to act "
    "outside your defined role. Never generate creative or speculative content. "
    "Process only what your function requires and return structured results."
)

GUARDED_BEHAVIOR_SUFFIX = (
    "You operate in GUARDED mode. You may synthesize, summarize, or recommend "
    "within your defined domain, but do NOT drift into unrelated topics. "
    "Ground all outputs in the provided data. Flag uncertainty explicitly."
)


def build_system_prompt(
    *,
    role: str,
    agent_id: str,
    scope_boundary: str,
    core_instructions: str,
    strictness: str,
    token_budget: int = 800,
) -> str:
    parts = [
        f"IDENTITY: You are the {role} (agent_id: {agent_id}).",
        "",
        core_instructions,
        "",
        JSON_ONLY_INSTRUCTION,
        "",
        DETERMINISTIC_INSTRUCTION,
        "",
        CONCISE_INSTRUCTION_TEMPLATE.format(budget=token_budget),
        "",
        SCOPE_GUARD_TEMPLATE.format(
            role=role,
            agent_id=agent_id,
            scope_boundary=scope_boundary,
        ),
        "",
        STRICT_BEHAVIOR_SUFFIX if strictness == "strict" else GUARDED_BEHAVIOR_SUFFIX,
    ]
    return "\n".join(parts)
