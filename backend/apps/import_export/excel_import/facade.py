from __future__ import annotations

import logging
from dataclasses import dataclass, field

from apps.import_export.models import ImportLog, ImportStatus

from .parser import parse_excel
from .row_processor import process_row

logger = logging.getLogger(__name__)


@dataclass
class RowError:
    row: int
    message: str


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    errors: list[RowError] = field(default_factory=list)


def process_excel_import(import_log: ImportLog) -> None:
    logger.info("Starting import for ImportLog #%s", import_log.pk)

    import_log.status = ImportStatus.PROCESSING
    import_log.save(update_fields=["status"])

    try:
        parsed = parse_excel(import_log.file.path)
    except Exception as exc:
        logger.exception("Failed to parse excel")
        import_log.status = ImportStatus.FAILED
        import_log.errors = [{"row": 0, "message": f"Не удалось прочитать файл: {exc}"}]
        import_log.error_count = 1
        import_log.save(update_fields=["status", "errors", "error_count"])
        return

    import_log.total_rows = parsed.total_rows
    result = ImportResult()

    for row in parsed.rows:
        try:
            applied = process_row(row)
            if applied.created:
                result.created += 1
            else:
                result.updated += 1
        except Exception as exc:
            logger.exception("Row import failed: row=%s", row.row_number)
            result.errors.append(RowError(row=row.row_number, message=str(exc)))

    if result.errors and (result.created > 0 or result.updated > 0):
        status = ImportStatus.PARTIAL
    elif result.errors:
        status = ImportStatus.FAILED
    else:
        status = ImportStatus.SUCCESS

    import_log.status = status
    import_log.created_count = result.created
    import_log.updated_count = result.updated
    import_log.error_count = len(result.errors)
    import_log.errors = [{"row": err.row, "message": err.message} for err in result.errors]
    import_log.save(
        update_fields=[
            "status",
            "total_rows",
            "created_count",
            "updated_count",
            "error_count",
            "errors",
        ]
    )
