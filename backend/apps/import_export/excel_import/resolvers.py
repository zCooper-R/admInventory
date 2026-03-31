"""Reference data resolvers used by row processor."""
from __future__ import annotations

from apps.inventory.models import Browser, Position
from apps.locations.models import Organization
from apps.locations.normalization import normalize_organization_name


def resolve_organization(raw_name: str) -> Organization:
    normalized = normalize_organization_name(raw_name)
    organization = Organization.objects.filter(normalized_name=normalized).first()
    if organization:
        return organization
    return Organization.objects.create(name=raw_name.strip(), normalized_name=normalized)


def resolve_position(raw_name: str) -> Position | None:
    value = (raw_name or "").strip()
    if not value:
        return None
    position = Position.objects.filter(name__iexact=value).first()
    if position:
        return position
    return Position.objects.create(name=value)


def resolve_browser(raw_name: str) -> Browser | None:
    value = (raw_name or "").strip()
    if not value:
        return None
    browser = Browser.objects.filter(name__iexact=value).first()
    if browser:
        return browser
    return Browser.objects.create(name=value)
