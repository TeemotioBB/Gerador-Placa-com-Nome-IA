from __future__ import annotations

import io
import os
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

BASE_DIR = Path(__file__).resolve().parent

BASE_IMAGE_PATH = Path(
    os.getenv(
        "BASE_IMAGE_PATH",
        BASE_DIR / "assets" / "foto_base.png",
    )
)

CUSTOM_FONT_PATH = Path(
    os.getenv(
        "FONT_PATH",
        BASE_DIR / "fonts" / "handwriting.ttf",
    )
)

# ============================================================================
# CALIBRAÇÃO DA FOTO-BASE INCLUÍDA NO PROJETO
# ============================================================================
# A foto usada nesta calibração mede 1254 x 1254 px.
# Caso a MESMA foto seja apenas redimensionada, os pontos são escalados
# automaticamente.
REFERENCE_SIZE = (1254, 1254)

# Ordem:
# topo-esquerdo, topo-direito, baixo-direito, baixo-esquerdo
PAPER_QUAD_REFERENCE = [
    (648, 636),
    (1153, 679),
    (1107, 1081),
    (592, 999),
]

# Papel virtual. O nome é desenhado aqui antes da transformação
# de perspectiva.
VIRTUAL_PAPER_W = 520
VIRTUAL_PAPER_H = 390

# Área onde o nome é escrito, deixando o coração livre.
TEXT_BOX = (45, 85, 475, 185)

# Cor de tinta cinza-chumbo levemente azulada.
INK_COLOR = (45, 48, 58, 220)

START_FONT_SIZE = 74
MIN_FONT_SIZE = 36
SUPERSAMPLING = 4
TEXT_BLUR = 0.15
JPEG_QUALITY = 97


def _safe_name(value: str) -> str:
    """Valida e normaliza o nome."""
    value = re.sub(r"\s+", " ", value.strip())

    if not value:
        raise ValueError("O nome não pode estar vazio.")

    if len(value) > 30:
        raise ValueError("Use um nome com no máximo 30 caracteres.")

    if any(ord(ch) < 32 for ch in value):
        raise ValueError("O nome contém caracteres inválidos.")

    return value


