from pathlib import Path

from webapp import PAGE


def test_webapp_renders_chart_values_without_inner_html_sinks():
    payload = "<img src=x onerror=alert(1)>"

    assert "innerHTML" not in PAGE
    assert "textContent" in PAGE
    assert "replaceChildren" in PAGE
    assert payload not in PAGE
    assert "function el(tag, cls, text)" in PAGE
    assert "function addRow(table, cells, rowCls)" in PAGE


def test_deploy_docs_do_not_embed_engine_key_header_values():
    deploy_doc = Path("DEPLOY-HETZNER.md").read_text()
    forbidden_header = "X-Engine-Key" + ":"

    assert "ENGINE_AUTH_HEADER" in deploy_doc
    assert "-H \"$ENGINE_AUTH_HEADER\"" in deploy_doc
    assert "-H \"" + forbidden_header not in deploy_doc
    assert forbidden_header + " $ENGINE_API_KEY" not in deploy_doc
    assert forbidden_header + " " not in deploy_doc
    assert "ENGINE_API_KEY=replace-with-long-random-key" not in deploy_doc
