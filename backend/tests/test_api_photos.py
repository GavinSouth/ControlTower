"""Cover photos through HTTP (F3.5): upload, replace, remove, serve, and clean up files."""

import io
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

from controltower.photos import PhotoStore

TRIP = {"title": "Lisbon", "home_tz": "Europe/Lisbon"}


def jpeg(size: tuple[int, int] = (1600, 900)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, "teal").save(buffer, "JPEG")
    return buffer.getvalue()


def new_trip(client: TestClient) -> dict[str, Any]:
    response = client.post("/trips", json=TRIP)
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


def upload(client: TestClient, trip_id: str, data: bytes, name: str = "cover.jpg") -> Any:
    return client.put(f"/trips/{trip_id}/cover", files={"file": (name, data, "image/jpeg")})


def folders(store: PhotoStore) -> list[Path]:
    return sorted(store.root.iterdir()) if store.root.exists() else []


def test_upload_sets_the_cover_and_serves_each_size(client: TestClient) -> None:
    trip = new_trip(client)
    assert trip["cover"] is None

    response = upload(client, trip["id"], jpeg())
    assert response.status_code == 200, response.text
    cover = response.json()["cover"]
    assert (cover["width"], cover["height"]) == (1600, 900)  # under lg: not upscaled

    assert client.get(f"/trips/{trip['id']}").json()["cover"] == cover
    assert client.get("/trips").json()[0]["cover"] == cover

    for size in ("sm", "md", "lg"):
        image = client.get(f"/photos/{cover['id']}/{size}")
        assert image.status_code == 200
        assert image.headers["content-type"] == "image/webp"
        assert "immutable" in image.headers["cache-control"]
    assert client.get(f"/photos/{cover['id']}/xl").status_code == 422


def test_replacing_the_cover_deletes_the_old_photo(
    client: TestClient, photo_store: PhotoStore
) -> None:
    trip = new_trip(client)
    first = upload(client, trip["id"], jpeg()).json()["cover"]
    second = upload(client, trip["id"], jpeg((800, 800))).json()["cover"]

    assert second["id"] != first["id"]  # a new id, so cached URLs never go stale
    assert client.get(f"/photos/{first['id']}/sm").status_code == 404
    assert [f.name for f in folders(photo_store)] == [second["id"]]


def test_removing_the_cover(client: TestClient, photo_store: PhotoStore) -> None:
    trip = new_trip(client)
    cover = upload(client, trip["id"], jpeg()).json()["cover"]

    response = client.delete(f"/trips/{trip['id']}/cover")
    assert response.status_code == 200
    assert response.json()["cover"] is None
    assert client.get(f"/photos/{cover['id']}/md").status_code == 404
    assert folders(photo_store) == []
    assert client.delete(f"/trips/{trip['id']}/cover").status_code == 200  # no-op


def test_deleting_the_trip_deletes_its_cover(client: TestClient, photo_store: PhotoStore) -> None:
    trip = new_trip(client)
    upload(client, trip["id"], jpeg())
    assert client.delete(f"/trips/{trip['id']}").status_code == 204
    assert folders(photo_store) == []


def test_bad_upload_is_422_and_leaves_no_files(client: TestClient, photo_store: PhotoStore) -> None:
    trip = new_trip(client)
    response = upload(client, trip["id"], b"not an image", name="notes.txt")
    assert response.status_code == 422
    assert "not a readable image" in response.text
    assert client.get(f"/trips/{trip['id']}").json()["cover"] is None
    assert folders(photo_store) == []


def test_missing_trip_or_photo_is_404(client: TestClient) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    assert upload(client, missing, jpeg()).status_code == 404
    assert client.get(f"/photos/{missing}/sm").status_code == 404
