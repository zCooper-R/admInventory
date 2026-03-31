from __future__ import annotations

from django.db import IntegrityError

from apps.inventory.models import Browser, Position
from apps.locations.models import Organization

from .normalizers import normalize_browser, normalize_org, normalize_position, normalize_text


class OrganizationResolver:
    @staticmethod
    def resolve_or_create(name: str, address: str = "") -> Organization:
        display_name = normalize_text(name)
        normalized = normalize_org(display_name)
        if not normalized:
            raise ValueError("Не заполнена организация")

        normalized_address = normalize_text(address)

        org = Organization.objects.filter(normalized_name=normalized).first()
        if org:
            updates: list[str] = []
            if display_name and org.name != display_name and len(display_name) > len(org.name):
                org.name = display_name
                updates.append("name")
            if normalized_address and org.address != normalized_address:
                org.address = normalized_address
                updates.append("address")
            if updates:
                org.save(update_fields=updates + ["normalized_name"])
            return org

        try:
            return Organization.objects.create(
                name=display_name or normalized,
                normalized_name=normalized,
                address=normalized_address,
            )
        except IntegrityError:
            org = Organization.objects.get(normalized_name=normalized)
            if normalized_address and not org.address:
                org.address = normalized_address
                org.save(update_fields=["address"])
            return org


class PositionResolver:
    @staticmethod
    def resolve_or_create(name: str) -> Position | None:
        display_name = normalize_text(name)
        normalized = normalize_position(display_name)
        if not normalized:
            return None

        position = Position.objects.filter(normalized_name=normalized).first()
        if position:
            return position

        try:
            return Position.objects.create(name=display_name, normalized_name=normalized)
        except IntegrityError:
            return Position.objects.get(normalized_name=normalized)


class BrowserResolver:
    @staticmethod
    def resolve_or_create(name: str) -> Browser | None:
        display_name = normalize_text(name)
        normalized = normalize_browser(display_name)
        if not normalized:
            return None

        browser = Browser.objects.filter(normalized_name=normalized).first()
        if browser:
            return browser

        try:
            return Browser.objects.create(name=display_name, normalized_name=normalized)
        except IntegrityError:
            return Browser.objects.get(normalized_name=normalized)
