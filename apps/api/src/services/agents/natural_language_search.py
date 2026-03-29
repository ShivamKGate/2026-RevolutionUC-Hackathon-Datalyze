"""Natural Language Search Agent — strict, light+pgvector."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "natural_language_search"
AGENT_NAME = "Natural Language Search Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 600

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="retrieval-augmented search and citation only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You provide grounded answers to natural language queries using the "
        "embedded data corpus.\n\n"
        "Retrieve relevant chunks via vector similarity, synthesize a concise "
        "answer, and cite source chunks. Optionally produce chart specifications "
        "when the query asks for visual data.\n\n"
        "Output schema:\n"
        "{\n"
        '  "answer": "Concise grounded answer...",\n'
        '  "sources": [{"chunk_id": "...", "relevance": 0.0-1.0, "excerpt": "..."}]\n'
        "}\n\n"
        "Never fabricate information. If the corpus lacks relevant data, "
        'return: {"answer": "Insufficient data to answer this query.", "sources": []}'
    ),
)

OUTPUT_SCHEMA = {
    "required": ["answer", "sources"],
    "optional": ["chart_spec", "follow_up_suggestions"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Provide grounded, citation-backed answers to natural language queries.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Answer the user's query using embedded corpus data. "
            "Cite relevant sources and flag insufficient data. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: answer, sources',
        agent=agent,
        context=context_tasks or [],
    )
