#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


GUARDED_PATH_PATTERNS = (
    re.compile(r"(^|/)\.github(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)deploy(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)auth(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)billing(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)payments?(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)migrations?([/.]|$)", re.IGNORECASE),
    re.compile(r"(^|/)金流(/|$)", re.IGNORECASE),
)

RUNTIME_BRAKE_PATH_PATTERNS = (
    re.compile(r"^worker/src/killswitch(/|$)", re.IGNORECASE),
    re.compile(r"^worker/src/controller(/|$)", re.IGNORECASE),
    re.compile(r"^worker/src/dispatch(/|$)", re.IGNORECASE),
)

BUILD_TOOLING_PATH_PATTERNS = (
    re.compile(r"(^|/)package\.json$", re.IGNORECASE),
    re.compile(r"(^|/)package-lock\.json$", re.IGNORECASE),
    re.compile(r"(^|/)npm-shrinkwrap\.json$", re.IGNORECASE),
    re.compile(r"(^|/)pnpm-lock\.ya?ml$", re.IGNORECASE),
    re.compile(r"(^|/)pnpm-workspace\.ya?ml$", re.IGNORECASE),
    re.compile(r"(^|/)yarn\.lock$", re.IGNORECASE),
    re.compile(r"(^|/)bun\.lockb?$", re.IGNORECASE),
    re.compile(r"(^|/)\.npmrc$", re.IGNORECASE),
    re.compile(r"(^|/)[^/]*\.config\.(js|cjs|mjs|ts|cts|mts|json|ya?ml)$", re.IGNORECASE),
    re.compile(r"(^|/)tsconfig[^/]*\.json$", re.IGNORECASE),
    re.compile(r"(^|/)Dockerfile(?:\.[^/]*)?$", re.IGNORECASE),
    re.compile(r"(^|/)Makefile$", re.IGNORECASE),
    re.compile(r"\.toml$", re.IGNORECASE),
    re.compile(r"(^|/)action\.ya?ml$", re.IGNORECASE),
    re.compile(r"(^|/)scripts(/|$)", re.IGNORECASE),
)

SOURCE_PATH_PATTERNS = (
    re.compile(r"^worker/src(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)src(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)tests?(/|$)", re.IGNORECASE),
    re.compile(r"^worker/test(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)scripts(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)\.github(/|$)", re.IGNORECASE),
    re.compile(r"\.(?:ts|tsx|js|jsx|mjs|cjs|py|sh)$", re.IGNORECASE),
)

DOCS_PATH_PATTERNS = (
    re.compile(r"^docs/.+", re.IGNORECASE),
    re.compile(r"(^|/)[^/]+\.md$", re.IGNORECASE),
    re.compile(r"^README[^/]*$", re.IGNORECASE),
)

GUIDANCE_PATH_PATTERNS = (
    re.compile(r"(^|/)CLAUDE\.md$", re.IGNORECASE),
    re.compile(r"(^|/)AGENTS\.md$", re.IGNORECASE),
    re.compile(r"(^|/)CONTEXT\.md$", re.IGNORECASE),
    re.compile(r"(^|/)docs/adr(/|$)", re.IGNORECASE),
)

AGENT_PATH_ALLOWLIST = (
    re.compile(r"^src/.+"),
    re.compile(r"^tests/.+"),
    re.compile(r"^test/.+"),
    re.compile(r"^docs/.+"),
    re.compile(r"^worker/src/.+"),
    re.compile(r"^worker/test/.+"),
    re.compile(r"^[^/]+\.md$", re.IGNORECASE),
)

REVIEW_CONTROL_TOKEN = re.compile(
    r"verdict|pass|fail|🔴|🟡|🟢", re.IGNORECASE
)


def normalize_path(path: str) -> str:
    normalized = path.strip()
    if normalized.startswith('"'):
        return normalized
    normalized = normalized.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_allowlisted_agent_path(path: str) -> bool:
    return any(pattern.search(path) for pattern in AGENT_PATH_ALLOWLIST)


