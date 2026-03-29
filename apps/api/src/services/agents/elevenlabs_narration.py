"""ElevenLabs Narration Agent — guarded, elevenlabs_api."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "elevenlabs_narration"
AGENT_NAME = "ElevenLabs Narration Agent"
STRICTNESS = "guarded"
TOKEN_BUDGET = 400

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="executive summary narration preparation",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You prepare executive summary text for audio narration via ElevenLabs TTS.\n\n"
        "Given an executive summary, produce narration-optimized text: "
        "adjust pacing with punctuation, expand abbreviations, add natural "
        "pauses, and ensure the text sounds professional when read aloud.\n\n"
        "Output schema:\n"
        "{\n"
        '  "narration_text": "Narration-optimized version of the summary...",\n'
        '  "status": "ready|needs_review"\n'
        "}\n\n"
        "Keep narration under 2500 characters for TTS API limits. "
        "Do not add content beyond what the executive summary contains."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["narration_text", "status"],
    "optional": ["audio_url", "duration_estimate"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Prepare executive summary text for audio narration.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Optimize the executive summary for audio narration. "
            "Adjust pacing, expand abbreviations, add natural pauses. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: narration_text, status',
        agent=agent,
        context=context_tasks or [],
    )
