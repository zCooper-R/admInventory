from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ReplacementStatus = Literal["ok", "attention", "replace"]


@dataclass(slots=True)
class ReplacementAssessment:
    status: ReplacementStatus
    score: int
    reasons: list[str]


def assess_device_for_replacement(device) -> ReplacementAssessment:
    """Evaluate device health/profile suitability with explainable reasons."""
    reasons: list[str] = []
    score = 100

    ram = device.ram or 0
    if ram < 8:
        score -= 50
        reasons.append("ОЗУ меньше 8 ГБ")
    elif ram == 8:
        score -= 20
        reasons.append("ОЗУ на минимально допустимом уровне (8 ГБ)")
    elif ram < 16:
        score -= 10
        reasons.append("ОЗУ ниже рекомендованных 16 ГБ")

    if device.storage_type == "HDD":
        score -= 35
        reasons.append("Используется HDD")

    heavy_usage = any(
        [
            bool(device.use_for_images),
            bool(device.use_for_presentations),
            bool(device.use_for_audio),
            bool(device.use_for_video),
        ]
    )
    if heavy_usage and ram < 16:
        score -= 20
        reasons.append("Профиль использования требует 16+ ГБ ОЗУ")

    if heavy_usage and device.storage_type == "HDD":
        score -= 10
        reasons.append("Для профильных задач рекомендуется SSD")

    score = max(0, min(100, score))

    if ram < 8 or device.storage_type == "HDD" or score < 50:
        status: ReplacementStatus = "replace"
    elif ram == 8 or score < 75:
        status = "attention"
    else:
        status = "ok"

    return ReplacementAssessment(status=status, score=score, reasons=reasons)
