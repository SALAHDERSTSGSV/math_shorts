from __future__ import annotations

import hashlib
import re
import unicodedata

from domain.artifacts import GeneratedContent


def normalize_text(value: str) -> str:
    value = unicodedata.normalize(
        "NFKC",
        value,
    )

    value = value.lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = re.sub(
        r"[.!?,:;]+$",
        "",
        value,
    )

    return value.strip()


def build_content_fingerprint(
    content: GeneratedContent,
) -> str:
    normalized_problem = normalize_text(
        content.problem
    )

    normalized_solution = normalize_text(
        " ".join(content.solution_steps)
    )

    canonical = (
        f"{normalized_problem}\n"
        f"{normalized_solution}"
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
