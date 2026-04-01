"""
Custom Django template tags and filters for the Inventory app.

Available tags / filters
------------------------
``rubles``              — format integer as Russian rubles string.
``abs_value``           — absolute value filter.
``query_url``           — merge current GET params with extra kwargs.
``sort_url``            — produce a sort URL toggling ASC/DESC.
``sort_icon``           — Bootstrap icon class for sort indicator.
``critical_pc_count``   — number of PCs with replacement_status=replace.

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""

from django import template

register = template.Library()


# ── Filters ────────────────────────────────────────────────────────────────────


@register.filter
def rubles(value):
    """Format integer as Russian rubles: 1 234 567 ₽"""
    try:
        return f"{int(value):,}".replace(",", "\u202f") + "\u00a0₽"
    except (TypeError, ValueError):
        return "—"


@register.filter
def abs_value(value):
    """Return the absolute (non-negative) integer value, or the original value on error."""
    try:
        return abs(int(value))
    except (TypeError, ValueError):
        return value


# ── URL helpers ────────────────────────────────────────────────────────────────


@register.simple_tag(takes_context=True)
def query_url(context, **kwargs):
    """
    Build a URL query string by merging current GET params with provided kwargs.
    Pass value=None to remove a param.

    Usage:
        {% query_url page=2 %}
        {% query_url sort='name' dir='asc' page=None %}
    """
    request = context.get("request")
    params = request.GET.copy() if request else {}

    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = str(value)

    qs = params.urlencode()
    return f"?{qs}" if qs else "?"


@register.simple_tag(takes_context=True)
def sort_url(context, field):
    """
    Generate a sort URL toggling direction for the given field.

    Usage: <a hx-get="{% sort_url 'name' %}">Name</a>
    """
    request = context.get("request")
    if not request:
        return f"?sort={field}&dir=asc"

    current_sort = request.GET.get("sort", "inventory_number")
    current_dir = request.GET.get("dir", "asc")

    new_dir = "desc" if (current_sort == field and current_dir == "asc") else "asc"

    params = request.GET.copy()
    params["sort"] = field
    params["dir"] = new_dir
    params.pop("page", None)
    return f"?{params.urlencode()}"


@register.simple_tag(takes_context=True)
def sort_icon(context, field):
    """Return Bootstrap Icon class for sort direction indicator."""
    request = context.get("request")
    if not request:
        return ""
    current_sort = request.GET.get("sort", "inventory_number")
    current_dir = request.GET.get("dir", "asc")

    if current_sort != field:
        return ""
    return "bi-caret-up-fill" if current_dir == "asc" else "bi-caret-down-fill"


# ── Dashboard / Topbar helpers ─────────────────────────────────────────────────


@register.simple_tag
def critical_pc_count():
    """
    Number of PCs that require replacement.
    Used in the topbar to alert managers.
    """
    try:
        from apps.inventory.models import Device, DeviceType, ReplacementStatus

        return Device.objects.filter(
            device_type=DeviceType.PC,
            replacement_status=ReplacementStatus.REPLACE,
        ).count()
    except Exception:
        return 0
