"""
Management command: create_demo_data
=====================================================
Reads the catalog from ``fixtures/demo_data.json`` and creates:
  • 6 organisations  •  14 locations  •  56 PCs  •  3 manager accounts

Usage:
  python manage.py create_demo_data           # create, skip existing
  python manage.py create_demo_data --clear   # delete DEMO- devices first
  python manage.py create_demo_data --clear --yes   # skip confirmation

All demo inventory numbers are prefixed "DEMO-" for safe cleanup.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inventory.models import Device, DeviceStatus, DeviceType, StorageType
from apps.locations.models import Location, Organization
from apps.locations.normalization import normalize_organization_name
from apps.users.models import User, UserRole

# Path: backend/apps/inventory/management/commands/ → [4] = backend/
_FIXTURE_PATH = Path(__file__).resolve().parents[4] / "fixtures" / "demo_data.json"

# Seeded RNG for reproducible data across runs
_RNG = random.Random(2024)

_STATUS_MAP = {
    "active":    DeviceStatus.ACTIVE,
    "broken":    DeviceStatus.BROKEN,
    "write_off": DeviceStatus.WRITE_OFF,
}

_STORAGE_TYPE_MAP = {
    "HDD":   StorageType.HDD,
    "SSD":   StorageType.SSD,
}


def _rand_date(start_str: str, end_str: str) -> date:
    """Return a random date within [start, end]."""
    start = date.fromisoformat(start_str)
    end   = date.fromisoformat(end_str)
    return start + timedelta(days=_RNG.randint(0, (end - start).days))


def _make_pc(idx: int, location: Location, era: str, prefix: str, hw: dict) -> dict:
    """Build a Device field-dict for one PC using the hardware catalog *hw*."""
    storage_type_str, storage_size = _RNG.choice(hw["storage"][era])
    start, end = hw["purchase_date_range"][era]
    return {
        "inventory_number": f"DEMO-{idx:03d}",
        "name":             f"{prefix}-{idx:03d}",
        "device_type":      DeviceType.PC,
        "cpu":              _RNG.choice(hw["cpu"][era]),
        "ram":              _RNG.choice(hw["ram"][era]),
        "storage_type":     _STORAGE_TYPE_MAP.get(storage_type_str, StorageType.HDD),
        "storage_size":     storage_size,
        "os":               _RNG.choice(hw["os"][era]),
        "status":           _STATUS_MAP[_RNG.choice(hw["status_weights"][era])],
        "organization":     location.organization,
        "location":         location,
        "purchase_date":    _rand_date(start, end),
        "serial_number":    f"SN{_RNG.randint(1_000_000, 9_999_999)}",
    }


class Command(BaseCommand):
    """Create demo data: 6 organisations, 14 locations, 56 PCs."""

    help = "Populate the database with demo organisations, locations, and PCs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all DEMO- prefixed devices before creating new ones.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the confirmation prompt when --clear is used.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        catalog = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        hw      = catalog["hardware"]

        # ── Optional cleanup ───────────────────────────────────────────────────
        if options["clear"]:
            count = Device.objects.filter(inventory_number__startswith="DEMO-").count()
            if count and not options["yes"]:
                answer = input(f"Delete {count} DEMO- devices? [y/N] ").strip().lower()
                if answer != "y":
                    self.stdout.write("Aborted.")
                    return
            deleted, _ = Device.objects.filter(inventory_number__startswith="DEMO-").delete()
            self.stdout.write(self.style.WARNING(f"  Deleted {deleted} demo devices."))

        # ── Build org / location map ───────────────────────────────────────────
        loc_map: dict[tuple[str, str], Location] = {}
        for org_def in catalog["organizations"]:
            normalized_name = normalize_organization_name(org_def["name"])
            org, _ = Organization.objects.get_or_create(
                normalized_name=normalized_name,
                defaults={"name": org_def["name"]},
            )
            for loc_def in org_def["locations"]:
                loc, created = Location.objects.get_or_create(
                    name=loc_def["name"],
                    organization=org,
                    defaults={"address": loc_def["address"]},
                )
                loc_map[(org_def["name"], loc_def["name"])] = loc
                if created:
                    self.stdout.write(f"  + Location: {org_def['name']} / {loc_def['name']}")

        # ── Manager accounts ───────────────────────────────────────────────────
        managers = []
        for uname, email, org_name, loc_name in catalog["managers"]:
            loc = loc_map.get((org_name, loc_name))
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email":     email,
                    "full_name": f"Менеджер ({loc_name})",
                    "role":      UserRole.MANAGER,
                    "location":  loc,
                },
            )
            if created:
                user.set_password("demo1234")
                user.save()
                self.stdout.write(f"  + User: {uname} (password: demo1234)")
            managers.append(uname)

        # ── PCs ────────────────────────────────────────────────────────────────
        counter       = 1
        created_count = 0
        skipped_count = 0

        for org_name, loc_name, count, era, prefix in catalog["pc_plan"]:
            location = loc_map[(org_name, loc_name)]
            for _ in range(count):
                pc_data = _make_pc(counter, location, era, prefix, hw)
                inv     = pc_data.pop("inventory_number")
                _, was_created = Device.objects.get_or_create(
                    inventory_number=inv,
                    defaults=pc_data,
                )
                created_count += was_created
                skipped_count += not was_created
                counter += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! Created {created_count} PCs, skipped {skipped_count} (already exist)."
        ))
        self.stdout.write(f"  Organisations : {Organization.objects.count()}")
        self.stdout.write(f"  Locations     : {Location.objects.count()}")
        self.stdout.write(f"  Total PCs     : {Device.objects.filter(device_type=DeviceType.PC).count()}")
        self.stdout.write("")
        self.stdout.write("  Demo manager accounts (password: demo1234):")
        for uname in managers:
            self.stdout.write(f"    • {uname}")
