"""Knowledge Graph Builder Agent — guarded, heavy_alt."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "knowledge_graph_builder"
AGENT_NAME = "Knowledge Graph Builder Agent"
STRICTNESS = "guarded"
TOKEN_BUDGET = 1200

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="entity relationship graph construction",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You build an entity relationship network from aggregated data.\n\n"
        "Extract named entities (companies, people, products, metrics, dates, locations) "
        "and identify relationships between them. Produce typed nodes and edges "
        "suitable for graph visualization.\n\n"
        "Output schema:\n"
        "{\n"
        '  "nodes": [{"id": "...", "label": "...", "type": "company|person|product|metric|date|location|concept"}],\n'
        '  "edges": [{"source": "node_id", "target": "node_id", "relationship": "...", "weight": 0.0-1.0}]\n'
        "}\n\n"
        "Ensure node IDs are deterministic and consistent. "
        "Use lowercase, underscore-separated IDs."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["nodes", "edges"],
    "optional": ["node_types", "edge_types", "clusters"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Build a typed entity relationship graph from aggregated data.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Extract entities and relationships from the aggregated corpus "
            "to build a knowledge graph with typed nodes and weighted edges. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: nodes, edges',
        agent=agent,
        context=context_tasks or [],
    )
