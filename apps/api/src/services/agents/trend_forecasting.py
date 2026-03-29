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
        "chart-ready KPI trajectory forecasts.\n\n"
        "Identify at least 3 KPI-worthy time-series candidates (revenue trends, "
        "growth rates, user counts, conversion rates, etc.) when data supports it. "
        "Compute trend direction and produce forecast values with confidence bands.\n\n"
        "Output schema:\n"
        "{\n"
        '  "forecasts": [\n'
        "    {\n"
        '      "metric": "string",\n'
        '      "historical": [{"date": "YYYY-MM", "value": N}],\n'
        '      "predicted": [{"date": "YYYY-MM", "value": N, "lower": N, "upper": N}],\n'
        '      "confidence": 0.0-1.0,\n'
        '      "trend_direction": "upward|downward|flat",\n'
        '      "seasonality_detected": true\n'
        "    }\n"
        "  ],\n"
        '  "drivers": [{"factor": "string", "impact_pct": N}],\n'
        '  "anomalies": [{"date": "YYYY-MM", "metric": "string", "expected": N, "actual": N, "root_cause": "string"}],\n'
        '  "chart_suggestions": ["time_series_confidence_band", "driver_bar_chart", "anomaly_timeline"]\n'
        "}\n\n"
        "Only forecast when sufficient historical data points exist. "
        "If data is limited, return partial results plus an explanatory anomaly "
        "or driver entry grounded in available evidence. "
        "Do not include prose outside the JSON object."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["forecasts", "drivers", "anomalies", "chart_suggestions"],
    "optional": ["methodology", "data_points_used"],
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
            "confidence bands, key forecast drivers, and anomalies with "
            "root-cause context. Include chart_suggestions. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: forecasts, drivers, anomalies, chart_suggestions",
        agent=agent,
        context=context_tasks or [],
    )