def _load_font(size: int) -> ImageFont.ImageFont:
    """
    Usa fonts/handwriting.ttf quando existir.

    Se nenhuma fonte personalizada tiver sido adicionada,
    usa a fonte padrão do Pillow para que o deploy já funcione.
    """
    if CUSTOM_FONT_PATH.exists():
        return ImageFont.truetype(
            str(CUSTOM_FONT_PATH),
            size,
        )

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _measure_text(
    text: str,
    font: ImageFont.ImageFont,
):
    canvas = Image.new(
        "RGBA",
        (16, 16),
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(canvas)

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    return bbox, width, height


def _choose_font(
    text: str,
    max_width: int,
    max_height: int,
    scale: int,
):
    """
    Reduz a fonte automaticamente se o nome for comprido.
    """
    for logical_size in range(
        START_FONT_SIZE,
        MIN_FONT_SIZE - 1,
        -2,
    ):
        font = _load_font(
            logical_size * scale
        )

        _, width, height = _measure_text(
            text,
            font,
        )

        if (
            width <= max_width * scale
            and height <= max_height * scale
        ):
            return font

    return _load_font(
        MIN_FONT_SIZE * scale
    )


def _create_text_layer(
    name: str,
) -> Image.Image:
    """
    Cria uma camada RGBA independente contendo apenas o nome.
    O texto não é escrito diretamente na foto-base.
    """
    scale = SUPERSAMPLING

    layer_hr = Image.new(
        "RGBA",
        (
            VIRTUAL_PAPER_W * scale,
            VIRTUAL_PAPER_H * scale,
        ),
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(layer_hr)

    x1, y1, x2, y2 = TEXT_BOX

    box_w = x2 - x1
    box_h = y2 - y1

    font = _choose_font(
        text=name,
        max_width=box_w,
        max_height=box_h,
        scale=scale,
    )

    bbox, text_w, text_h = _measure_text(
        name,
        font,
    )

    # Centraliza o nome dentro da caixa calibrada.
    x = (
        ((x1 + x2) / 2) * scale
        - (text_w / 2)
        - bbox[0]
    )

    y = (
        ((y1 + y2) / 2) * scale
        - (text_h / 2)
        - bbox[1]
    )

    draw.text(
        (x, y),
        name,
        font=font,
        fill=INK_COLOR,
    )

    # Supersampling para evitar bordas serrilhadas.
    layer = layer_hr.resize(
        (
            VIRTUAL_PAPER_W,
            VIRTUAL_PAPER_H,
        ),
        Image.Resampling.LANCZOS,
    )

    if TEXT_BLUR > 0:
        layer = layer.filter(
            ImageFilter.GaussianBlur(
                TEXT_BLUR
            )
        )

    return layer


def _scaled_paper_quad(
    image_size: tuple[int, int],
):
    """
    Escala a calibração caso a mesma foto seja redimensionada.
    """
    width, height = image_size

    ref_w, ref_h = REFERENCE_SIZE

    sx = width / ref_w
    sy = height / ref_h

    return [
        (
            x * sx,
            y * sy,
        )
        for x, y in PAPER_QUAD_REFERENCE
    ]


def _perspective_coeffs(
    destination_points,
    source_points,
):
    """
    Calcula os coeficientes output -> input usados pelo Pillow.

    destination_points:
        pontos do papel na fotografia

    source_points:
        pontos do papel virtual
    """
    matrix = []
    vector = []

    for (
        (xd, yd),
        (xs, ys),
    ) in zip(
        destination_points,
        source_points,
    ):
        matrix.append(
            [
                xd,
                yd,
                1,
                0,
                0,
                0,
                -xs * xd,
                -xs * yd,
            ]
        )
        vector.append(xs)

        matrix.append(
            [
                0,
                0,
                0,
                xd,
                yd,
                1,
                -ys * xd,
                -ys * yd,
            ]
        )
        vector.append(ys)

    coefficients = np.linalg.solve(
        np.asarray(
            matrix,
            dtype=np.float64,
        ),
        np.asarray(
            vector,
            dtype=np.float64,
        ),
    )

    return coefficients.tolist()


def _warp_to_paper(
    text_layer: Image.Image,
    output_size: tuple[int, int],
) -> Image.Image:
    """
    Aplica a perspectiva ao texto.
    """
    source = [
        (0, 0),
        (
            text_layer.width - 1,
            0,
        ),
        (
            text_layer.width - 1,
            text_layer.height - 1,
        ),
        (
            0,
            text_layer.height - 1,
        ),
    ]

    destination = _scaled_paper_quad(
        output_size
    )

    coeffs = _perspective_coeffs(
        destination_points=destination,
        source_points=source,
    )

    return text_layer.transform(
        output_size,
        Image.Transform.PERSPECTIVE,
        coeffs,
        resample=Image.Resampling.BICUBIC,
    )


def generate_image(
    name: str,
) -> Image.Image:
    """
    Retorna a foto personalizada como objeto PIL.Image.
    """
    name = _safe_name(name)

    if not BASE_IMAGE_PATH.exists():
        raise FileNotFoundError(
            "Imagem base não encontrada: "
            f"{BASE_IMAGE_PATH}"
        )

    original = Image.open(
        BASE_IMAGE_PATH
    )

    original = ImageOps.exif_transpose(
        original
    )

    original = original.convert(
        "RGBA"
    )

    text_layer = _create_text_layer(
        name
    )

    warped_text = _warp_to_paper(
        text_layer=text_layer,
        output_size=original.size,
    )

    result = Image.alpha_composite(
        original,
        warped_text,
    ).convert("RGB")

    return result


def generate_jpeg_bytes(
    name: str,
) -> bytes:
    """
    Retorna a imagem JPEG em memória.
    Útil para FastAPI, Telegram etc.
    """
    image = generate_image(
        name
    )

    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=JPEG_QUALITY,
        subsampling=0,
        optimize=True,
    )

    return output.getvalue()


if __name__ == "__main__":
    out = (
        BASE_DIR
        / "teste_henrique.jpg"
    )

    out.write_bytes(
        generate_jpeg_bytes(
            "Henrique"
        )
    )

    print(
        f"Imagem criada: {out}"
    )
