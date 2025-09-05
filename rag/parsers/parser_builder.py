# parsers/parser_builder.py
from __future__ import annotations
from typing import Dict, Any, Callable, Optional

class OutputParserImpl:
    def __init__(self, parseFn: Callable[[str], Dict[str, Any]]):
        self._parseFn = parseFn

    def parse(self, text: str) -> Dict[str, Any]:
        return self._parseFn(text)

class ParserBuilder:
    def __init__(self):
        self._fmt = "markdown-qa"
        self._schema: Optional[Dict[str, Any]] = None

    def setFormat(self, fmt: str) -> "ParserBuilder":
        self._fmt = fmt
        return self

    def withJsonSchema(self, schema: Dict[str, Any]) -> "ParserBuilder":
        self._schema = schema
        return self

    def build(self) -> OutputParserImpl:
        if self._fmt == "json":
            return OutputParserImpl(self._json)
        if self._fmt == "yaml":
            return OutputParserImpl(self._yaml)
        return OutputParserImpl(self._mdqa)

    def _json(self, s: str) -> Dict[str, Any]:
        import json
        try:
            obj = json.loads(_sliceObj(s, "{", "}"))
            if self._schema is not None:
                _validate(obj, self._schema)
            return obj
        except Exception:
            return {"answer": s.strip(), "warning": "json-parse-fallback"}

    def _yaml(self, s: str) -> Dict[str, Any]:
        try:
            import yaml
            obj = yaml.safe_load(s)
            if isinstance(obj, dict):
                return obj
            return {"answer": str(obj)}
        except Exception:
            return {"answer": s.strip(), "warning": "yaml-parse-fallback"}

    def _mdqa(self, s: str) -> Dict[str, Any]:
        lines = [ln.strip() for ln in s.splitlines() if len(ln.strip()) > 0]
        q = ""
        a = []
        for ln in lines:
            if ln.lower().startswith("q:"):
                q = ln[2:].strip()
            else:
                a.append(ln)
        return {"question": q, "answer": "\n".join(a) if len(a) > 0 else s.strip()}

def _sliceObj(s: str, l: str, r: str) -> str:
    i = s.find(l)
    j = s.rfind(r)
    return s[i:j+1] if (i != -1 and j != -1 and j >= i) else s

def _validate(obj: Dict[str, Any], schema: Dict[str, Any]) -> None:
    if schema.get("type") == "object":
        miss = [k for k in schema.get("required", []) if k not in obj]
        if len(miss) > 0:
            raise ValueError(f"Missing keys: {miss}")
