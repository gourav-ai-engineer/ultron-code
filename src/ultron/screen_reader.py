"""Optional OCR-based screen text extraction for UI fallback observation."""

from dataclasses import dataclass
from pathlib import Path
import os


class ScreenTextUnavailableError(RuntimeError):
    """Raised when OCR dependencies or the OCR engine are unavailable."""


@dataclass(frozen=True)
class ScreenText:
    """Text extracted from one screenshot."""

    path: str
    text: str


class PytesseractScreenReader:
    """Extract visible text from screenshots using Tesseract."""

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or os.getenv("ULTRON_TESSERACT_CMD")

    def read(self, image_path: Path | str) -> ScreenText:
        try:
            from PIL import Image
            import pytesseract
        except ImportError as exc:
            raise ScreenTextUnavailableError(
                "Install the optional OCR dependencies to read screen text."
            ) from exc

        if self.executable:
            pytesseract.pytesseract.tesseract_cmd = self.executable

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Screenshot does not exist: {path}")

        try:
            with Image.open(path) as image:
                text = pytesseract.image_to_string(image)
        except Exception as exc:
            raise ScreenTextUnavailableError(f"OCR failed: {exc}") from exc

        return ScreenText(path=str(path), text=text.strip()[:8000])
