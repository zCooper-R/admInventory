from __future__ import annotations

import json
import random
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inventory.models import Device, DeviceType, StorageType
from apps.locations.models import Organization
from apps.locations.normalization import normalize_organization_name
from apps.users.models import User, UserRole

_FIXTURE_PATH = Path(__file__).resolve().parents[4] / "fixtures" / "demo_data.json"
_RNG = random.Random(2024)

_STORAGE_TYPE_MAP = {"HDD": StorageType.HDD, "SSD": StorageType.SSD, "Mixed": StorageType.HDD}


class Command(BaseCommand):
    help = "Populate the database with demo organizations and devices."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true")
        parser.add_argument("--yes", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        catalog = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        hw = catalog["hardware"]

        if options["clear"]:
            Device.objects.filter(inventory_number__startswith="DEMO-").delete()

        org_map: dict[str, Organization] = {}
        for org_def in catalog["organizations"]:
            normalized = normalize_organization_name(org_def["name"])
            org, _ = Organization.objects.get_or_create(normalized_name=normalized, defaults={"name": org_def["name"], "address": ""})
            org_map[org_def["name"]] = org

        for uname, email, _org_name, _loc_name in catalog["managers"]:
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={"email": email, "full_name": f"Менеджер {uname}", "role": UserRole.MANAGER},
            )
            if created:
                user.set_password("demo1234")
                user.save()

        counter = 1
        for org_name, _loc_name, count, era, _prefix in catalog["pc_plan"]:
            org = org_map[org_name]
            for _ in range(count):
                storage_type_str, storage_size = _RNG.choice(hw["storage"][era])
                Device.objects.get_or_create(
                    inventory_number=f"DEMO-{counter:03d}",
                    defaults={
                        "organization": org,
                        "device_type": DeviceType.PC,
                        "cpu_model": _RNG.choice(hw["cpu"][era]),
                        "ram": _RNG.choice(hw["ram"][era]),
                        "storage_type": _STORAGE_TYPE_MAP.get(storage_type_str, StorageType.HDD),
                        "storage_size": storage_size,
                        "os": _RNG.choice(hw["os"][era]),
                        "employee_name": f"Сотрудник {counter}",
                    },
                )
                counter += 1

        self.stdout.write(self.style.SUCCESS("Demo data created."))
