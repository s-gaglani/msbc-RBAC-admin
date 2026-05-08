# my_project/migration_naming_patch.py
from datetime import datetime
import random
from django.db.migrations.writer import MigrationWriter

"""
    - Prevent migration naming conflicts across developers
    - Ensure globally unique migration filenames
    - Improve readability for CI/CD and production debugging
"""


def unique_timestamp():
    """Return timestamp with milliseconds: YYYYMMDD_HHMMSS_mmm"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


class CustomMigrationWriter(MigrationWriter):

    @property
    def filename(self):
        """
        Override default 0001_XXX.py => <timestamp>_<name>.py
        """

        ts = unique_timestamp()

        name = self.migration.name

        # OPTIONAL random suffix for absolute uniqueness

        filename = f"V{ts}_{name}.py"
        return filename



MigrationWriter.filename = CustomMigrationWriter.filename
