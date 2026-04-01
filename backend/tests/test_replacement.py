import pytest
from apps.inventory.models import ReplacementStatus, SystemSettings
from apps.inventory.services.replacement import (
    CPUCategory,
    assess_device_for_replacement,
    classify_cpu,
)

from .factories import DeviceFactory


@pytest.mark.django_db
class TestReplacementRules:
    def test_replacement_depends_only_on_hardware(self):
        base = DeviceFactory(
            ram=16, storage_type="SSD", cpu_model="Intel Core i5-12400"
        )
        score_base = assess_device_for_replacement(base).score

        mutated = DeviceFactory(
            ram=16,
            storage_type="SSD",
            cpu_model="Intel Core i5-12400",
            is_certified=False,
            use_for_text=True,
            use_for_images=True,
            use_for_presentations=True,
            use_for_audio=True,
            use_for_video=True,
        )
        score_mutated = assess_device_for_replacement(mutated).score

        assert score_base == score_mutated

    def test_is_certified_does_not_affect_score(self):
        a = DeviceFactory(
            ram=8, storage_type="HDD", cpu_model="Intel Core i3-7100", is_certified=True
        )
        b = DeviceFactory(
            ram=8,
            storage_type="HDD",
            cpu_model="Intel Core i3-7100",
            is_certified=False,
        )
        assert (
            assess_device_for_replacement(a).score
            == assess_device_for_replacement(b).score
        )

    def test_use_flags_do_not_affect_score(self):
        a = DeviceFactory(
            ram=8,
            storage_type="HDD",
            cpu_model="Intel Core i3-7100",
            use_for_video=False,
        )
        b = DeviceFactory(
            ram=8,
            storage_type="HDD",
            cpu_model="Intel Core i3-7100",
            use_for_video=True,
        )
        assert (
            assess_device_for_replacement(a).score
            == assess_device_for_replacement(b).score
        )

    @pytest.mark.parametrize(
        "cpu,expected",
        [
            ("Intel Celeron N4020", CPUCategory.WEAK),
            ("Intel Core i3-7100", CPUCategory.MEDIUM),
            ("Intel Core i5-12400", CPUCategory.GOOD),
            ("Intel Core i7-12700", CPUCategory.EXCELLENT),
            ("AMD Ryzen 5 5600G", CPUCategory.GOOD),
        ],
    )
    def test_cpu_classification(self, cpu, expected):
        assert classify_cpu(cpu) == expected

    def test_unknown_cpu_is_handled(self):
        result = assess_device_for_replacement(
            DeviceFactory(ram=16, storage_type="SSD", cpu_model="My Custom CPU 123")
        )
        assert result.status in {
            ReplacementStatus.OK,
            ReplacementStatus.ATTENTION,
            ReplacementStatus.REPLACE,
        }
        assert result.score >= 0

    def test_thresholds_come_from_settings(self):
        cfg = SystemSettings.get()
        cfg.replacement_attention_threshold = 2
        cfg.replacement_ok_threshold = 3
        cfg.replacement_cpu_unknown_score = 0
        cfg.save()

        device = DeviceFactory(ram=8, storage_type="SSD", cpu_model="Unknown CPU")
        result = assess_device_for_replacement(device)
        assert result.status in {ReplacementStatus.ATTENTION, ReplacementStatus.OK}
