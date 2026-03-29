"""Image/Multimodal Processor Agent — strict, Gemini vision."""

from __future__ import annotations

from crewai import Agent, LLM, Task

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "image_multimodal_processor"
AGENT_NAME = "Image/Multimodal Processor Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 800

SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="image/chart text and label extraction only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You extract information from images, chart screenshots, and whiteboard photos.\n\n"
        "Recover text, labels, data values, and chart interpretations from visual inputs. "
        "Assess extraction confidence and flag items needing manual review.\n\n"
        "Output schema:\n"
        "{\n"
        '  "extracted_text": "...",\n'
        '  "labels": ["label1", "label2"],\n'
        '  "interpretation": "concise description of visual content",\n'
        '  "confidence": 0.0-1.0,\n'
        '  "manual_review_flag": true|false\n'
        "}\n\n"
        "Set manual_review_flag=true when confidence < 0.6."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["extracted_text", "labels", "interpretation"],
    "optional": ["confidence", "manual_review_flag"],
}


def build_agent(llm: LLM) -> Agent:
    return Agent(
        role=AGENT_NAME,
        goal="Extract text, labels, and interpretations from visual inputs.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Agent, context_tasks: list[Task] | None = None) -> Task:
    return Task(
        description=(
            "Analyze the provided image and extract all text, labels, and "
            "data interpretations. Flag low-confidence items for manual review. "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output='JSON object with keys: extracted_text, labels, interpretation',
        agent=agent,
        context=context_tasks or [],
    )
