from __future__ import annotations

import ast
import importlib
import inspect
import json
import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, UnionType
from typing import Any, Callable, Union, get_args, get_origin

from utils.decorators import SKILL_METADATA_ATTR


class SkillManager:
    """Discover and export project skills declared with @skill."""

    _EXCLUDED_DIRS = {
        ".git",
        ".idea",
        ".pytest_cache",
        ".venv",
        "__pycache__",
    }

    def __init__(self, project_root: str | Path | None = None):
        if project_root is None:
            self.project_root = Path(__file__).resolve().parents[1]
        else:
            self.project_root = Path(project_root).resolve()

        self.logger = logging.getLogger(self.__class__.__name__)
        self.import_errors: list[dict[str, str]] = []

    def list_skills(self) -> list[dict[str, Any]]:
        """Return all discovered skills as structured Python dicts."""
        self.import_errors.clear()
        skills: list[dict[str, Any]] = []
        seen_paths: set[str] = set()

        for module_path in self._discover_candidate_modules():
            module = self._safe_import_module(module_path)
            if module is None:
                continue

            for item in self._extract_skills_from_module(module):
                callable_path = str(item["callable_path"])
                if callable_path in seen_paths:
                    continue
                seen_paths.add(callable_path)
                skills.append(item)

        skills.sort(key=lambda item: item["callable_path"])
        return skills

    def get_skills(self) -> list[dict[str, Any]]:
        """Alias of list_skills for external callers."""
        return self.list_skills()

    def to_json(self, *, indent: int = 2, ensure_ascii: bool = False) -> str:
        """Serialize discovered skills to JSON."""
        return json.dumps(
            self.list_skills(),
            indent=indent,
            ensure_ascii=ensure_ascii,
        )

    def _discover_candidate_modules(self) -> list[str]:
        modules: list[str] = []
        for file_path in sorted(self.project_root.rglob("*.py")):
            if self._should_skip_path(file_path):
                continue
            if not self._file_may_define_skill(file_path):
                continue
            modules.append(self._to_module_path(file_path))
        return modules

    def _should_skip_path(self, file_path: Path) -> bool:
        if any(part in self._EXCLUDED_DIRS for part in file_path.parts):
            return True
        return False

    def _file_may_define_skill(self, file_path: Path) -> bool:
        try:
            source = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = file_path.read_text(encoding="utf-8-sig")
        except OSError:
            return False

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return False

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if self._is_skill_decorator_node(decorator):
                        return True
        return False

    @staticmethod
    def _is_skill_decorator_node(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id == "skill"
        if isinstance(node, ast.Attribute):
            return node.attr == "skill"
        if isinstance(node, ast.Call):
            return SkillManager._is_skill_decorator_node(node.func)
        return False

    def _to_module_path(self, file_path: Path) -> str:
        relative = file_path.resolve().relative_to(self.project_root)
        return ".".join(relative.with_suffix("").parts)

    @contextmanager
    def _project_root_on_path(self):
        root = str(self.project_root)
        inserted = False
        if root not in sys.path:
            sys.path.insert(0, root)
            inserted = True
        try:
            yield
        finally:
            if inserted:
                try:
                    sys.path.remove(root)
                except ValueError:
                    pass

    def _safe_import_module(self, module_path: str) -> ModuleType | None:
        try:
            with self._project_root_on_path():
                return importlib.import_module(module_path)
        except Exception as exc:
            self.import_errors.append(
                {
                    "module": module_path,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            self.logger.warning("Failed to import module %s: %s", module_path, exc)
            return None

    def _extract_skills_from_module(self, module: ModuleType) -> list[dict[str, Any]]:
        skills: list[dict[str, Any]] = []

        for _, func in inspect.getmembers(module, inspect.isfunction):
            if func.__module__ != module.__name__:
                continue
            item = self._build_skill_item(
                func,
                module_name=module.__name__,
                owner_name=None,
            )
            if item is not None:
                skills.append(item)

        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue
            skills.extend(self._extract_skills_from_class(cls))

        return skills

    def _extract_skills_from_class(self, cls: type[Any]) -> list[dict[str, Any]]:
        skills: list[dict[str, Any]] = []
        for attr_name, attr_value in cls.__dict__.items():
            func = self._unwrap_callable(attr_value)
            if func is None or func.__module__ != cls.__module__:
                continue

            item = self._build_skill_item(
                func,
                module_name=cls.__module__,
                owner_name=cls.__qualname__,
                attr_name=attr_name,
            )
            if item is not None:
                skills.append(item)
        return skills

    @staticmethod
    def _unwrap_callable(value: Any) -> Callable[..., Any] | None:
        if isinstance(value, (staticmethod, classmethod)):
            return value.__func__
        if inspect.isfunction(value):
            return value
        return None

    def _build_skill_item(
        self,
        func: Callable[..., Any],
        *,
        module_name: str,
        owner_name: str | None,
        attr_name: str | None = None,
    ) -> dict[str, Any] | None:
        metadata = getattr(func, SKILL_METADATA_ATTR, None)
        if not isinstance(metadata, dict):
            return None

        name = str(metadata.get("name") or func.__name__).strip()
        description = str(
            metadata.get("description") or inspect.getdoc(func) or ""
        ).strip()
        explicit_schema = metadata.get("schema")
        parameters = (
            explicit_schema
            if isinstance(explicit_schema, dict)
            else self._build_parameters_schema(func)
        )

        qualname = func.__qualname__
        callable_path = f"{module_name}.{qualname}"
        if owner_name and attr_name:
            callable_path = f"{module_name}.{owner_name}.{attr_name}"

        return {
            "type": "function",
            "name": name,
            "description": description,
            "parameters": parameters,
            "module": module_name,
            "qualname": qualname,
            "callable_path": callable_path,
        }

    def _build_parameters_schema(self, func: Callable[..., Any]) -> dict[str, Any]:
        signature = inspect.signature(func)
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, parameter in signature.parameters.items():
            if param_name in {"self", "cls"}:
                continue

            if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                properties[param_name] = {"type": "array"}
                continue

            if parameter.kind is inspect.Parameter.VAR_KEYWORD:
                properties[param_name] = {"type": "object"}
                continue

            schema = self._annotation_to_schema(parameter.annotation)
            if parameter.default is inspect._empty:
                required.append(param_name)
            else:
                schema["default"] = parameter.default

            properties[param_name] = schema

        result: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            result["required"] = required
        return result

    def _annotation_to_schema(self, annotation: Any) -> dict[str, Any]:
        if annotation is inspect._empty:
            return {"type": "string"}

        origin = get_origin(annotation)
        if origin in {list, tuple, set}:
            return {"type": "array"}
        if origin is dict:
            return {"type": "object"}
        if origin in {UnionType, Union}:
            args = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(args) == 1:
                return self._annotation_to_schema(args[0])
            return {"type": "string"}

        if annotation is str:
            return {"type": "string"}
        if annotation is int:
            return {"type": "integer"}
        if annotation is float:
            return {"type": "number"}
        if annotation is bool:
            return {"type": "boolean"}
        if annotation is list:
            return {"type": "array"}
        if annotation is dict:
            return {"type": "object"}

        if isinstance(annotation, str):
            lowered = annotation.lower()
            if lowered == "str":
                return {"type": "string"}
            if lowered == "int":
                return {"type": "integer"}
            if lowered == "float":
                return {"type": "number"}
            if lowered == "bool":
                return {"type": "boolean"}
            if lowered.startswith("list"):
                return {"type": "array"}
            if lowered.startswith("dict"):
                return {"type": "object"}

        return {"type": "string"}


__all__ = ["SkillManager"]
