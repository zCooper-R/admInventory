from django.db import migrations, models


def _normalize(value: str) -> str:
    import re

    whitespace_re = re.compile(r"\s+")
    non_word_re = re.compile(r"[^\w\s]", re.UNICODE)
    abbr_map = {
        "муниципальное": "м",
        "казенное": "к",
        "казённое": "к",
        "бюджетное": "б",
        "общеобразовательное": "о",
        "учреждение": "у",
    }

    raw = (value or "").strip().lower()
    raw = non_word_re.sub(" ", raw)
    raw = whitespace_re.sub(" ", raw).strip()
    tokens = [abbr_map.get(tok, tok) for tok in raw.split(" ") if tok]

    if tokens[:3] == ["м", "к", "у"]:
        tokens = ["мку"] + tokens[3:]
    if tokens[:3] == ["м", "б", "у"]:
        tokens = ["мбу"] + tokens[3:]
    if tokens[:4] == ["м", "б", "о", "у"]:
        tokens = ["мбоу"] + tokens[4:]

    return " ".join(tokens).strip()


def populate_normalized_names(apps, schema_editor):
    Organization = apps.get_model("locations", "Organization")
    used = set()
    for org in Organization.objects.all().order_by("id"):
        base = _normalize(org.name)
        candidate = base
        i = 1
        while candidate in used:
            i += 1
            candidate = f"{base} {i}"
        used.add(candidate)
        org.normalized_name = candidate
        org.save(update_fields=["normalized_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="normalized_name",
            field=models.CharField(blank=True, db_index=True, default="", max_length=255, verbose_name="Нормализованное название"),
        ),
        migrations.RunPython(populate_normalized_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="organization",
            name="normalized_name",
            field=models.CharField(db_index=True, editable=False, max_length=255, unique=True, verbose_name="Нормализованное название"),
        ),
    ]
