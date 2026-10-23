"""Photo processing and storage (F3.5): sizes, rotation, EXIF stripping, formats."""

import io
import uuid
from pathlib import Path

import pytest
from PIL import Image

from controltower.photos import (
    MAX_UPLOAD_BYTES,
    InvalidPhotoError,
    PhotoSize,
    PhotoStore,
    process,
)

GPS_IFD = 0x8825
MAKE = 0x010F
ORIENTATION = 0x0112


def encode(fmt: str, size: tuple[int, int] = (3000, 2000), exif: Image.Exif | None = None) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", size, "teal")
    image.save(buffer, fmt, **({"exif": exif} if exif is not None else {}))
    return buffer.getvalue()


def phone_exif(orientation: int = 1) -> Image.Exif:
    exif = Image.Exif()
    exif[ORIENTATION] = orientation
    exif[MAKE] = "TestCam"
    exif[GPS_IFD] = {1: "N", 2: (35.0, 41.0, 0.0)}  # a latitude: where the photo was taken
    return exif


def open_copy(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


def test_makes_one_webp_per_size_by_longest_edge() -> None:
    photo = process(encode("JPEG", (3000, 2000)))
    assert set(photo.copies) == set(PhotoSize)
    for size, data in photo.copies.items():
        copy = open_copy(data)
        assert copy.format == "WEBP"
        assert copy.size == (size.max_edge, round(size.max_edge * 2 / 3))
    assert (photo.width, photo.height) == (2400, 1600)


def test_small_images_are_not_upscaled() -> None:
    photo = process(encode("PNG", (300, 350)))
    assert all(open_copy(d).size == (300, 350) for d in photo.copies.values())
    assert (photo.width, photo.height) == (300, 350)


def test_exif_and_gps_location_are_removed() -> None:
    upload = encode("JPEG", exif=phone_exif())
    assert open_copy(upload).getexif().get_ifd(GPS_IFD)  # the test file really has GPS
    for data in process(upload).copies.values():
        copy = open_copy(data)
        assert not copy.getexif()
        assert "exif" not in copy.info


def test_exif_rotation_is_applied_before_stripping() -> None:
    # Orientation 6: stored landscape, meant to be shown rotated 90° (a portrait phone shot).
    photo = process(encode("JPEG", (3000, 2000), exif=phone_exif(orientation=6)))
    assert (photo.width, photo.height) == (1600, 2400)


@pytest.mark.parametrize("fmt", ["PNG", "WEBP", "HEIF"])
def test_accepts_png_webp_and_heic(fmt: str) -> None:
    assert process(encode(fmt, (800, 600))).width == 800


def test_transparent_png_keeps_its_alpha() -> None:
    buffer = io.BytesIO()
    Image.new("RGBA", (100, 100), (0, 0, 0, 0)).save(buffer, "PNG")
    assert open_copy(process(buffer.getvalue()).copies[PhotoSize.sm]).mode == "RGBA"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"not an image", "not a readable image"),
        (encode("GIF", (10, 10)), "unsupported image format: GIF"),
        (b"\0" * (MAX_UPLOAD_BYTES + 1), "larger than 20 MB"),
    ],
)
def test_rejects_bad_uploads(data: bytes, message: str) -> None:
    with pytest.raises(InvalidPhotoError, match=message):
        process(data)


def test_store_saves_and_deletes_one_folder_per_photo(tmp_path: Path) -> None:
    store = PhotoStore(tmp_path)
    photo_id = uuid.uuid4()
    store.save(photo_id, process(encode("JPEG", (500, 500))))
    assert all(store.path(photo_id, size).is_file() for size in PhotoSize)
    store.delete(photo_id)
    assert not (tmp_path / str(photo_id)).exists()
    store.delete(photo_id)  # deleting twice is fine
