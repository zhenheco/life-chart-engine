"""Guard: the 18 translated READMEs must stay in sync with English on the
contract-bearing literals. Markers are language-independent code tokens so the
check works across scripts without parsing prose."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TRANSLATIONS = {
    "README.ar.md", "README.de.md", "README.es.md", "README.fr.md",
    "README.hi.md", "README.id.md", "README.it.md", "README.ja.md",
    "README.ko.md", "README.nl.md", "README.pl.md", "README.pt.md",
    "README.ru.md", "README.th.md", "README.tr.md", "README.vi.md",
    "README.zh-CN.md", "README.zh-TW.md",
}

# language-independent literals every translation (and English) must carry
HOROSCOPE_SHAPE = "{ decadal, yearly, age }"
EXAMPLE_FLAG = "`--example`"
NODE_FLOOR = "Node.js ≥ 18"
REQUIRED_FLAG_TOKENS = ("`--date`", "`--time`", "`--tz`", "`--lat`", "`--lon`", "`--gender`")
STALE_MARKERS = ("required=True", "{ decadal, yearly }です", "{ decadal, yearly }`")

# Live schema_version pin. JSON-field form distinguishes "current output is X"
# from legitimate residual 1.1 (package string v1.1.0, backtick history prose
# like `` `schema_version` `1.1` is an additive… ``).
CURRENT_SCHEMA_VERSION_JSON = '"schema_version": "1.2"'
STALE_CURRENT_SCHEMA_VERSION_JSON = '"schema_version": "1.1"'


def _translations():
    return {p.name for p in ROOT.glob("README.*.md")}


def _contract_docs():
    """AGENTS.md + DEPLOY-HETZNER.md + all 19 README*.md (English + 18 translations)."""
    return ["AGENTS.md", "DEPLOY-HETZNER.md", "README.md"] + sorted(EXPECTED_TRANSLATIONS)


def test_translation_set_is_exactly_the_expected_18_files():
    assert _translations() == EXPECTED_TRANSLATIONS


def test_every_translation_carries_the_pinned_contract_literals():
    problems = []
    for name in sorted(EXPECTED_TRANSLATIONS | {"README.md"}):
        text = (ROOT / name).read_text(encoding="utf-8")
        if HOROSCOPE_SHAPE not in text:
            problems.append(f"{name}: missing horoscope shape literal {HOROSCOPE_SHAPE!r}")
        if EXAMPLE_FLAG not in text:
            problems.append(f"{name}: missing {EXAMPLE_FLAG} flag documentation")
        if NODE_FLOOR not in text:
            problems.append(f"{name}: missing Node runtime floor literal {NODE_FLOOR!r}")
        for token in REQUIRED_FLAG_TOKENS:
            if token not in text:
                problems.append(f"{name}: missing required-flag token {token}")
    assert not problems, "\n" + "\n".join(problems)


def test_no_translation_still_describes_the_removed_silent_fallback():
    problems = []
    for name in sorted(EXPECTED_TRANSLATIONS):
        text = (ROOT / name).read_text(encoding="utf-8")
        for stale in STALE_MARKERS:
            if stale in text:
                problems.append(f"{name}: stale marker {stale!r} still present")
    assert not problems, "\n" + "\n".join(problems)


def test_contract_docs_declare_schema_version_1_2_not_1_1():
    """AGENTS.md + DEPLOY-HETZNER.md + every README must pin live schema_version to 1.2.

    Guards the 'docs synced to 1.2' AC: reverting a current-version marker from
    1.2 back to 1.1 (JSON-field form) must fail this suite. Residual 1.1 that is
    *not* a current-version claim — ``v1.1.0`` package string, backtick history
    prose — is allowed and does not match the JSON-field literals below.
    """
    problems = []
    for name in _contract_docs():
        text = (ROOT / name).read_text(encoding="utf-8")
        if CURRENT_SCHEMA_VERSION_JSON not in text:
            problems.append(
                f"{name}: missing current schema_version JSON literal "
                f"{CURRENT_SCHEMA_VERSION_JSON!r}"
            )
        if STALE_CURRENT_SCHEMA_VERSION_JSON in text:
            problems.append(
                f"{name}: residual current-version 1.1 literal "
                f"{STALE_CURRENT_SCHEMA_VERSION_JSON!r}"
            )
    assert not problems, "\n" + "\n".join(problems)
