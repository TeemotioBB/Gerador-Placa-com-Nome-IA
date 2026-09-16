from __future__ import annotations

import os
import re

from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Query,
)
from fastapi.responses import (
    HTMLResponse,
    Response,
)
from pydantic import BaseModel

from generator import generate_jpeg_bytes


app = FastAPI(
    title="Foto Personalizada API",
    version="1.0.0",
)

# Opcional.
# Se não existir no Railway, a API fica aberta para o primeiro teste.
API_KEY = os.getenv(
    "API_KEY",
    "",
).strip()


class GenerateRequest(BaseModel):
    name: str


def _authorize(
    x_api_key: str | None,
):
    if (
        API_KEY
        and x_api_key != API_KEY
    ):
        raise HTTPException(
            status_code=401,
            detail="API key inválida.",
        )


def _filename(
    name: str,
) -> str:
    safe = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        name.strip(),
    )[:40]

    if not safe:
        safe = "nome"

    return (
        f"personalizada_{safe}.jpg"
    )


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": (
            "foto-personalizada"
        ),
    }


@app.get(
    "/",
    response_class=HTMLResponse,
)
def home():
    return HTMLResponse(
        """
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width,initial-scale=1"
    >

    <title>
        Teste - Foto Personalizada
    </title>

    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 760px;
            margin: 40px auto;
            padding: 0 18px;
            background: #f4f4f4;
        }

        .card {
            background: #fff;
            border-radius: 18px;
            padding: 24px;
            box-shadow:
                0 10px 30px
                rgba(0, 0, 0, .08);
        }

        form {
            display: flex;
            gap: 8px;
            margin: 20px 0;
        }

        input {
            flex: 1;
            padding: 12px;
            font-size: 16px;
        }

        button {
            padding: 12px 18px;
            cursor: pointer;
        }

        img {
            width: 100%;
            max-width: 620px;
            border-radius: 12px;
            display: block;
            margin-top: 20px;
        }

        small {
            color: #666;
        }

        code {
            background: #eee;
            padding: 2px 5px;
            border-radius: 5px;
        }
    </style>
</head>

<body>
    <div class="card">
        <h1>
            Teste da foto personalizada
        </h1>

        <p>
            Digite um nome para gerar
            a imagem.
        </p>

        <form id="form">
            <input
                id="name"
                maxlength="30"
                value="Henrique"
                autocomplete="off"
                required
            >

            <button type="submit">
                Gerar
            </button>
        </form>

        <small>
            Para aparência manuscrita,
            adicione sua fonte em
            <code>
                fonts/handwriting.ttf
            </code>.
        </small>

        <img
            id="preview"
            alt="Imagem gerada"
            hidden
        >
    </div>

    <script>
        const form =
            document.getElementById(
                "form"
            );

        const input =
            document.getElementById(
                "name"
            );

        const preview =
            document.getElementById(
                "preview"
            );

        form.addEventListener(
            "submit",
            function (event) {
                event.preventDefault();

                const name =
                    encodeURIComponent(
                        input.value
                    );

                preview.src =
                    "/generate?name="
                    + name
                    + "&t="
                    + Date.now();

                preview.hidden = false;
            }
        );
    </script>
</body>
</html>
        """
    )


@app.get("/generate")
def generate_get(
    name: str = Query(
        ...,
        min_length=1,
        max_length=30,
    ),
    x_api_key: str | None = Header(
        default=None
    ),
):
    _authorize(
        x_api_key
    )

    try:
        data = generate_jpeg_bytes(
            name
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return Response(
        data,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": (
                'inline; filename="'
                + _filename(name)
                + '"'
            ),
            "Cache-Control": "no-store",
        },
    )


@app.post("/generate")
def generate_post(
    body: GenerateRequest,
    x_api_key: str | None = Header(
        default=None
    ),
):
    _authorize(
        x_api_key
    )

    try:
        data = generate_jpeg_bytes(
            body.name
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return Response(
        data,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": (
                'inline; filename="'
                + _filename(
                    body.name
                )
                + '"'
            ),
            "Cache-Control": "no-store",
        },
    )
