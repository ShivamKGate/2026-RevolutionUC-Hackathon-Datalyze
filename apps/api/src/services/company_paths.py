from __future__ import annotations

import re
from pathlib import Path

from core.config import settings


def slugify_company_dir(name: str) -> str:
    if not name or not str(name).strip():
        return "unnamed_company"
    s = re.sub(r"[^\w\s-]", "", name.strip(), flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "_", s)
    return (s[:80] or "unnamed_company")


def company_data_private_dir(company_display_name: str) -> Path:
    root = settings.repo_root / "data" / "company" / slugify_company_dir(company_display_name) / "private"
    root.mkdir(parents=True, exist_ok=True)
    return root


def company_data_public_dir(company_display_name: str) -> Path:
    root = settings.repo_root / "data" / "company" / slugify_company_dir(company_display_name) / "public"
    root.mkdir(parents=True, exist_ok=True)
    return root


def relative_posix_path(full_path: Path) -> str:
    try:
        return full_path.relative_to(settings.repo_root).as_posix()
    except ValueError:
        return full_path.as_posix()
