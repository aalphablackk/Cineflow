import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")

import django
django.setup()

from django.core.management import call_command

sys.stdout.reconfigure(encoding="utf-8")

with open("cineflow_data.json", "w", encoding="utf-8") as file:
    call_command(
        "dumpdata",
        exclude=[
            "contenttypes",
            "auth.permission",
            "admin.logentry",
            "sessions",
        ],
        natural_foreign=True,
        natural_primary=True,
        indent=2,
        stdout=file,
    )

print("Export completed successfully.")