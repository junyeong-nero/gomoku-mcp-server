from typing import Dict, Any


def to_openrouter_schema(tool) -> Dict[str, Any]:
    schema = to_openai_schema(tool)
    return {
        "type": schema.get("type", "function"),
        "function": {
            "name": schema.get("name"),
            "description": schema.get("description"),
            "parameters": schema.get("parameters"),
        },
    }


def to_openai_schema(tool) -> Dict[str, Any]:
    # 입력 스키마 추출
    raw_schema = (
        getattr(tool, "inputSchema", None)
        or getattr(tool, "input_schema", None)
        or getattr(tool, "parameters", None)
    )

    # 다양한 형태를 dict(JSON-Schema) 로 통일
    if raw_schema is None:
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }

    elif isinstance(raw_schema, dict):
        schema = raw_schema

    elif hasattr(raw_schema, "model_json_schema"):  # Pydantic v2 모델
        schema = raw_schema.model_json_schema()

    elif isinstance(raw_schema, list):  # list[dict]
        props, required = {}, []
        for p in raw_schema:
            props[p["name"]] = {
                "type": p["type"],
                "description": p.get("description", ""),
            }
            if p.get("required", True):
                required.append(p["name"])
        schema = {"type": "object", "properties": props}
        if required:
            schema["required"] = required

    else:  # 알 수 없는 형식
        schema = {"type": "object", "properties": {}, "additionalProperties": True}

    # 필수 키 보강
    schema.setdefault("type", "object")
    schema.setdefault("properties", {})
    if "required" not in schema:
        schema["required"] = list(
            schema["properties"].keys()
        )  # 모두 optional 로 두고 싶다면 []

    # OpenAI 툴 JSON 반환
    return {
        "type": "function",
        "name": tool.name,
        "description": getattr(tool, "description", ""),
        "parameters": schema,
    }
