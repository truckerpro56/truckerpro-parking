"""Static checks against unsafe DOM patterns in templates.

Round-3 #F: ensure error toasts and dynamic <a href> values go through
escape helpers, not raw string concat into innerHTML.
"""
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _read(path):
    with open(os.path.join(REPO, path), 'r', encoding='utf-8') as f:
        return f.read()


def test_stop_detail_does_not_inject_data_error_into_innerHTML():
    src = _read('app/templates/stops/stop_detail.html')
    assert "innerHTML = '<span style=\"color:#ef4444\">' + (data.error" not in src
    # Replacement should go through showError — never into innerHTML
    assert 'showError(msg, data.error' in src


def test_stop_detail_defines_show_error_helper():
    src = _read('app/templates/stops/stop_detail.html')
    assert 'function showError(' in src
    # The helper must use textContent (not innerHTML) for the error string
    section = src.split('function showError(', 1)[1].split('}', 1)[0]
    assert 'textContent' in section or '.textContent' in section


def test_route_planner_uses_escUrl_for_href_attributes():
    src = _read('app/templates/stops/route_planner.html')
    # The fixed pattern is `escUrl(item.url)` and `escUrl(url)`
    assert 'escUrl(item.url)' in src
    assert 'escUrl(url)' in src
    # Old unsafe patterns must be gone
    assert "'<a href=\"' + url +" not in src
    assert "'<a href=\"' + item.url +" not in src


def test_escUrl_blocks_protocol_relative_and_javascript():
    """The escUrl helper must reject anything not starting with `/` AND
    must reject `//` (protocol-relative) and `/\\` (Windows path / backslash
    trick that some browsers treat as protocol-relative)."""
    src = _read('app/templates/stops/route_planner.html')
    # The helper exists
    assert 'function escUrl(' in src
    body = src.split('function escUrl(', 1)[1].split('\n    }', 1)[0]
    # Must check leading character
    assert "charAt(0) !== '/'" in body or "startsWith('/')" in body
    # Must reject `//`
    assert "'/'" in body and ("'\\\\'" in body or "/\\" in body or 'charAt(1)' in body)
    # Must have a `#` fallback for blocked URLs
    assert "return '#'" in body
