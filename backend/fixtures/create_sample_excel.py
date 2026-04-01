"""
Run this script to generate a sample Excel file for import testing.
Usage: python fixtures/create_sample_excel.py
"""

from pathlib import Path

import pandas as pd

data = [
    {
        "name": "ПК-Импорт-001",
        "inventory_number": "IMPORT-001",
        "device_type": "PC",
        "cpu": "Intel Core i7-12700",
        "ram": 32,
        "storage_type": "SSD",
        "storage_size": 1000,
        "os": "Windows 11 Pro",
        "status": "active",
        "location": "Главный офис",
        "assigned_to": "ivanov",
    },
    {
        "name": "Ноутбук-Импорт-001",
        "inventory_number": "IMPORT-002",
        "device_type": "Laptop",
        "cpu": "AMD Ryzen 7 6800H",
        "ram": 16,
        "storage_type": "SSD",
        "storage_size": 512,
        "os": "Windows 11 Home",
        "status": "active",
        "location": "Филиал №1",
        "assigned_to": "",
    },
    {
        "name": "Принтер-Импорт-001",
        "inventory_number": "IMPORT-003",
        "device_type": "Printer",
        "cpu": "",
        "ram": "",
        "storage_type": "None",
        "storage_size": "",
        "os": "",
        "status": "broken",
        "location": "Главный офис",
        "assigned_to": "",
    },
]

output_path = Path(__file__).parent / "sample_import.xlsx"
df = pd.DataFrame(data)
df.to_excel(output_path, index=False)
print(f"Sample Excel created: {output_path}")
