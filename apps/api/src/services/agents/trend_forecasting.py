"""Trend Forecasting Agent — guarded, heavy_alt."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "trend_forecasting"
AGENT_NAME = "Trend Forecasting Agent"
STRICTNESS = "guarded"
TOKEN_BUDGET = 800

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="time-series trend analysis and forecasting",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You analyze time-series data from the aggregated corpus and produce "
        "KPI trajectory forecasts.\n\n"
        "Identify time-series candidates (revenue trends, growth rates, user counts, etc.), "
        "compute trend direction, and produce forecast values with confidence bands.\n\n"
        "Output schema:\n"
        "{\n"
        '  "forecasts": [{"metric": "...", "current_value": N, "forecast_value": N, '
        '"period": "...", "direction": "up|down|flat", "confidence": 0.0-1.0}],\n'
        '  "confidence_bands": [{"metric": "...", "lower": N, "upper": N, "period": "..."}]\n'
        "}\n\n"
        "Only forecast when sufficient historical data points exist. "
        "Flag insufficient data rather than speculating."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["forecasts", "confidence_bands"],
    "optional": ["plot_payloads", "methodology", "data_points_used"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Forecast KPI trajectories from time-series data.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Identify time-series candidates and produce forecasts with "
            "confidence bands. Flag insufficient data. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: forecasts, confidence_bands',
        agent=agent,
        context=context_tasks or [],
    )
