"""
Phase 1.2 validation: file_type_classifier routing utility + contract + normalizer.

Run from repo root:
  cd apps/api && set PYTHONPATH=src (Windows) or export PYTHONPATH=src (Unix)
  python scripts/validate_file_type_classifier.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# apps/api/src
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from services.agents.contracts import get_contract
from services.agents.file_type_classifier import classify_file_types
from services.agents.normalizer import normalize_agent_output, validate_envelope


_ALLOWED_PROCESSORS = frozenset(
    {
        "pdf_processor",
        "csv_processor",
        "excel_processor",
        "json_processor",
        "image_multimodal_processor",
        "plain_text_processor",
    }
)


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    contract = get_contract("file_type_classifier")
    _assert(contract is not None, "contract missing")

    # Excel-only upload → single processor
    excel_only = classify_file_types(
        [
            {
                "filename": "data.xlsx",
                "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        ]
    )
    _assert(
        excel_only["file_routing_map"]["data.xlsx"] == "excel_processor",
        "excel-only should route to excel_processor",
    )
    _assert(excel_only["metadata_tags"]["processors_needed"] == ["excel_processor"], "processors_needed")

    # Mixed manifest (matches verify_all_agents nominal shape)
    mixed = classify_file_types(
        [
            {"filename": "report.pdf", "mime": "application/pdf", "size": 2048000},
            {"filename": "data.csv", "mime": "text/csv", "size": 15000},
            {"filename": "chart.png", "mime": "image/png", "size": 500000},
        ]
    )
    _assert(mixed["file_routing_map"]["report.pdf"] == "pdf_processor", "pdf")
    _assert(mixed["file_routing_map"]["data.csv"] == "csv_processor", "csv")
    _assert(mixed["file_routing_map"]["chart.png"] == "image_multimodal_processor", "png")
    _assert(
        mixed["metadata_tags"]["processors_needed"]
        == ["csv_processor", "image_multimodal_processor", "pdf_processor"],
        "sorted unique processors",
    )

    # Unknown extension + octet-stream → fallback + heuristic_fallbacks
    unknown = classify_file_types(
        [{"filename": "mystery.xyz", "mime": "application/octet-stream", "size": 100}]
    )
    _assert(
        unknown["file_routing_map"]["mystery.xyz"] == "plain_text_processor",
        "unknown fallback",
    )
    _assert("heuristic_fallbacks" in unknown, "should list heuristic_fallbacks")

    # Contract validation on synthetic output
    ok, errs = contract.validate_output(excel_only)
    _assert(ok, f"contract: {errs}")

    env = normalize_agent_output("file_type_classifier", excel_only)
    ev_ok, ev_errs = validate_envelope(env)
    _assert(ev_ok, f"envelope: {ev_errs}")
    _assert(any(a.get("kind") == "file_routing_map" for a in env["artifacts"]), "artifact routing")

    for payload in (excel_only, mixed, unknown):
        for proc in payload["file_routing_map"].values():
            _assert(proc in _ALLOWED_PROCESSORS, f"bad processor id: {proc}")

    print("validate_file_type_classifier: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
