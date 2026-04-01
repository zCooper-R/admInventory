from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ParsedRow:
    row_number: int
    values: dict[str, Any]


@dataclass(slots=True)
class ParseResult:
    rows: list[ParsedRow]
    total_rows: int
    skipped_empty_rows: int = 0
    skipped_numbering_rows: int = 0
    skipped_non_device_rows: int = 0
