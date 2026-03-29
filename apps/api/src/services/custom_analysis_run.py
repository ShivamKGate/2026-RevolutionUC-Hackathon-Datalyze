"""
Datalyze Chat — custom analysis kickoff (isolated from orchestrator core).

Maps a chosen pipeline base (predictive, automation, optimization, supply_chain) to the
same `onboarding_path` strings the standard `resolve_track()` path already understands,
so the orchestrator runs the normal track profile with no CUSTOM track or profile_for_run().
"""

from __future__ import annotations

# Canonical track id -> onboarding_path key understood by track_profiles.resolve_track
_ONBOARDING_FOR_BASE: dict[str, str] = {
    "predictive": "Deep Analysis",
    "automation": "DevOps/Automations",
    "optimization": "Business Automations",
    "supply_chain": "supply chain",
}


def onboarding_path_for_custom_base(base: str) -> str:
    """Return onboarding_path for resolve_track() from a canonical track id."""
    b = (base or "").strip().lower().replace("-", "_")
    if b not in _ONBOARDING_FOR_BASE:
        b = "predictive"
    return _ONBOARDING_FOR_BASE[b]
