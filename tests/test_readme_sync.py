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
REQUIRED_FLAG_TOKENS = ("`--date`", "`--time`", "`--tz`", "`--lat`", "`--lon`", "`--gender`")
STALE_MARKERS = ("required=True", "{ decadal, yearly }です", "{ decadal, yearly }`")


def _translations():
    return {p.name for p in ROOT.glob("README.*.md")}


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
