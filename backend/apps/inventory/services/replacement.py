from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal

from apps.inventory.models import ReplacementStatus, StorageType, SystemSettings

ReplacementStatusLiteral = Literal["ok", "attention", "replace"]
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ReplacementAssessment:
    status: ReplacementStatusLiteral
    score: int
    reasons: list[str]


class CPUCategory:
    WEAK = "weak"
    MEDIUM = "medium"
    GOOD = "good"
    EXCELLENT = "excellent"
    UNKNOWN = "unknown"


_WEAK_PATTERNS = [
    re.compile(r"\bceleron\b"),
    re.compile(r"\bpentium\b"),
    re.compile(r"\batom\b"),
    re.compile(r"\bamd\s+a\d"),
    re.compile(r"\bamd\s+e\d"),
]


def _normalize_cpu_model(cpu_model: str | None) -> str:
    return " ".join((cpu_model or "").strip().lower().split())


def _extract_intel_core(cpu: str) -> tuple[int, int | None] | None:
    """Return (series, generation?) for Intel Core iX strings."""
    series_match = re.search(r"\bcore\s*i([3579])\b", cpu)
    if not series_match:
        return None
    series = int(series_match.group(1))

    model_match = re.search(r"\bi[3579]-?(\d{4,5})\b", cpu)
    if not model_match:
        return series, None
    model_num = model_match.group(1)

    # Intel heuristic: 4 digits -> first digit generation, 5 digits -> first 2 digits.
    if len(model_num) == 5:
        generation = int(model_num[:2])
    else:
        generation = int(model_num[0])
    return series, generation


def _extract_ryzen(cpu: str) -> tuple[int, int | None] | None:
    """Return (series, generation?) for Ryzen strings."""
    series_match = re.search(r"\bryzen\s*([3579])\b", cpu)
    if not series_match:
        return None
    series = int(series_match.group(1))

    model_match = re.search(r"\bryzen\s*[3579]\s*(\d{4,5})\b", cpu)
    generation = int(model_match.group(1)[0]) if model_match else None
    return series, generation


def classify_cpu(cpu_model: str | None) -> str:
    normalized = _normalize_cpu_model(cpu_model)
    if not normalized:
        return CPUCategory.UNKNOWN

    for pattern in _WEAK_PATTERNS:
        if pattern.search(normalized):
            return CPUCategory.WEAK

    intel = _extract_intel_core(normalized)
    if intel:
        series, generation = intel
        if series == 3:
            return CPUCategory.MEDIUM
        if series == 5:
            if generation is not None and generation < 8:
                return CPUCategory.MEDIUM
            return CPUCategory.GOOD
        if series == 7:
            if generation is not None and generation >= 10:
                return CPUCategory.EXCELLENT
            return CPUCategory.GOOD
        if series == 9:
            return CPUCategory.EXCELLENT

    ryzen = _extract_ryzen(normalized)
    if ryzen:
        series, generation = ryzen
        if series == 3:
            return CPUCategory.MEDIUM
        if series == 5:
            return CPUCategory.GOOD
        if series == 7:
            if generation is not None and generation >= 7:
                return CPUCategory.EXCELLENT
            return CPUCategory.GOOD
        if series == 9:
            return CPUCategory.EXCELLENT

    return CPUCategory.UNKNOWN


def _ram_score(device, cfg: SystemSettings) -> tuple[int, str]:
    ram = device.ram
    if ram is None:
        return cfg.replacement_ram_low_score, "ОЗУ не указано"

    if ram < cfg.replacement_ram_low_threshold_gb:
        return (
            cfg.replacement_ram_low_score,
            f"ОЗУ {ram} ГБ: ниже {cfg.replacement_ram_low_threshold_gb} ГБ",
        )
    if ram < cfg.replacement_ram_mid_threshold_gb:
        return cfg.replacement_ram_mid_score, f"ОЗУ {ram} ГБ: базовый уровень"
    if ram < cfg.replacement_ram_high_threshold_gb:
        return cfg.replacement_ram_high_score, f"ОЗУ {ram} ГБ: хороший уровень"
    return cfg.replacement_ram_top_score, f"ОЗУ {ram} ГБ: высокий уровень"


def _storage_score(device, cfg: SystemSettings) -> tuple[int, str]:
    if device.storage_type == StorageType.SSD:
        return cfg.replacement_storage_ssd_score, "Накопитель SSD"
    if device.storage_type == StorageType.HDD:
        return cfg.replacement_storage_hdd_score, "Накопитель HDD"
    return 0, "Тип накопителя не определён"


def _cpu_score(device, cfg: SystemSettings) -> tuple[int, str]:
    category = classify_cpu(device.cpu_model)
    if category == CPUCategory.WEAK:
        return cfg.replacement_cpu_weak_score, "Процессор: слабый"
    if category == CPUCategory.MEDIUM:
        return cfg.replacement_cpu_medium_score, "Процессор: средний"
    if category == CPUCategory.GOOD:
        return cfg.replacement_cpu_good_score, "Процессор: хороший"
    if category == CPUCategory.EXCELLENT:
        return cfg.replacement_cpu_excellent_score, "Процессор: отличный"
    return cfg.replacement_cpu_unknown_score, "Процессор: нераспознанный"


def assess_device_for_replacement(device) -> ReplacementAssessment:
    """Replacement assessment based only on hardware: RAM + storage + CPU."""
    cfg = SystemSettings.get()
    logger.debug(
        "Пересчёт replacement: inventory=%s cfg(attention=%s, ok=%s)",
        getattr(device, "inventory_number", ""),
        cfg.replacement_attention_threshold,
        cfg.replacement_ok_threshold,
    )

    ram_score, ram_reason = _ram_score(device, cfg)
    storage_score, storage_reason = _storage_score(device, cfg)
    cpu_score, cpu_reason = _cpu_score(device, cfg)

    total_score = ram_score + storage_score + cpu_score

    if total_score >= cfg.replacement_ok_threshold:
        status: ReplacementStatusLiteral = ReplacementStatus.OK
    elif total_score >= cfg.replacement_attention_threshold:
        status = ReplacementStatus.ATTENTION
    else:
        status = ReplacementStatus.REPLACE

    reasons = [
        ram_reason,
        storage_reason,
        cpu_reason,
        f"Итоговый балл: {total_score}",
    ]
    if cpu_reason.endswith("нераспознанный"):
        logger.warning(
            "CPU не распознан: inventory=%s cpu_model=%s assigned_score=%s",
            getattr(device, "inventory_number", ""),
            getattr(device, "cpu_model", ""),
            cpu_score,
        )
    logger.info(
        "replacement рассчитан: inventory=%s status=%s score=%s reasons=%s",
        getattr(device, "inventory_number", ""),
        status,
        total_score,
        "; ".join(reasons),
    )

    return ReplacementAssessment(status=status, score=total_score, reasons=reasons)
