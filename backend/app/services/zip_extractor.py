"""ZIP archive extraction service."""

import logging
import shutil
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

EMAIL_EXTENSIONS = {".eml", ".msg", ".txt", ".mime"}


class ZipExtractorService:
    """Extract email files from uploaded ZIP archives."""

    def extract(self, zip_path: Path, destination: Path) -> list[Path]:
        """
        Extract a ZIP archive and return paths to discovered email files.

        Raises:
            ValueError: If the file is not a valid ZIP archive.
        """
        if not zipfile.is_zipfile(zip_path):
            raise ValueError("Uploaded file is not a valid ZIP archive")

        destination.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(destination)

        email_files = self._discover_email_files(destination)
        logger.info("Discovered %s email files in %s", len(email_files), zip_path.name)
        return email_files

    def cleanup(self, directory: Path) -> None:
        """Remove a temporary extraction directory."""
        if directory.exists():
            shutil.rmtree(directory, ignore_errors=True)

    def _discover_email_files(self, root: Path) -> list[Path]:
        files: list[Path] = []
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in EMAIL_EXTENSIONS:
                files.append(path)
        return sorted(files)
