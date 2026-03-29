import os

from crewai import Agent, Crew, LLM, Process, Task

from core.config import settings


def _normalize_model(model: str) -> str:
    normalized = model.strip()
    # Route org/model slugs through OpenAI-compatible provider (Featherless).
    if "/" in normalized and not normalized.startswith(("openai/", "azure/", "gemini/")):
        return f"openai/{normalized}"
    return normalized


def _prime_crewai_env() -> None:
    """CrewAI reads OPENAI_* env vars internally for its LLM wire protocol. We
    point them to Featherless (OpenAI-compatible base URL + API key)."""
    os.environ.setdefault("OPENAI_BASE_URL", settings.llm_base_url)
    os.environ.setdefault("OPENAI_API_KEY", settings.llm_api_key or "DATALYZE_PLACEHOLDER_KEY")


def _build_llm(model_name: str) -> LLM:
    _prime_crewai_env()
    return LLM(
        model=_normalize_model(model_name),
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )


def build_mvp_crew(user_goal: str, company_context: str) -> tuple[Crew, list[Task], list[Agent]]:
    # Orchestrator: HEAVY_MODEL (Kimi). Synthesis chain: HEAVY_ALT_MODEL (DeepSeek). LIGHT_MODEL for future light-only steps.
    llm_orchestrator = _build_llm(settings.heavy_model)
    llm_heavy_alt = _build_llm(settings.heavy_alt_model)

    orchestrator = Agent(
        role="Orchestrator Agent",
        goal="Coordinate analysis order and ensure concise, actionable output.",
        backstory=(
            "You are the Data Allies MVP coordinator for Datalyze. "
            "You convert a business goal into an ordered, practical plan."
        ),
        llm=llm_orchestrator,
        verbose=False,
    )

    aggregator = Agent(
        role="Aggregator Agent",
        goal="Aggregate context into prioritized evidence and business signals.",
        backstory=(
            "You combine mixed business context into a short, structured set "
            "of high-signal findings and assumptions."
        ),
        llm=llm_heavy_alt,
        verbose=False,
    )

    insights = Agent(
        role="Insight Generation Agent",
        goal="Generate core insights with confidence statements.",
        backstory=(
            "You produce clear insight bullets that can be rendered in cards "
            "for an executive dashboard."
        ),
        llm=llm_heavy_alt,
        verbose=False,
    )

    summary = Agent(
        role="Executive Summary Agent",
        goal="Return a board-ready summary with immediate next actions.",
        backstory=(
            "You write concise executive summaries with practical "
            "recommendations and follow-up actions."
        ),
        llm=llm_heavy_alt,
        verbose=False,
    )

    plan_task = Task(
        description=(
            "Given user_goal='{user_goal}' and company_context='{company_context}', "
            "produce a concise 3-step analysis plan for this run."
        ),
        expected_output="Three numbered steps with one-line rationale each.",
        agent=orchestrator,
    )

    aggregate_task = Task(
        description=(
            "Aggregate available context and list the top 5 evidence signals "
            "that matter for business decisions."
        ),
        expected_output=(
            "Five bullets with signal, why it matters, and confidence "
            "(high/medium/low)."
        ),
        agent=aggregator,
        context=[plan_task],
    )

    insight_task = Task(
        description=(
            "Generate 3-5 insights with clear business impact based on "
            "the aggregated signals."
        ),
        expected_output=(
            "A JSON-like list of insight objects with fields: title, impact, confidence."
        ),
        agent=insights,
        context=[aggregate_task],
    )

    summary_task = Task(
        description=(
            "Write an executive summary that includes key findings and 2 immediate next steps."
        ),
        expected_output="One concise paragraph plus two action bullets.",
        agent=summary,
        context=[insight_task],
    )

    crew = Crew(
        agents=[orchestrator, aggregator, insights, summary],
        tasks=[plan_task, aggregate_task, insight_task, summary_task],
        process=Process.sequential,
        verbose=False,
    )
    return crew, [plan_task, aggregate_task, insight_task, summary_task], [
        orchestrator,
        aggregator,
        insights,
        summary,
    ]


def kickoff_mvp(user_goal: str, company_context: str) -> dict[str, object]:
    crew, tasks, agents = build_mvp_crew(user_goal=user_goal, company_context=company_context)
    result = crew.kickoff(
        inputs={
            "user_goal": user_goal,
            "company_context": company_context,
        }
    )

    output_text = getattr(result, "raw", None) or getattr(result, "output", None) or str(result)

    return {
        "agents_initialized": [agent.role for agent in agents],
        "tasks_initialized": len(tasks),
        "output": output_text,
    }


def initialize_only_mvp(user_goal: str, company_context: str) -> dict[str, object]:
    _, tasks, agents = build_mvp_crew(user_goal=user_goal, company_context=company_context)
    return {
        "agents_initialized": [agent.role for agent in agents],
        "tasks_initialized": len(tasks),
        "output": None,
    }
