"""Phase 1 (Red): static data tables the shell/dock/canvas build from."""

from __future__ import annotations

from visionpower.app import constants


def test_dock_categories_are_twelve_icon_label_pairs():
    cats = constants.DOCK_CATEGORIES
    assert len(cats) == 12
    for icon, label in cats:
        assert isinstance(icon, str) and icon
        assert isinstance(label, str) and label
    # spot-check the design's first and last entries
    assert cats[0] == ("camera", "影像擷取")
    assert cats[-1] == ("branch", "條件分支")


def test_layout_dimensions_match_design():
    assert constants.TITLE_H == 46
    assert constants.TOOLBAR_H == 54
    assert constants.STATUS_H == 30
    assert constants.DOCK_W == 56
    assert constants.RIGHT_W == 542
