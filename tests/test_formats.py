import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xconvr import (  # noqa: E402
    ARCHIVE_FORMATS,
    IMAGE_FORMATS,
    MEDIA_FORMATS,
    _ext,
)


def test_ext_normalized():
    assert _ext("Photo.JPG") == "jpg"
    assert _ext("song.mp3") == "mp3"
    assert _ext("archive.tar.gz") == "gz"


def test_format_sets_cover_common_types():
    for fmt in ("jpg", "png", "webp", "heic"):
        assert fmt in IMAGE_FORMATS
    for fmt in ("mp3", "wav", "mp4", "mkv"):
        assert fmt in MEDIA_FORMATS
    for fmt in ("zip", "7z", "tar", "rar"):
        assert fmt in ARCHIVE_FORMATS
