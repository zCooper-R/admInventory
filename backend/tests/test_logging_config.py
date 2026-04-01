import logging

import pytest
from django.conf import settings


@pytest.mark.django_db
def test_logging_configuration_contains_expected_handlers():
    handlers = settings.LOGGING.get("handlers", {})
    expected = {
        "app_file",
        "errors_file",
        "import_file",
        "replacement_file",
        "web_file",
        "security_file",
        "tasks_file",
        "audit_file",
    }
    assert expected.issubset(set(handlers.keys()))


@pytest.mark.django_db
def test_module_loggers_are_configured():
    loggers = settings.LOGGING.get("loggers", {})
    assert "apps.import_export.excel_import" in loggers
    assert "apps.inventory.services.replacement" in loggers
    assert "apps.inventory.views" in loggers
    assert "apps.inventory.audit" in loggers

    assert logging.getLogger("apps.import_export.excel_import.parser")
    assert logging.getLogger("apps.inventory.services.replacement")
