import pytest

from domain.exceptions import InvalidURLError
from domain.models import CaptureSettings


def test_capture_settings_accepts_http_url() -> None:
    settings = CaptureSettings(url="  https://example.com  ")
    assert settings.url == "https://example.com"


@pytest.mark.parametrize("url", ["example.com", "ftp://example.com", "", "javascript:alert(1)"])
def test_capture_settings_rejects_unsupported_url(url: str) -> None:
    with pytest.raises(InvalidURLError):
        CaptureSettings(url=url)
