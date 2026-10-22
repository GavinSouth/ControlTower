"""Print the API's OpenAPI schema as JSON (the web app generates its TypeScript types from it).

    uv run python -m controltower.api.openapi > ../web/openapi.json

Or from web/: `npm run gen:api`, which also regenerates `src/api/schema.d.ts`.
"""

import json

from controltower.api.app import create_app


def openapi_json() -> str:
    return json.dumps(create_app().openapi(), indent=2) + "\n"


if __name__ == "__main__":
    print(openapi_json(), end="")
