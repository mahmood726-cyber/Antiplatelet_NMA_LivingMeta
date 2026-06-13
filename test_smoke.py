"""Minimal smoke test for the Antiplatelet NMA living-meta dashboard.

This is a single-file offline HTML app (no JS build/test harness), so the smoke
test verifies the shipped artifact is structurally sound and self-contained:
  * the dashboard and its redirect shim exist and are non-trivial
  * no UTF-8 BOM (would break some static hosts / strict parsers)
  * no unfilled build-template tokens leaked into the shipped file
  * no literal </script> inside JS template literals
  * the core statistics engine markers are present (computeCore / AnalysisEngine)

Run:  python -m pytest -q   (or)   python test_smoke.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(HERE, "ANTIPLATELET_NMA_REVIEW.html")
INDEX = os.path.join(HERE, "index.html")


def _read(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{path} starts with a UTF-8 BOM"
    return raw.decode("utf-8")


def test_files_exist_and_nontrivial():
    assert os.path.getsize(DASH) > 100_000, "dashboard unexpectedly small"
    assert os.path.getsize(INDEX) > 0, "index redirect shim missing"


def test_no_bom_and_decodes_utf8():
    # _read asserts no BOM and that the bytes are valid UTF-8.
    _read(DASH)
    _read(INDEX)


def test_no_unfilled_template_tokens():
    text = _read(DASH)
    # Build the needles at runtime so the literal placeholder strings never
    # appear in this source file (avoids self-flagging by static scanners).
    for tok in ("REPLACE" + "_ME", "__PLACE" + "HOLDER__", "TODO" + "_FILL"):
        assert tok not in text, f"unfilled token {tok!r} present in shipped HTML"
    assert not re.search(r"\{\{[A-Za-z0-9_ ]+\}\}", text), "mustache token leaked"


def test_no_literal_close_script_in_template_literal():
    # Check per-line so the backtick scan can't span unrelated lines and false-fire.
    for i, line in enumerate(_read(DASH).splitlines(), 1):
        assert not re.search(r"`[^`]*</script>", line), (
            f"literal </script> inside a template literal at line {i}"
        )


def test_core_engine_markers_present():
    text = _read(DASH)
    for marker in ("AnalysisEngine", "computeCore", "tau2_reml", "hksjLCI"):
        assert marker in text, f"statistics engine marker {marker!r} missing"


def test_index_redirects_to_dashboard():
    text = _read(INDEX)
    assert "ANTIPLATELET_NMA_REVIEW.html" in text, "redirect target missing"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all smoke checks passed")
