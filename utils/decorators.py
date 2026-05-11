from __future__ import annotations

from copy import deepcopy
from inspect import getdoc
from typing import Any, Callable


SKILL_METADATA_ATTR = "__skill_metadata__"


def _normalize_skill_metadata(
    func: Callable[..., Any],
    *,
    name: str | None = None,
    description: str | None = None,
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if schema is not None and not isinstance(schema, dict):
        raise TypeError("schema must be a dict or None")

    resolved_name = (name or func.__name__).strip()
    if not resolved_name:
        raise ValueError("skill name cannot be empty")

    resolved_description = (description or getdoc(func) or "").strip()

    return {
        "name": resolved_name,
        "description": resolved_description,
        "schema": deepcopy(schema),
    }


def skill(
    name: str | None = None,
    description: str | None = None,
    schema: dict[str, Any] | None = None,
):
    """Mark a function or method as an AI-discoverable skill."""

    def decorator(target: Any):
        if isinstance(target, staticmethod):
            setattr(
                target.__func__,
                SKILL_METADATA_ATTR,
                _normalize_skill_metadata(
                    target.__func__,
                    name=name,
                    description=description,
                    schema=schema,
                ),
            )
            return target

        if isinstance(target, classmethod):
            setattr(
                target.__func__,
                SKILL_METADATA_ATTR,
                _normalize_skill_metadata(
                    target.__func__,
                    name=name,
                    description=description,
                    schema=schema,
                ),
            )
            return target

        if not callable(target):
            raise TypeError("@skill can only decorate callable targets")

        setattr(
            target,
            SKILL_METADATA_ATTR,
            _normalize_skill_metadata(
                target,
                name=name,
                description=description,
                schema=schema,
            ),
        )
        return target

    return decorator


__all__ = ["SKILL_METADATA_ATTR", "skill"]
