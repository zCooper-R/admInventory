import io

import pandas as pd

from apps.inventory.models import Device, DeviceType


def export_pcs_to_excel() -> bytes:
    devices = (
        Device.objects.filter(device_type=DeviceType.PC)
        .select_related("organization", "browser", "position")
        .order_by("organization__name", "inventory_number")
    )

    rows = []
    for d in devices:
        rows.append(
            {
                "Инв. №": d.inventory_number,
                "Организация": d.organization.name,
                "Адрес организации": d.organization.address,
                "Наименование ОС": d.os,
                "Процессор": d.cpu_model,
                "Тактовая частота": d.cpu_frequency,
                "Оперативная память": d.ram,
                "Тип диска": d.storage_type,
                "Емкость диска": d.storage_size,
                "Браузер": d.browser.name if d.browser else "",
                "Google": d.has_google_account,
                "Apple": d.has_apple_account,
                "Microsoft": d.has_microsoft_account,
                "Скорость интернета": d.get_internet_speed_display() if d.internet_speed else "",
                "Провайдер": d.provider,
                "Аттестованный": d.is_certified,
                "Текст": d.use_for_text,
                "Изображения": d.use_for_images,
                "Презентации": d.use_for_presentations,
                "Аудио": d.use_for_audio,
                "Видео": d.use_for_video,
                "Сотрудник": d.employee_name,
                "Должность": d.position.name if d.position else "",
                "Статус замены": d.get_replacement_status_display(),
                "Оценка": d.replacement_score,
                "Причины": d.replacement_reason,
            }
        )

    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Устройства")
    buffer.seek(0)
    return buffer.read()
