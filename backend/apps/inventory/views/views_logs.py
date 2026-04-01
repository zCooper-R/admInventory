from __future__ import annotations

import logging
import re
from collections import deque
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

web_logger = logging.getLogger("apps.inventory.views")

DEFAULT_TAIL_LINES = 200
MAX_TAIL_LINES = 2000
ALLOWED_LEVELS = ("", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def _is_admin_user(user) -> bool:
    return bool(
        user.is_authenticated
        and (user.is_superuser or getattr(user, "role", "") == "admin")
    )


def _list_log_files(log_dir: Path) -> list[Path]:
    if not log_dir.exists():
        return []
    files = [p for p in log_dir.glob("*.log*") if p.is_file()]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def _read_tail_filtered(path: Path, lines: int, level: str, query: str) -> list[str]:
    ring: deque[str] = deque(maxlen=lines)
    level_re = (
        re.compile(rf"\|\s*{re.escape(level)}\s*\|", flags=re.IGNORECASE)
        if level
        else None
    )
    query_l = query.lower().strip()

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            if level_re and not level_re.search(line):
                continue
            if query_l and query_l not in line.lower():
                continue
            ring.append(line)

    return list(ring)


@login_required
def logs_view(request):
    if not _is_admin_user(request.user):
        messages.error(
            request, "Доступ к просмотру логов разрешён только администраторам."
        )
        return redirect("dashboard")

    log_dir = Path(settings.LOG_DIR)
    files = _list_log_files(log_dir)
    file_map = {item.name: item for item in files}

    selected_name = request.GET.get("file", "").strip()
    if not selected_name and files:
        selected_name = files[0].name

    selected_file = file_map.get(selected_name)
    if selected_name and not selected_file:
        messages.warning(request, f"Файл лога «{selected_name}» недоступен.")

    try:
        lines = int(request.GET.get("lines", DEFAULT_TAIL_LINES))
    except (TypeError, ValueError):
        lines = DEFAULT_TAIL_LINES
    lines = max(50, min(lines, MAX_TAIL_LINES))

    level = (request.GET.get("level", "") or "").upper().strip()
    if level not in ALLOWED_LEVELS:
        level = ""

    query = (request.GET.get("q", "") or "").strip()

    rendered_lines: list[str] = []
    if selected_file:
        rendered_lines = _read_tail_filtered(
            selected_file, lines=lines, level=level, query=query
        )

    web_logger.info(
        "Просмотр логов: user=%s file=%s lines=%s level=%s q=%s",
        request.user.username,
        selected_name or "-",
        lines,
        level or "-",
        bool(query),
    )

    return render(
        request,
        "inventory/logs.html",
        {
            "nav_active": "logs",
            "log_files": files,
            "selected_file_name": selected_name,
            "selected_lines": lines,
            "selected_level": level,
            "query": query,
            "rendered_lines": rendered_lines,
            "allowed_levels": [item for item in ALLOWED_LEVELS if item],
        },
    )


@login_required
def logs_download_view(request):
    if not _is_admin_user(request.user):
        raise Http404("Not found")

    file_name = (request.GET.get("file", "") or "").strip()
    if not file_name:
        raise Http404("Not found")

    log_dir = Path(settings.LOG_DIR)
    file_map = {item.name: item for item in _list_log_files(log_dir)}
    selected_file = file_map.get(file_name)
    if not selected_file:
        raise Http404("Not found")

    web_logger.info(
        "Скачивание лога: user=%s file=%s",
        request.user.username,
        file_name,
    )
    return FileResponse(
        selected_file.open("rb"),
        as_attachment=True,
        filename=selected_file.name,
        content_type="text/plain; charset=utf-8",
    )
