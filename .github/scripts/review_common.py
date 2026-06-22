import json


def parse_review_verdict(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return "fail"
    if payload == {"verdict": "pass"}:
        return "pass"
    return "fail"


def escape_untrusted_markdown(value: str) -> str:
    escaped = []
    for line in value.splitlines():
        if line.startswith("#"):
            escaped.append("\\" + line)
        elif line.startswith("```"):
            escaped.append("\\`\\`\\`" + line[3:])
        else:
            escaped.append(line)
    return "\n".join(escaped)