def is_guarded_path(path: str) -> bool:
    normalized = normalize_path(path)
    if not normalized:
        return False
    if normalized.startswith('"'):
        return True
    if any(pattern.search(normalized) for pattern in GUARDED_PATH_PATTERNS):
        return True
    if any(pattern.search(normalized) for pattern in RUNTIME_BRAKE_PATH_PATTERNS):
        return True
    if any(pattern.search(normalized) for pattern in BUILD_TOOLING_PATH_PATTERNS):
        return True
    if any(pattern.search(normalized) for pattern in GUIDANCE_PATH_PATTERNS):
        return True
    return not is_allowlisted_agent_path(normalized)


def diff_requires_guarded_scope(paths: list[str]) -> bool:
    return any(is_guarded_path(path) for path in paths)


def is_docs_only_change(paths: list[str]) -> bool:
    if not paths:
        return False
    for path in paths:
        normalized = normalize_path(path)
        if not normalized or normalized.startswith('"'):
            return False
        if any(pattern.search(normalized) for pattern in SOURCE_PATH_PATTERNS):
            return False
        if any(pattern.search(normalized) for pattern in BUILD_TOOLING_PATH_PATTERNS):
            return False
        if not any(pattern.search(normalized) for pattern in DOCS_PATH_PATTERNS):
            return False
    return True


