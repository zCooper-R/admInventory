"""Facade service for target Excel import."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from apps.import_export.models import ImportLog, ImportStatus

from .parser import parse_excel
from .row_processor import RowValidationError, process_row

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

    @property
    def total_processed(self) -> int:
        return self.created + self.updated + len(self.errors)



def _save_result(import_log: ImportLog, result: ImportResult, total_rows: int) -> None:
    if result.errors and (result.created > 0 or result.updated > 0):
        status = ImportStatus.PARTIAL
    elif result.errors:
        status = ImportStatus.FAILED
    else:
        status = ImportStatus.SUCCESS

    import_log.status = status
    import_log.total_rows = total_rows
    import_log.created_count = result.created
    import_log.updated_count = result.updated
    import_log.error_count = len(result.errors)
    import_log.errors = [{"row": e.row, "message": e.message} for e in result.errors]
    import_log.save(update_fields=["status", "total_rows", "created_count", "updated_count", "error_count", "errors"])



def process_import_log(import_log: ImportLog) -> ImportResult:
    logger.info("Starting import for ImportLog #%s", import_log.pk)

    import_log.status = ImportStatus.PROCESSING
    import_log.save(update_fields=["status"])

    parsed = parse_excel(import_log.file.path)
    result = ImportResult()

    if parsed.errors:
        result.errors.extend(RowError(row=e["row"], message=e["message"]) for e in parsed.errors)
        _save_result(import_log, result, 0)
        return result

    for row_num, row in parsed.rows:
        try:
            created, _ = process_row(row_num=row_num, row=row)
            if created:
                result.created += 1
            else:
                result.updated += 1
        except RowValidationError as exc:
            result.errors.append(RowError(row=row_num, message=str(exc)))
        except Exception as exc:  # pragma: no cover
            logger.exception("Unexpected error on row %s", row_num)
            result.errors.append(RowError(row=row_num, message=str(exc)))

    _save_result(import_log, result, len(parsed.rows))
    logger.info(
        "Import #%s done: created=%s, updated=%s, errors=%s",
        import_log.pk,
        result.created,
        result.updated,
        len(result.errors),
    )
    return result
