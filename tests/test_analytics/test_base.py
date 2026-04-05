from __future__ import annotations

from app.analytics.base import normalize_label


def test_normalize_label_handles_special_phase_values() -> None:
    assert normalize_label("NA") == "N/A"
    assert normalize_label("EARLY_PHASE1") == "Early Phase 1"
    assert normalize_label("PHASE1_PHASE2") == "Phase 1/Phase 2"
    assert normalize_label("PHASE1") == "Phase 1"
