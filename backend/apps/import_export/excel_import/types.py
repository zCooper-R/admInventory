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
