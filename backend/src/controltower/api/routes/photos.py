"""Cover photos (F3.5): upload, replace, or remove a trip's cover, and serve photo files.

Uploads are multipart form data (`file` field). Each upload becomes a new photo with a new
id, so the files behind a URL never change and browsers may cache them for a year.
"""

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Response, UploadFile
from fastapi.responses import FileResponse

from controltower.api.deps import (
    OwnerDep,
    PhotoStoreDep,
    SessionDep,
    get_trip,
    not_found,
    unprocessable,
)
from controltower.api.routes.trips import my_trip_read
from controltower.api.schemas import TripRead
from controltower.models import Photo
from controltower.photos import MAX_UPLOAD_BYTES, InvalidPhotoError, PhotoSize, process

router = APIRouter(tags=["photos"])

_CACHE_FOREVER = "private, max-age=31536000, immutable"


@router.put("/trips/{trip_id}/cover")
def put_cover(
    trip_id: UUID,
    session: SessionDep,
    owner: OwnerDep,
    store: PhotoStoreDep,
    file: Annotated[UploadFile, File(description="JPEG, PNG, WebP, or HEIC, up to 20 MB")],
) -> TripRead:
    """Set or replace the trip's cover photo. EXIF data (incl. GPS location) is removed."""
    trip = get_trip(session, owner, trip_id)
    # A sync route runs in a worker thread, so the resize doesn't block other requests.
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    try:
        processed = process(data)
    except InvalidPhotoError as err:
        raise unprocessable(f"file: {err}") from err

    photo = Photo(
        id=uuid4(),
        owner_id=owner.id,
        width=processed.width,
        height=processed.height,
        original_name=file.filename[:255] if file.filename else None,
    )
    store.save(photo.id, processed)
    old = trip.cover_photo
    try:
        session.add(photo)
        trip.cover_photo = photo
        if old is not None:
            session.delete(old)
        session.commit()
    except Exception:
        store.delete(photo.id)  # don't leave orphan files behind a failed commit
        raise
    if old is not None:
        store.delete(old.id)
    return my_trip_read(session, owner, trip)


@router.delete("/trips/{trip_id}/cover")
def delete_cover(
    trip_id: UUID, session: SessionDep, owner: OwnerDep, store: PhotoStoreDep
) -> TripRead:
    """Remove the trip's cover photo (no-op if it has none); the cover falls back to teal."""
    trip = get_trip(session, owner, trip_id)
    old = trip.cover_photo
    if old is not None:
        trip.cover_photo = None
        session.delete(old)
        session.commit()
        store.delete(old.id)
    return my_trip_read(session, owner, trip)


@router.get(
    "/photos/{photo_id}/{size}",
    response_class=FileResponse,
    responses={200: {"content": {"image/webp": {}}, "description": "The WebP file"}},
)
def read_photo(
    photo_id: UUID, size: PhotoSize, session: SessionDep, owner: OwnerDep, store: PhotoStoreDep
) -> Response:
    """One stored copy of a photo: sm (400px), md (1200px), or lg (2400px), longest edge."""
    photo = session.get(Photo, photo_id)
    path = store.path(photo_id, size)
    if photo is None or photo.owner_id != owner.id or not path.is_file():
        raise not_found("photo")
    return FileResponse(
        path,
        media_type="image/webp",
        headers={"Cache-Control": _CACHE_FOREVER},
    )
