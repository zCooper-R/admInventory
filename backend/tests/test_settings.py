"""
Tests for SystemSettings model, view, cache behaviour, and budget cache.

Covers
------
* ``SystemSettings.get()`` creates a default singleton on first call.
* Cache is populated after the first ``.get()`` call.
* Saving ``SystemSettings`` invalidates the cache.
* Settings page requires admin/superuser access.
* Settings page accepts a valid POST and saves changes.
* Budget report cache is populated and invalidated by Device signals.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
import pytest
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from apps.inventory.models import ReplacementStatus, SystemSettings
from apps.inventory.services.budget import (
    _BUDGET_CACHE_KEY,
    get_cached_budget_report,
    invalidate_budget_cache,
)
from .factories import AdminUserFactory, DeviceFactory, UserFactory


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure a clean cache state for every test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def admin_client(db):
    user = AdminUserFactory()
    c = Client()
    c.force_login(user)
    return c


@pytest.fixture
def regular_client(db):
    user = UserFactory()
    c = Client()
    c.force_login(user)
    return c


# ── SystemSettings model ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSystemSettingsModel:
    def test_get_creates_singleton(self):
        assert SystemSettings.objects.count() == 0
        obj = SystemSettings.get()
        assert obj.pk == 1
        assert SystemSettings.objects.count() == 1

    def test_get_returns_same_instance(self):
        a = SystemSettings.get()
        b = SystemSettings.get()
        assert a.pk == b.pk

    def test_cache_populated_after_get(self):
        SystemSettings.get()
        cached = cache.get(SystemSettings._CACHE_KEY)
        assert cached is not None

    def test_save_invalidates_cache(self):
        obj = SystemSettings.get()
        assert cache.get(SystemSettings._CACHE_KEY) is not None

        obj.pc_min_ram_gb = 16
        obj.save()
        assert cache.get(SystemSettings._CACHE_KEY) is None

    def test_default_values_are_reasonable(self):
        obj = SystemSettings.get()
        assert obj.pc_min_ram_gb > 0
        assert obj.pc_max_age_years > 0
        assert obj.pc_price_default > 0


# ── Settings view ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSystemSettingsView:
    def test_requires_login(self):
        url = reverse("system-settings")
        response = Client().get(url)
        assert response.status_code == 302

    def test_regular_user_redirected(self, regular_client):
        url = reverse("system-settings")
        response = regular_client.get(url)
        assert response.status_code == 302

    def test_admin_can_access(self, admin_client):
        url = reverse("system-settings")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_form_present_in_response(self, admin_client):
        url = reverse("system-settings")
        response = admin_client.get(url)
        assert b"form" in response.content.lower()

    def test_post_saves_settings(self, admin_client):
        SystemSettings.get()  # ensure singleton exists
        url = reverse("system-settings")
        settings_obj = SystemSettings.get()
        response = admin_client.post(url, {
            "system_title":     "Test Title",
            "system_subtitle":  "Test Subtitle",
            "pc_min_ram_gb":    8,
            "pc_max_age_years": 5,
            "pc_price_default": 75000,
            "replacement_ram_low_threshold_gb": settings_obj.replacement_ram_low_threshold_gb,
            "replacement_ram_mid_threshold_gb": settings_obj.replacement_ram_mid_threshold_gb,
            "replacement_ram_high_threshold_gb": settings_obj.replacement_ram_high_threshold_gb,
            "replacement_ram_low_score": settings_obj.replacement_ram_low_score,
            "replacement_ram_mid_score": settings_obj.replacement_ram_mid_score,
            "replacement_ram_high_score": settings_obj.replacement_ram_high_score,
            "replacement_ram_top_score": settings_obj.replacement_ram_top_score,
            "replacement_storage_hdd_score": settings_obj.replacement_storage_hdd_score,
            "replacement_storage_ssd_score": settings_obj.replacement_storage_ssd_score,
            "replacement_cpu_weak_score": settings_obj.replacement_cpu_weak_score,
            "replacement_cpu_medium_score": settings_obj.replacement_cpu_medium_score,
            "replacement_cpu_good_score": settings_obj.replacement_cpu_good_score,
            "replacement_cpu_excellent_score": settings_obj.replacement_cpu_excellent_score,
            "replacement_cpu_unknown_score": settings_obj.replacement_cpu_unknown_score,
            "replacement_attention_threshold": settings_obj.replacement_attention_threshold,
            "replacement_ok_threshold": settings_obj.replacement_ok_threshold,
        })
        assert response.status_code == 302

        updated = SystemSettings.objects.get(pk=1)
        assert updated.system_title    == "Test Title"
        assert updated.pc_min_ram_gb   == 8
        assert updated.pc_price_default == 75000

    def test_invalid_post_shows_form_again(self, admin_client):
        SystemSettings.get()
        url = reverse("system-settings")
        response = admin_client.post(url, {"pc_min_ram_gb": "not_a_number"})
        assert response.status_code == 200  # re-render with errors


# ── Budget cache ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBudgetCache:
    def test_get_cached_populates_cache(self):
        assert cache.get(_BUDGET_CACHE_KEY) is None
        get_cached_budget_report()
        assert cache.get(_BUDGET_CACHE_KEY) is not None

    def test_invalidate_clears_cache(self):
        get_cached_budget_report()
        invalidate_budget_cache()
        assert cache.get(_BUDGET_CACHE_KEY) is None

    def test_device_save_invalidates_cache(self):
        get_cached_budget_report()
        assert cache.get(_BUDGET_CACHE_KEY) is not None

        pc = DeviceFactory()
        pc.replacement_status = ReplacementStatus.REPLACE
        pc.save()

        assert cache.get(_BUDGET_CACHE_KEY) is None

    def test_device_delete_invalidates_cache(self):
        pc = DeviceFactory()
        get_cached_budget_report()
        assert cache.get(_BUDGET_CACHE_KEY) is not None

        pc.delete()
        assert cache.get(_BUDGET_CACHE_KEY) is None

    def test_cached_report_is_reused(self):
        """Two consecutive calls return data from the same cached computation."""
        report1 = get_cached_budget_report()
        report2 = get_cached_budget_report()
        assert report1.total_pcs == report2.total_pcs
        assert report1.price_per_pc == report2.price_per_pc
