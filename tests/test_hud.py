"""Tests for the HUD overlay (hud.py)."""

import json
from pathlib import Path

import numpy as np
import pytest

import hud
from config import AppConfig, ConfigError
from hud import HUDOverlay
from metrics import DistanceCategory, FrameMetrics
from reminder import ReminderManager, select_banner

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _metrics(
    face: bool = True,
    category: DistanceCategory = DistanceCategory.NORMAL,
    distance: float = 45.0,
) -> FrameMetrics:
    return FrameMetrics(
        timestamp=0.0,
        distance_cm=distance if face else None,
        distance_category=category if face else DistanceCategory.UNKNOWN,
        posture_score=0.8 if face else 0.0,
        brightness_level=3,
        face_detected=face,
        face_box=None,
    )


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _frame() -> np.ndarray:
    return np.zeros((240, 320, 3), dtype=np.uint8)


def test_draw_zh_returns_same_shape_ndarray():
    overlay = HUDOverlay(language="zh")
    frame = _frame()
    out = overlay.draw(
        frame, _metrics(), 27.8, 1, "WARNING: distance", "baseline ready"
    )
    assert isinstance(out, np.ndarray)
    assert out.shape == frame.shape
    assert out.dtype == frame.dtype


def test_draw_zh_falls_back_to_english_without_font(monkeypatch):
    monkeypatch.setattr(hud, "find_cjk_font", lambda: None)
    zh = HUDOverlay(language="zh")
    en = HUDOverlay(language="en")

    frame = _frame()
    metrics = _metrics()
    out_zh = zh.draw(frame, metrics, 27.8, 1, "WARNING: distance", "baseline ready")
    out_en = en.draw(frame, metrics, 27.8, 1, "WARNING: distance", "baseline ready")

    # Without a CJK font, the "zh" overlay must fall back to the English path.
    np.testing.assert_array_equal(out_zh, out_en)


def test_language_defaults_to_en():
    assert HUDOverlay().language == "en"


def test_config_rejects_invalid_language(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"hud": {"language": "fr"}}), encoding="utf-8")
    with pytest.raises(ConfigError):
        AppConfig(path)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Eye care: look 20 ft away for 20 s", "用眼提醒：向远处看 20 秒"),
        ("Stand up and move around", "起身活动一下"),
        ("Adjust viewing distance", "请调整用眼距离"),
        ("Adjust your posture", "请调整坐姿"),
    ],
)
def test_warning_exact_message_translated(source, expected):
    assert HUDOverlay._zh_warning(source) == expected


def test_warning_dynamic_single_label():
    assert HUDOverlay._zh_warning("WARNING: face_lost") == "警告：人脸丢失"


def test_warning_dynamic_multiple_labels():
    assert HUDOverlay._zh_warning("WARNING: distance, posture") == "警告：距离异常、坐姿不良"


def test_warning_unknown_passes_through():
    assert HUDOverlay._zh_warning("Some unknown banner") == "Some unknown banner"


def test_warning_en_not_translated(monkeypatch):
    calls = []
    monkeypatch.setattr(
        HUDOverlay,
        "_zh_warning",
        staticmethod(lambda text: calls.append(text) or text),
    )
    HUDOverlay(language="en").draw(
        _frame(), _metrics(), 27.8, 1, "WARNING: distance", None
    )
    assert calls == []


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("WARNING: distance_too_close", "警告：距离过近"),
        ("WARNING: distance_too_far", "警告：距离过远"),
        ("WARNING: distance_too_close, posture", "警告：距离过近、坐姿不良"),
    ],
)
def test_warning_directional_labels_translated(source, expected):
    assert HUDOverlay._zh_warning(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Too close — move back", "距离过近，请后退"),
        ("Too far — move closer", "距离过远，请靠近"),
    ],
)
def test_warning_directional_messages_translated(source, expected):
    assert HUDOverlay._zh_warning(source) == expected


def test_distance_banner_message_then_chinese_label():
    """End-to-end banner policy: whole sentence, then directional label."""
    config = AppConfig(PROJECT_ROOT / "configs" / "default.json")
    clock = _Clock()
    manager = ReminderManager(config, clock=clock)
    threshold = config.get("reminder.distance_anomaly_threshold_sec")
    metrics = _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)

    manager.update(metrics)
    clock.t += threshold + 0.1
    held_events = manager.update(metrics)
    assert held_events
    banner = select_banner(
        clock.t, held_events, manager.active_warnings(), 3.0
    )
    assert banner == "Too close — move back"
    assert HUDOverlay._zh_warning(banner) == "距离过近，请后退"

    # main.py keeps the last event batch, so the sentence must survive the
    # following frames instead of being replaced after a single frame.
    clock.t += 1.5
    events = manager.update(metrics)
    assert events == []
    banner = select_banner(
        clock.t, held_events, manager.active_warnings(), 3.0
    )
    assert HUDOverlay._zh_warning(banner) == "距离过近，请后退"

    clock.t += 1.501
    events = manager.update(metrics)
    banner = select_banner(
        clock.t, held_events, manager.active_warnings(), 3.0
    )
    assert banner == "WARNING: distance_too_close"
    assert HUDOverlay._zh_warning(banner) == "警告：距离过近"


def test_zh_distance_category_labels_use_over_near_wording():
    """D4: [过近]/[过远] must match the O1-C banner wording."""
    assert hud._ZH_LABELS["too_close"] == "过近"
    assert hud._ZH_LABELS["too_far"] == "过远"
    assert DistanceCategory.TOO_CLOSE.value == "too_close"
    assert DistanceCategory.TOO_FAR.value == "too_far"
