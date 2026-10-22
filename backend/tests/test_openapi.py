"""The web app's committed schema must match the API, or its generated types are stale."""

from pathlib import Path

import pytest

from controltower.api.openapi import openapi_json

WEB_SCHEMA = Path(__file__).resolve().parents[2] / "web" / "openapi.json"


@pytest.mark.skipif(not WEB_SCHEMA.exists(), reason="no web app checked out")
def test_web_openapi_schema_is_current() -> None:
    # If this fails after an API change, run `npm run gen:api` in web/ and commit the result.
    assert WEB_SCHEMA.read_text() == openapi_json()
