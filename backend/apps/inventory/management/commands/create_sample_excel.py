"""
Management command: create_sample_excel

Generates ``fixtures/sample_import.xlsx`` for Excel import testing.
Delegates to :func:`build_import_template_bytes` — the single source of
truth shared with the ``pc_import_template`` view.

Usage::

    python manage.py create_sample_excel
    python manage.py create_sample_excel --output /tmp/my_test.xlsx

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""

from pathlib import Path

from apps.inventory.services.template_excel import (
    SAMPLE_ROWS,
    build_import_template_bytes,
)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Generate fixtures/sample_import.xlsx for import testing."""

    help = "Generate fixtures/sample_import.xlsx for import testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="",
            help="Destination path. Defaults to <backend>/fixtures/sample_import.xlsx.",
        )

    def handle(self, *args, **options):
        output = options.get("output", "").strip()
        if output:
            dest = Path(output)
        else:
            commands_dir = Path(__file__).resolve().parent  # .../commands/
            backend_dir = commands_dir.parents[3]  # backend/
            dest = backend_dir / "fixtures" / "sample_import.xlsx"

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(build_import_template_bytes())

        self.stdout.write(self.style.SUCCESS(f"Sample Excel created: {dest}"))
        self.stdout.write(
            "  Rows: " + ", ".join(r["inventory_number"] for r in SAMPLE_ROWS)
        )
