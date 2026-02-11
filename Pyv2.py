from __future__ import annotations
from typing import Any, Dict
import copy

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

def _clean_json_schema(node: Any) -> Any:
    """Remove invalid/unsupported bits for Anthropic tool schemas."""
    if isinstance(node, dict):
        out: Dict[str, Any] = {}
        for k, v in node.items():
            if v is None:
                continue

            v2 = _clean_json_schema(v)

            # Drop empty combinators (Anthropic rejects anyOf: [])
            if k in ("anyOf", "oneOf", "allOf") and (not isinstance(v2, list) or len(v2) == 0):
                continue

            # Drop enum if it's null / empty / wrong type
            if k == "enum" and (not isinstance(v2, list) or len(v2) == 0):
                continue

            # Drop items if null/empty
            if k == "items" and (not isinstance(v2, dict) or len(v2) == 0):
                continue

            # Drop scalar properties:{} nonsense if empty
            if k == "properties" and isinstance(v2, dict) and len(v2) == 0:
                continue

            out[k] = v2
        return out

    if isinstance(node, list):
        return [_clean_json_schema(x) for x in node if x is not None]

    return node

def _anthropic_schema_from_pydantic(model_cls: Any) -> Dict[str, Any]:
    # Prefer v2 API when available
    if hasattr(model_cls, "model_json_schema"):
        raw = model_cls.model_json_schema()
    else:
        raw = model_cls.schema()

    raw = copy.deepcopy(raw)
    raw.setdefault("$schema", DRAFT_2020_12)
    return _clean_json_schema(raw)

def _patch_args_schema_for_anthropic(tool: Any) -> None:
    """Force tool.args_schema.schema() to return clean 2020-12 schema."""
    if not hasattr(tool, "args_schema") or tool.args_schema is None:
        return

    model_cls = tool.args_schema

    # Build once to ensure it works
    _ = _anthropic_schema_from_pydantic(model_cls)

    # Monkeypatch schema() and model_json_schema() to return cleaned dict
    if hasattr(model_cls, "schema"):
        model_cls.schema = classmethod(lambda cls, *a, **k: _anthropic_schema_from_pydantic(cls))
    if hasattr(model_cls, "model_json_schema"):
        model_cls.model_json_schema = classmethod(lambda cls, *a, **k: _anthropic_schema_from_pydantic(cls))

# Apply patch to all MCP tools you loaded
for t in self.tools:
    _patch_args_schema_for_anthropic(t)
