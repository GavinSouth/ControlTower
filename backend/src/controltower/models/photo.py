"""Photo: an uploaded image, stored as resized WebP files on disk (F3.5).

The row holds only metadata; the files live under the photo store (`photos.py`), one
folder per photo id. A photo is never edited: replacing a cover makes a new photo, so a
photo's URLs can be cached forever. Trips point at their cover (`trip.cover_photo_id`);
item and log photos can point here the same way later.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from controltower.models.base import Base, UUIDPrimaryKey, utc_now


class Photo(UUIDPrimaryKey, Base):
    __tablename__ = "photo"

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), index=True)
    # Size of the largest stored copy, after EXIF rotation (for aspect ratio and layout).
    width: Mapped[int]
    height: Mapped[int]
    original_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    def __repr__(self) -> str:
        return f"Photo({self.width}x{self.height})"