# Deterministic coarse capability tripwire. This intentionally uses static
# regexes over added diff lines only; it is not a precise detector and has known
# blind spots. Logic-backdoor coverage belongs to the invariant suite, AI review,
# and the high-risk park flow. Prefer false positives here for obvious dangerous
# primitives and blast-radius signaling.
CAPABILITY_PATTERNS = (
    # 1. Outbound network: new sinks, explicit targets, raw IPs, and common clients.
    (
        "outbound_network",
        "high",
        (
            re.compile(r"\bfetch\s*\(", re.IGNORECASE),
            re.compile(r"https?://", re.IGNORECASE),
            re.compile(r"\bnew\s+WebSocket\b", re.IGNORECASE),
            re.compile(r"\bXMLHttpRequest\b", re.IGNORECASE),
            re.compile(r"\baxios(?:\.|\s*\()", re.IGNORECASE),
            re.compile(r"\brequire\s*\(\s*['\"]axios['\"]\s*\)", re.IGNORECASE),
            re.compile(r"\bfrom\s+['\"]axios['\"]", re.IGNORECASE),
            re.compile(r"\burllib(?:\.request)?\b", re.IGNORECASE),
            re.compile(r"\brequests\.(?:get|post|put|patch|delete|request)\b", re.IGNORECASE),
            re.compile(r"\bhttp\.client\b", re.IGNORECASE),
            re.compile(r"\bwebhook\b", re.IGNORECASE),
            re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
            re.compile(r"\b(?:net\.connect|dgram\.)\b", re.IGNORECASE),
        ),
    ),
    # 2. Secret access: env objects, env files, and obvious uppercase secret names.
    (
        "secret_access",
        "high",
        (
            re.compile(r"\bprocess\.env\b"),
            re.compile(r"\bos\.environ\b"),
            re.compile(r"\bimport\s+os\b.*\benviron\b"),
            re.compile(r"\b[A-Z_]*(?:TOKEN|SECRET|KEY|PASSWORD|CREDENTIAL)[A-Z_]*\b"),
            re.compile(r"\.dev\.vars\b"),
            re.compile(r"['\"](?:[^'\"]*/)?\.env['\"]"),
        ),
    ),
    # 3. Dynamic execution: eval/shell/process primitives and non-literal loaders.
    (
        "dynamic_exec",
        "high",
        (
            re.compile(r"\beval\s*\("),
            re.compile(r"\bnew\s+Function\b"),
            re.compile(r"\bexec(?:Sync)?\s*\("),
            re.compile(r"\bchild_process\b"),
            re.compile(r"\bspawn\s*\("),
            re.compile(r"\bos\.system\s*\("),
            re.compile(r"\bsubprocess\b"),
            re.compile(r"\bimport\s*\(\s*(?!['\"])"),
            re.compile(r"\brequire\s*\(\s*(?!['\"])"),
        ),
    ),
    # 4. Authz/billing logic: content-level signal complementing guarded paths.
    (
        "authz_billing_logic",
        "high",
        (
            re.compile(
                r"\b(?:auth|authn|authz|authoriz\w*|permission|permissions|role|roles|"
                r"isAdmin|billing|price|prices|charge|charges|charged|quota|quotas|"
                r"subscription|subscriptions|entitlement|entitlements)\b",
                re.IGNORECASE,
            ),
        ),
    ),
    # 5. new_dependency is deliberately not scanned here. package.json/lockfiles
    # are already guarded by BUILD_TOOLING_PATH_PATTERNS, and inline import/require
    # novelty detection without project context is too noisy for this coarse filter.
    # 6. Destructive operations: SQL deletion, filesystem deletion, broad revokes,
    # bulk deletes, and feature flag flips.
    (
        "destructive",
        "high",
        (
            re.compile(r"\bDROP\s+(?:TABLE|DATABASE)\b", re.IGNORECASE),
            re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
            re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
            re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
            re.compile(r"\bbulkDelete\b", re.IGNORECASE),
            re.compile(r"\bdeleteMany\b", re.IGNORECASE),
            re.compile(r"\brevoke\b", re.IGNORECASE),
            re.compile(r"\b\w*flag\w*\b[^=]{0,80}=\s*(?:false|true)\b", re.IGNORECASE),
        ),
    ),
    # 7. Evasion: weak token/signature compares, verification short-circuits,
    # time/count/header gates, encoding smuggling, and opaque blobs.
    (
        "evasion",
        "high",
        (
            re.compile(
                r"\b(?:token|signature|hmac|hash)\b.{0,80}(?:={2,3}|startsWith\s*\()|"
                r"(?:={2,3}|startsWith\s*\().{0,80}\b(?:token|signature|hmac|hash)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(?:verifySignature|constantTimeEqual)\b.{0,80}"
                r"(?:return\s+true|=>\s*true|=\s*true|\|\|\s*true|&&\s*false)",
                re.IGNORECASE,
            ),
            re.compile(
                r"\bverify\s*\([^)]*\)\s*(?:\|\|\s*true|&&\s*false)",
                re.IGNORECASE,
            ),
            re.compile(r"\bDate\.now\(\)\s*(?:<=|>=|<|>)"),
            re.compile(
                r"\bif\s*\([^)]*\b(?:date|count|header|headers)\b[^)]*(?:<=|>=|<|>|={2,3}|!=)",
                re.IGNORECASE,
            ),
            re.compile(r"\batob\s*\("),
            re.compile(r"\bBuffer\.from\s*\([^)]*base64", re.IGNORECASE),
            re.compile(r"\bfromCharCode\s*\("),
            re.compile(
                r"(?:\\x[0-9a-fA-F]{2}|0x[0-9a-fA-F]{2}).{0,120}"
                r"\b(?:fetch|https?|eval|exec|Function|import|require)\b"
            ),
            re.compile(r"['\"][A-Za-z0-9+/=]{201,}['\"]"),
            re.compile(r"['\"][0-9a-fA-F]{201,}['\"]"),
        ),
    ),
)

