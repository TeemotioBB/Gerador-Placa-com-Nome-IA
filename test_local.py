from pathlib import Path

from generator import generate_jpeg_bytes


NAMES = [
    "Henrique",
    "Pedro",
    "Lucas",
    "Maycon",
]

output_dir = Path(
    "testes"
)

output_dir.mkdir(
    exist_ok=True
)

for name in NAMES:
    path = (
        output_dir
        / f"{name}.jpg"
    )

    path.write_bytes(
        generate_jpeg_bytes(
            name
        )
    )

    print(
        "OK:",
        path,
    )
