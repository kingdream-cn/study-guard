"""Heads-up display overlay for video frames."""

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from metrics import FrameMetrics

BOX_COLOR = (0, 255, 0)  # BGR green
TEXT_COLOR = (0, 255, 0)  # BGR green
WARN_COLOR = (0, 0, 255)  # BGR red
BASELINE_COLOR = (0, 255, 255)  # BGR yellow

# CJK font candidate paths, probed in order. The first existing file is used
# for Chinese text rendering.
CJK_FONT_CANDIDATES: tuple[str, ...] = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttf",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
)

# Pillow font size (px) used for Chinese overlay text.
FONT_SIZE = 18

# Internal value -> Chinese display text. Rendering-layer only: CSV/JSON/logs
# keep English values (see PROJECT_RULES and INTERFACE_SPEC §3).
_ZH_LABELS = {
    "FPS": "帧率",
    "Faces": "人脸",
    "Distance": "距离",
    "Posture": "坐姿",
    "Light": "亮度",
    "unknown": "未知",
    "too_close": "太近",
    "too_far": "太远",
    "normal": "正常",
}

_WARNING_PREFIX = "WARNING: "
_WARNING_PREFIX_ZH = "警告："

# Fixed reminder messages -> Chinese (rendering layer only). The source strings
# come verbatim from reminder.py and must stay English there.
_WARNING_MESSAGES_ZH = {
    "Eye care: look 20 ft away for 20 s": "用眼提醒：向远处看 20 秒",
    "Stand up and move around": "起身活动一下",
    "Adjust viewing distance": "请调整用眼距离",
    "Adjust your posture": "请调整坐姿",
}

# Dynamic "WARNING: <label>[, <label>...]" labels -> Chinese.
_WARNING_LABELS_ZH = {
    "face_lost": "人脸丢失",
    "distance": "距离异常",
    "posture": "坐姿不良",
}

_BASELINE_HINTS_ZH = {
    "baseline ready": "基线就绪",
    "Sit upright, press b to set posture baseline": "坐直，按 b 设置坐姿基线",
}
_BASELINE_PREFIX = "Baseline: "
_BASELINE_PREFIX_ZH = "基线："


def find_cjk_font(
    candidates: tuple[str, ...] = CJK_FONT_CANDIDATES,
) -> Optional[Path]:
    """Return the first existing CJK font path, or None if none is found.

    Args:
        candidates: Ordered font file paths to probe.

    Returns:
        Path to an existing font file, or None.
    """
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return path
    return None