CAPABILITY_CARD_LINES = {
    "outbound_network": "🔴 對外連線：此改動新增/動到對外網路。Q：這功能需要連外網嗎？",
    "secret_access": "🔴 讀取 secret/env/credential。Q：這功能需要碰密鑰嗎？",
    "dynamic_exec": "🔴 動態執行（eval/exec/child_process）。Q：這功能需要動態執行程式嗎？",
    "authz_billing_logic": "🔴 授權/付費/quota 邏輯。Q：要讓 agent 改授權或付費邏輯嗎？",
    "destructive": "🔴 破壞性操作（刪表/刪檔/回收權限/flag 翻轉）。Q：這功能該做破壞性操作嗎？",
    "evasion": "🔴 規避手法（弱比對/驗章短路/time-bomb/編碼偷渡）。Q：正常修法不該出現這些，確認嗎？",
}

CAPABILITY_CARD_ORDER = tuple(CAPABILITY_CARD_LINES)


def analyze_capabilities(added_lines: list[str]) -> list[dict]:
    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for line in added_lines:
        evidence = line.strip()
        for category, tier, patterns in CAPABILITY_PATTERNS:
            if not any(pattern.search(line) for pattern in patterns):
                continue
            key = (category, evidence)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "category": category,
                    "tier": tier,
                    "evidence": evidence,
                }
            )
    return findings


def capability_card(findings: list[dict]) -> str:
    categories = {str(finding.get("category") or "") for finding in findings}
    lines = [
        "🔴 高風險改動偵測（用商業常識判斷，非看 code）",
        "",
    ]
    for category in CAPABILITY_CARD_ORDER:
        if category in categories:
            lines.append(CAPABILITY_CARD_LINES[category])
    lines.extend(
        [
            "",
            "請只回答：這張 PR 的功能是否需要上述能力？若不是明確需要，請先停下要求人工審查。",
            "此卡片只使用 detector 類別訊號，不使用 raw diff 文字作為敘事來源。",
        ]
    )
    return "\n".join(lines)


def capability_tier(added_lines: list[str]) -> str:
    if any(finding["tier"] == "high" for finding in analyze_capabilities(added_lines)):
        return "high"
    return "normal"


def added_lines_from_unified_diff(diff_text: str) -> list[str]:
    added_lines: list[str] = []
    for line in diff_text.splitlines():
        if not line.startswith("+"):
            continue
        if line.startswith("+++ ") or line.startswith("+++\t"):
            continue
        added_lines.append(line[1:])
    return added_lines


