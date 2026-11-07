"""本文の形の誤りは、422 と `{"detail": "<文>"}` で返す(方式設計の「横断の方式」の「例外とログ」・「API」)。

欄の欠け・型の違い・JSON として読めない本文は、どれも 422 と同じ文にする。送った値は応答に返さない。
OpenAPI の 422 の形も、ほかの誤りと同じ `{"detail": "<文>"}` の形にする(画面の型をこれから生成するため)。
"""

import secrets
from typing import Any, cast

import pytest

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.postgres import PostgresServer

# 方式設計の「横断の方式」の「例外とログ」の、本文の形の誤りの文
VALIDATION_ERROR_MESSAGE = "入力の形が正しくありません"

SECRET = secrets.token_urlsafe(16)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"employee_no": "000001"},
        {"password": SECRET},
        {"employee_no": 1, "password": SECRET},
        {"employee_no": "000001", "password": ["a", SECRET]},
        [],
        "000001",
    ],
    ids=["empty", "no_password", "no_employee_no", "number_employee_no", "list_password", "array", "string"],
)
def test_malformed_login_body_is_422_with_a_string_detail(postgres_server: PostgresServer, body: object) -> None:
    app = make_app(make_settings(postgres_server.url()))

    with api_client(app) as client:
        response = client.post("/api/auth/login", json=body)

    assert response.status_code == 422, response.text
    assert response.json() == {"detail": VALIDATION_ERROR_MESSAGE}
    assert SECRET not in response.text


def test_unreadable_json_body_is_422_with_a_string_detail(postgres_server: PostgresServer) -> None:
    app = make_app(make_settings(postgres_server.url()))

    with api_client(app) as client:
        response = client.post(
            "/api/auth/login",
            content=f'{{"employee_no": "000001", "password": "{SECRET}"',
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 422, response.text
    assert response.json() == {"detail": VALIDATION_ERROR_MESSAGE}
    assert SECRET not in response.text


def test_openapi_422_uses_the_common_error_shape(postgres_server: PostgresServer) -> None:
    app = make_app(make_settings(postgres_server.url()))
    spec: dict[str, Any] = app.openapi()

    error_refs: set[str] = set()
    for path, operations in cast(dict[str, dict[str, Any]], spec["paths"]).items():
        for method, operation in operations.items():
            responses = cast(dict[str, Any], operation["responses"])
            if "422" not in responses:
                continue
            ref = responses["422"]["content"]["application/json"]["schema"]["$ref"]
            assert ref == "#/components/schemas/ErrorResponse", (method, path, ref)
            error_refs.add(ref)

    assert error_refs, "422 を返す口が OpenAPI に無い"
    schemas = cast(dict[str, Any], spec["components"]["schemas"])
    assert "HTTPValidationError" not in schemas
    assert schemas["ErrorResponse"]["properties"]["detail"]["type"] == "string"
