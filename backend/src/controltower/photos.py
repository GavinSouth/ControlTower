"""Photo processing and storage (F3.5): resize uploads to WebP copies on disk.

`process()` is pure (bytes in, images out) so it is easy to test. `PhotoStore` writes
and deletes the files, one folder per photo: `<root>/<photo id>/{sm,md,lg}.webp`.

Privacy: the copies are re-encoded from pixels only, so EXIF (GPS location, camera,
timestamps) is never written. The EXIF rotation is applied first, so phone photos
still stand the right way up.
"""

import io
import shutil
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import pillow_heif
from PIL import Image, ImageOps, UnidentifiedImageError

pillow_heif.register_heif_opener()  # lets Pillow open HEIC/HEIF (iPhone photos)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ACCEPTED_FORMATS = frozenset({"JPEG", "PNG", "WEBP", "HEIF"})
WEBP_QUALITY = 80


class PhotoSize(StrEnum):
    """Stored copies, by longest edge in pixels. Smaller images are never upscaled."""

    sm = "sm"  # trip cards
    md = "md"  # cover and banner on a phone or laptop
    lg = "lg"  # cover on large or high-density screens

    @property
    def max_edge(self) -> int:
        return {"sm": 400, "md": 1200, "lg": 2400}[self.value]


class InvalidPhotoError(ValueError):
    """The upload is not an image we accept (bad format, corrupt, or too large)."""


@dataclass(frozen=True)
class ProcessedPhoto:
    width: int  # of the lg copy
    height: int
    copies: dict[PhotoSize, bytes]  # WebP bytes per size


def process(data: bytes) -> ProcessedPhoto:
    """Decode an upload, fix its rotation, and encode one WebP copy per size."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidPhotoError(f"file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in ACCEPTED_FORMATS:
                raise InvalidPhotoError(f"unsupported image format: {source.format}")
            image = ImageOps.exif_transpose(source)
            image.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as err:
        raise InvalidPhotoError("not a readable image") from err

    # WebP has no CMYK; palette and other modes convert cleanly to RGB(A).
    icc_profile = image.info.get("icc_profile")  # colour profile (e.g. Display P3): kept
    image = image.convert("RGBA" if image.has_transparency_data else "RGB")
    copies: dict[PhotoSize, bytes] = {}
    dimensions: dict[PhotoSize, tuple[int, int]] = {}
    for size in PhotoSize:
        copy = image.copy()
        copy.thumbnail((size.max_edge, size.max_edge), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        # No exif= argument, so no EXIF is written.
        copy.save(buffer, "WEBP", quality=WEBP_QUALITY, icc_profile=icc_profile)
        copies[size] = buffer.getvalue()
        dimensions[size] = copy.size
    width, height = dimensions[PhotoSize.lg]
    return ProcessedPhoto(width=width, height=height, copies=copies)


class PhotoStore:
    """Photo files on local disk. Swappable for S3/R2 later (Phase 6) behind the same API."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, photo_id: uuid.UUID, size: PhotoSize) -> Path:
        return self.root / str(photo_id) / f"{size.value}.webp"

    def save(self, photo_id: uuid.UUID, photo: ProcessedPhoto) -> None:
        folder = self.root / str(photo_id)
        folder.mkdir(parents=True, exist_ok=True)
        for size, data in photo.copies.items():
            self.path(photo_id, size).write_bytes(data)

    def delete(self, photo_id: uuid.UUID) -> None:
        """Remove a photo's files; a missing folder is fine."""
        shutil.rmtree(self.root / str(photo_id), ignore_errors=True)
