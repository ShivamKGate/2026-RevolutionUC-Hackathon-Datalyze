"""File Type Classifier Agent — strict, light.

Provides deterministic `classify_file_types()` for extension + MIME routing.
The LLM agent is instructed to return the same shape for orchestrator consumption.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from services.agents.shared_prompts import build_system_prompt

AGENT_ID = "file_type_classifier"
AGENT_NAME = "File Type Classifier Agent"
STRICTNESS = "strict"
TOKEN_BUDGET = 400

# --- Deterministic routing (extension first, then MIME) ----------------------

_EXT_PROCESSORS: list[tuple[tuple[str, ...], str, str]] = [
    ((".pdf",), "pdf_processor", "pdf"),
    ((".csv", ".tsv"), "csv_processor", "csv"),
    (
        (".xlsx", ".xls", ".xlsm", ".xlsb", ".ods"),
        "excel_processor",
        "excel",
    ),
    ((".json", ".jsonl", ".ndjson"), "json_processor", "json"),
    (
        (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".bmp",
            ".tif",
            ".tiff",
            ".svg",
            ".heic",
        ),
        "image_multimodal_processor",
        "image",
    ),
    (
        (
            ".txt",
            ".md",
            ".markdown",
            ".log",
            ".rtf",
            ".html",
            ".htm",
            ".xml",
            ".yaml",
            ".yml",
        ),
        "plain_text_processor",
        "text",
    ),
]


def _processor_from_extension(suffix: str) -> tuple[str | None, str | None]:
    s = suffix.lower()
    for extensions, proc, kind in _EXT_PROCESSORS:
        if s in extensions:
            return proc, kind
    return None, None


def _processor_from_mime(mime: str) -> tuple[str | None, str | None]:
    m = (mime or "").strip().lower()
    if not m:
        return None, None
    if m == "application/pdf":
        return "pdf_processor", "pdf"
    if m in ("text/csv", "application/csv", "text/comma-separated-values"):
        return "csv_processor", "csv"
    if m in (
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel.sheet.macroenabled.12",
    ):
        return "excel_processor", "excel"
    if m in ("application/json", "application/x-ndjson", "application/jsonlines"):
        return "json_processor", "json"
    if m.startswith("image/"):
        return "image_multimodal_processor", "image"
    if m.startswith("text/") or m in ("application/xml",):
        return "plain_text_processor", "text"
    return None, None


def classify_file_types(source_files_meta: list[dict[str, Any]]) -> dict[str, Any]:
    """Map each uploaded file to exactly one processor using extension + MIME.

    Each item may include:
      - ``filename`` or ``name`` (required for routing keys)
      - ``mime_type`` or ``mime`` (optional)
      - ``size_bytes`` or ``size`` (optional; informational only)

    Returns a dict suitable for merging with LLM output:
      - ``file_routing_map``: filename -> processor id
      - ``metadata_tags``: counts, detected kinds, ordered ``processors_needed``
      - ``heuristic_fallbacks`` (optional): filenames where MIME/extension was ambiguous
    """
    file_routing_map: dict[str, str] = {}
    kinds: list[str] = []
    fallbacks: list[str] = []

    for raw in source_files_meta:
        filename = str(raw.get("filename") or raw.get("name") or "").strip()
        if not filename:
            continue
        mime = str(raw.get("mime_type") or raw.get("mime") or "").strip()

        path = Path(filename)
        ext = path.suffix.lower()
        guessed_mime, _ = mimetypes.guess_type(filename)
        if not mime and guessed_mime:
            mime = guessed_mime

        proc, kind = _processor_from_extension(ext)
        is_fallback = False
        if proc is None:
            proc, kind = _processor_from_mime(mime)
        if proc is None:
            proc, kind = _plain_text_fallback(ext, mime)
            is_fallback = True

        if kind:
            kinds.append(kind)
        file_routing_map[filename] = proc
        if is_fallback:
            fallbacks.append(filename)

    processors_needed = sorted(set(file_routing_map.values())) if file_routing_map else []

    metadata_tags: dict[str, Any] = {
        "total_files": len(file_routing_map),
        "types_detected": sorted(set(kinds)),
        "processors_needed": processors_needed,
    }

    out: dict[str, Any] = {
        "file_routing_map": file_routing_map,
        "metadata_tags": metadata_tags,
    }
    if fallbacks:
        out["heuristic_fallbacks"] = fallbacks
    return out


def _plain_text_fallback(ext: str, mime: str) -> tuple[str, str]:
    """Last-resort routing for unknown extension/MIME (e.g. octet-stream)."""
    if ext in (".bin", ".exe", ".dll", ".zip", ".gz", ".7z"):
        return "plain_text_processor", "unknown"
    if mime == "application/octet-stream":
        return "plain_text_processor", "unknown"
    return "plain_text_processor", "unknown"


SYSTEM_PROMPT = build_system_prompt(
    role=AGENT_NAME,
    agent_id=AGENT_ID,
    scope_boundary="file type detection and routing only",
    strictness=STRICTNESS,
    token_budget=TOKEN_BUDGET,
    core_instructions=(
        "You classify uploaded files and determine which processor agent "
        "should handle each file.\n\n"
        "Given a file manifest (filenames, MIME types, size hints), produce "
        "a routing map that assigns EACH file to exactly one processor.\n\n"
        "Supported processors: pdf_processor, csv_processor, excel_processor, "
        "json_processor, image_multimodal_processor, plain_text_processor.\n\n"
        "Routing rules (apply in order): (1) file extension, (2) MIME type, "
        "(3) if still ambiguous, use plain_text_processor and list the filename "
        "under heuristic_fallbacks.\n\n"
        "Output schema:\n"
        "{\n"
        '  "file_routing_map": {"report.pdf": "pdf_processor", "data.xlsx": "excel_processor"},\n'
        '  "metadata_tags": {\n'
        '    "total_files": N,\n'
        '    "types_detected": ["pdf", "excel", ...],\n'
        '    "processors_needed": ["excel_processor", "pdf_processor"]\n'
        "  },\n"
        '  "heuristic_fallbacks": ["optional_filename_only_if_guessed"]\n'
        "}\n\n"
        "file_routing_map keys MUST be the exact filenames from the manifest. "
        "metadata_tags.processors_needed MUST be the sorted unique processors "
        "referenced in file_routing_map. "
        "Return JSON only."
    ),
)

OUTPUT_SCHEMA = {
    "required": ["file_routing_map", "metadata_tags"],
    "optional": ["heuristic_fallbacks"],
}


def build_agent(llm: Any) -> Any:
    from crewai import Agent

    return Agent(
        role=AGENT_NAME,
        goal="Correctly classify files and route to appropriate processor agents.",
        backstory=SYSTEM_PROMPT,
        llm=llm,
        verbose=False,
    )


def build_task(agent: Any, context_tasks: list[Any] | None = None) -> Any:
    from crewai import Task

    return Task(
        description=(
            "Given the uploaded file manifest, classify each file by type and "
            "assign it to exactly one processor in file_routing_map. "
            "Fill metadata_tags (total_files, types_detected, processors_needed). "
            "Return ONLY a JSON object matching the required schema."
        ),
        expected_output="JSON object with keys: file_routing_map, metadata_tags",
        agent=agent,
        context=context_tasks or [],
    )
