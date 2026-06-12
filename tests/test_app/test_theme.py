"""Phase 1 (Red): the rewritten theme must expose AGC colour + font tokens.

The AXON redesign drives all chrome from named tokens (no hard-coded hex in
widgets), so these are the contract the widgets build on.
"""

from __future__ import annotations

import re

import pytest

from visionpower.app import theme

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def test_agc_palette_exposes_exact_brand_colours():
    # AGC corporate palette, locked by the approved design.
    assert theme.PRIMARY.upper() == "#0C4DA2"   # deep brand blue
    assert theme.ACCENT.upper() == "#2F80D8"    # interactive highlight
    assert theme.RED.upper() == "#D23A55"       # alert / close
    assert theme.SUCCESS.upper() == "#34D399"   # done / ok


def test_core_surface_and_text_tokens_are_valid_hex():
    for name in ("BG", "BG_PANEL", "BG_CANVAS", "TEXT", "TEXT_DIM", "BORDER"):
        value = getattr(theme, name)
        assert _HEX.match(value), f"{name}={value!r} is not #RRGGBB"


def test_font_family_constants_are_nonempty_strings():
    for name in ("FONT_BRAND", "FONT_BODY", "FONT_MONO"):
        value = getattr(theme, name)
        assert isinstance(value, str) and value.strip()


def test_resolve_font_family_falls_back_when_missing(qapp):
    # An obviously-absent family must yield the provided fallback, never crash.
    resolved = theme.resolve_font_family("NoSuchFont-XYZ-123", "monospace")
    assert resolved == "monospace"


def test_build_stylesheet_returns_qss_referencing_accent(qapp):
    qss = theme.build_stylesheet()
    assert isinstance(qss, str) and qss.strip()
    assert theme.ACCENT in qss  # accent actually wired into the stylesheet


def test_apply_theme_is_callable_without_error(qapp):
    theme.apply_theme(qapp)  # must not raise
