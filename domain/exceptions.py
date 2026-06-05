"""Business exceptions exposed to the application layer."""


class StreamlitOCRError(Exception):
    """Base exception for errors that can be presented to the user."""


class InvalidURLError(StreamlitOCRError):
    """Raised when a capture URL is missing or unsupported."""


class CaptureError(StreamlitOCRError):
    """Raised when the browser capture cannot complete."""


class VideoProcessingError(StreamlitOCRError):
    """Raised when video conversion or frame extraction fails."""


class OCRProcessingError(StreamlitOCRError):
    """Raised when Tesseract cannot process an image."""


class ExportError(StreamlitOCRError):
    """Raised when a document cannot be exported."""