def _bgr_to_rgb(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """Convert a BGR color tuple to the RGB order expected by Pillow."""
    return (color[2], color[1], color[0])


class HUDOverlay:
    """Draw heads-up display overlay on video frames."""

    def __init__(self, language: str = "en") -> None:
        """Initialize the overlay.

        Args:
            language: Display language, either ``"en"`` or ``"zh"``
                (default ``"en"``). ``"zh"`` renders via Pillow with a system
                CJK font; if no CJK font is found it falls back to the English
                cv2 rendering path.
        """
        self.language = language
        self._font: Optional[ImageFont.FreeTypeFont] = None
        if language == "zh":
            font_path = find_cjk_font()
            if font_path is not None:
                try:
                    self._font = ImageFont.truetype(str(font_path), FONT_SIZE)
                except OSError:
                    self._font = None

    def draw(
        self,
        frame: np.ndarray,
        metrics: FrameMetrics,
        fps: float,
        face_count: int = 0,
        warning: Optional[str] = None,
        baseline_hint: Optional[str] = None,
    ) -> np.ndarray:
        """Draw overlay on a copy of the frame.

        M4 scope: FPS, face count, face box, distance, posture, brightness,
        an active reminder/warning banner (INTERFACE_SPEC §1.9 banner), and the
        posture-baseline prompt/status.

        Args:
            frame: BGR image to draw on.
            metrics: Computed frame metrics.
            fps: Current processing FPS.
            face_count: Number of faces detected in this frame.
            warning: Active warning text, or None.
            baseline_hint: Posture-baseline prompt/status, or None.

        Returns:
            New image with overlay drawn. Original frame is not modified.
        """
        out = frame.copy()

        if metrics.face_box is not None:
            f = metrics.face_box
            cv2.rectangle(out, (f.x, f.y), (f.x + f.w, f.y + f.h), BOX_COLOR, 2)

        if self.language == "zh" and self._font is not None:
            self._draw_pil(out, metrics, fps, face_count, warning, baseline_hint)
        else:
            self._draw_cv2(out, metrics, fps, face_count, warning, baseline_hint)

        return out

    # -- English rendering (unchanged from v0.1.0) ---------------------------

    def _draw_cv2(
        self,
        out: np.ndarray,
        metrics: FrameMetrics,
        fps: float,
        face_count: int,
        warning: Optional[str],
        baseline_hint: Optional[str],
    ) -> None:
        cv2.putText(
            out, f"FPS: {fps:.1f}", (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )
        cv2.putText(
            out, f"Faces: {face_count}", (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )

        if metrics.distance_cm is not None:
            dist_text = (
                f"Distance: {metrics.distance_cm:.1f} cm "
                f"[{metrics.distance_category.value}]"
            )
        else:
            dist_text = "Distance: -- cm [unknown]"
        cv2.putText(
            out, dist_text, (10, 75),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )

        cv2.putText(
            out, f"Posture: {metrics.posture_score:.2f}", (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )
        cv2.putText(
            out, f"Light: Lv.{metrics.brightness_level}", (10, 125),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )

        if baseline_hint:
            cv2.putText(
                out, baseline_hint, (10, out.shape[0] - 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, BASELINE_COLOR, 2,
            )

        if warning:
            cv2.putText(
                out, warning, (10, out.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, WARN_COLOR, 2,
            )

    # -- Chinese rendering (Pillow + CJK font) ------------------------------

    def _draw_pil(
        self,
        out: np.ndarray,
        metrics: FrameMetrics,
        fps: float,
        face_count: int,
        warning: Optional[str],
        baseline_hint: Optional[str],
    ) -> None:
        lines: list[tuple[str, int, tuple[int, int, int]]] = []
        lines.append((f"{_ZH_LABELS['FPS']}: {fps:.1f}", 25, TEXT_COLOR))
        lines.append((f"{_ZH_LABELS['Faces']}: {face_count}", 50, TEXT_COLOR))

        if metrics.distance_cm is not None:
            category = _ZH_LABELS.get(
                metrics.distance_category.value, metrics.distance_category.value
            )
            dist_text = (
                f"{_ZH_LABELS['Distance']}: {metrics.distance_cm:.1f} cm [{category}]"
            )
        else:
            dist_text = f"{_ZH_LABELS['Distance']}: -- cm [{_ZH_LABELS['unknown']}]"
        lines.append((dist_text, 75, TEXT_COLOR))

        lines.append(
            (f"{_ZH_LABELS['Posture']}: {metrics.posture_score:.2f}", 100, TEXT_COLOR)
        )
        lines.append(
            (f"{_ZH_LABELS['Light']}: Lv.{metrics.brightness_level}", 125, TEXT_COLOR)
        )

        if baseline_hint:
            lines.append(
                (self._zh_baseline_hint(baseline_hint), out.shape[0] - 45, BASELINE_COLOR)
            )
        if warning:
            lines.append(
                (self._zh_warning(warning), out.shape[0] - 20, WARN_COLOR)
            )

        rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        draw = ImageDraw.Draw(pil)
        for text, y, color in lines:
            draw.text((10, y), text, font=self._font, fill=_bgr_to_rgb(color))
        out[...] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _zh_warning(text: str) -> str:
        """Translate a warning banner to Chinese (rendering layer only).

        Priority: (a) exact whole-message match, (b) ``"WARNING: "`` prefix with
        per-label translation joined by ``、``, (c) pass through unchanged.
        """
        translated = _WARNING_MESSAGES_ZH.get(text)
        if translated is not None:
            return translated
        if text.startswith(_WARNING_PREFIX):
            labels = text[len(_WARNING_PREFIX):].split(", ")
            translated_labels = [
                _WARNING_LABELS_ZH.get(label, label) for label in labels
            ]
            return _WARNING_PREFIX_ZH + "、".join(translated_labels)
        return text

    @staticmethod
    def _zh_baseline_hint(text: str) -> str:
        """Translate a known baseline hint, or its dynamic ``Baseline: `` prefix."""
        translated = _BASELINE_HINTS_ZH.get(text)
        if translated is not None:
            return translated
        if text.startswith(_BASELINE_PREFIX):
            return _BASELINE_PREFIX_ZH + text[len(_BASELINE_PREFIX):]
        return text
