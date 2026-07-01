import os
from typing import Any


_sentry_sdk: Any | None = None


def init_sentry() -> None:
    global _sentry_sdk

    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        _sentry_sdk = None
        return

    import sentry_sdk

    _sentry_sdk = sentry_sdk
    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        release=os.environ.get("SENTRY_RELEASE"),
        traces_sample_rate=_sample_rate(),
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        before_send=scrub_event,
        before_send_transaction=scrub_event,
    )


def capture_exception(exc: BaseException) -> None:
    if _sentry_sdk is None:
        return
    _sentry_sdk.capture_exception(exc)


def scrub_event(event: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any] | None:
    request = event.get("request")
    if isinstance(request, dict):
        request.pop("data", None)
        request.pop("cookies", None)
        request.pop("query_string", None)
        headers = request.get("headers")
        if isinstance(headers, dict):
            for key in list(headers):
                if _is_sensitive_header(key):
                    headers.pop(key, None)
    _scrub_exception(event)
    event.pop("user", None)
    return event


def _sample_rate() -> float:
    raw = os.environ.get("SENTRY_TRACES_SAMPLE_RATE")
    if raw is None:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _is_sensitive_header(key: str) -> bool:
    lowered = key.lower()
    return any(
        marker in lowered
        for marker in ("authorization", "cookie", "signature", "api-key", "token", "engine-key")
    )


def _scrub_exception(event: dict[str, Any]) -> None:
    exception = event.get("exception")
    if not isinstance(exception, dict):
        return
    values = exception.get("values")
    if not isinstance(values, list):
        return
    for value in values:
        if not isinstance(value, dict):
            continue
        if "value" in value:
            value["value"] = "[redacted]"
        stacktrace = value.get("stacktrace")
        if not isinstance(stacktrace, dict):
            continue
        frames = stacktrace.get("frames")
        if not isinstance(frames, list):
            continue
        for frame in frames:
            if isinstance(frame, dict):
                frame.pop("vars", None)