def changed_paths_from_name_status(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")) and len(parts) >= 3:
            paths.extend([parts[1], parts[2]])
        elif len(parts) >= 2:
            paths.append(parts[1])
    return [normalize_path(path) for path in paths if normalize_path(path)]


def changed_paths_from_api_file_rows(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        for path in parts:
            normalized = normalize_path(path)
            if normalized:
                paths.append(normalized)
    return paths


def symlink_paths_from_raw(text: str) -> list[str]:
    symlinks: list[str] = []
    for line in text.splitlines():
        if not line.startswith(":") or "\t" not in line:
            continue
        meta, path_text = line.split("\t", 1)
        fields = meta.split()
        if len(fields) < 5:
            continue
        old_mode, new_mode = fields[0].lstrip(":"), fields[1]
        if old_mode != "120000" and new_mode != "120000":
            continue
        parts = path_text.split("\t")
        symlinks.extend(parts)
    return [normalize_path(path) for path in symlinks if normalize_path(path)]


def git_blob_text(rev: str, path: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "cat-file", "-p", f"{rev}:{path}"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def check_scope(
    name_status_text: str,
    raw_text: str,
    *,
    git_rev: Optional[str] = None,
) -> tuple[bool, str]:
    paths = changed_paths_from_name_status(name_status_text)
    if not paths:
        return False, "empty_diff_failclosed"

    for path in paths:
        if is_guarded_path(path):
            return False, f"guarded_path:{path}"

    symlink_paths = symlink_paths_from_raw(raw_text)
    if symlink_paths:
        if git_rev:
            for path in symlink_paths:
                target = git_blob_text(git_rev, path)
                if is_guarded_path(target):
                    return False, f"symlink_guarded_target:{path}->{target}"
        return False, f"symlink_change:{symlink_paths[0]}"

    return True, "ok"


def compare_local_and_api_paths(name_status_text: str, api_rows_text: str) -> tuple[bool, str]:
    local = set(changed_paths_from_name_status(name_status_text))
    api = set(changed_paths_from_api_file_rows(api_rows_text))
    if not local or not api:
        return False, "empty_diff_failclosed"
    if local != api:
        return False, "diff_mismatch_failclosed"
    return True, "ok"


def strip_review_control_tokens(text: str) -> str:
    return REVIEW_CONTROL_TOKEN.sub("[stripped]", text)


def parse_review_verdict(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return "fail"
    if payload == {"verdict": "pass"}:
        return "pass"
    return "fail"


def kill_status_allows_merge(text: str) -> bool:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False
    return payload.get("killed") is False


def protection_allows_automerge(text: str) -> tuple[bool, str]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return False, "required_status_checks_unparseable"
    contexts = payload.get("contexts") or []
    if "automerge-gate" not in contexts:
        return False, "automerge_gate_not_required"
    if "diff-review-verdict" not in contexts:
        return False, "diff_review_verdict_not_required"
    if payload.get("strict") is not True:
        return False, "branch_protection_strict_required"
    return True, "ok"


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def emit_result(ok: bool, reason: str) -> int:
    print(reason)
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_scope_parser = subparsers.add_parser("check-scope")
    check_scope_parser.add_argument("--name-status", required=True)
    check_scope_parser.add_argument("--raw", required=True)
    check_scope_parser.add_argument("--git-rev")

    compare_parser = subparsers.add_parser("compare-files")
    compare_parser.add_argument("--name-status", required=True)
    compare_parser.add_argument("--api-files", required=True)

    docs_only_parser = subparsers.add_parser("docs-only-check")
    docs_only_parser.add_argument("--name-status", required=True)

    sanitize_parser = subparsers.add_parser("sanitize-diff")
    sanitize_parser.add_argument("path")

    verdict_parser = subparsers.add_parser("review-verdict")
    verdict_parser.add_argument("path")

    kill_parser = subparsers.add_parser("kill-status")
    kill_parser.add_argument("path")

    protection_parser = subparsers.add_parser("protection")
    protection_parser.add_argument("path")

    capability_parser = subparsers.add_parser("capability-scan")
    capability_parser.add_argument("path")

    args = parser.parse_args()

    if args.command == "check-scope":
        ok, reason = check_scope(
            read(args.name_status),
            read(args.raw),
            git_rev=args.git_rev,
        )
        return emit_result(ok, reason)

    if args.command == "compare-files":
        ok, reason = compare_local_and_api_paths(read(args.name_status), read(args.api_files))
        return emit_result(ok, reason)

    if args.command == "docs-only-check":
        ok = is_docs_only_change(changed_paths_from_name_status(read(args.name_status)))
        return emit_result(ok, "docs_only" if ok else "source_touching")

    if args.command == "sanitize-diff":
        sys.stdout.write(strip_review_control_tokens(read(args.path)))
        return 0

    if args.command == "review-verdict":
        verdict = parse_review_verdict(read(args.path))
        print(verdict)
        return 0 if verdict == "pass" else 1

    if args.command == "kill-status":
        return emit_result(kill_status_allows_merge(read(args.path)), "kill_status")

    if args.command == "protection":
        ok, reason = protection_allows_automerge(read(args.path))
        return emit_result(ok, reason)

    if args.command == "capability-scan":
        try:
            added = added_lines_from_unified_diff(read(args.path))
        except OSError:
            print("capability_scan_failed:read_error")
            return 1
        if not added:
            print("ok")
            return 0
        findings = analyze_capabilities(added)
        if findings:
            print(capability_card(findings))
            return 1
        print("ok")
        return 0

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
