# Foto Personalizada — Pillow + FastAPI + Railway

Projeto pronto para GitHub e Railway.

A API insere o nome em uma camada RGBA separada, aplica perspectiva
para acompanhar o papel e compõe o resultado na foto-base.

O coração da foto-base é preservado.

> A imagem é uma composição automática. Não a apresente como prova de
> que a foto foi tirada naquele instante ou escrita pessoalmente pela
> modelo se isso não aconteceu.

## Estrutura

```text
.
├── app.py
├── generator.py
├── requirements.txt
├── Dockerfile
├── railway.json
├── test_local.py
├── assets/
│   └── foto_base.png
└── fonts/
    └── README.txt
```

## Fonte manuscrita

Adicione uma fonte `.ttf` que você tenha direito de usar:

```text
fonts/handwriting.ttf
```

Sem ela, o serviço ainda funciona usando a fonte padrão do Pillow.

## Testar localmente

```bash
pip install -r requirements.txt
python test_local.py
```

Para rodar a API:

```bash
uvicorn app:app --reload --port 8000
```

Abra:

```text
http://127.0.0.1:8000
```

## Endpoints

Health check:

```http
GET /health
```

Gerar imagem:

```http
GET /generate?name=Henrique
```

Ou:

```http
POST /generate
Content-Type: application/json

{
  "name": "Henrique"
}
```

O retorno é o JPEG.

## GitHub

Envie todos os arquivos desta pasta para um repositório.

## Railway

1. New Project.
2. Deploy from GitHub repo.
3. Escolha o repositório.
4. O `Dockerfile` será detectado.
5. Aguarde o deploy.
6. Vá em Settings / Networking.
7. Gere um domínio público.
8. Abra o domínio.

A página inicial `/` já tem um campo para testar nomes.

Exemplo:

```text
https://SEU-PROJETO.up.railway.app/
```

Ou direto:

```text
https://SEU-PROJETO.up.railway.app/generate?name=Henrique
```

## API key opcional

No primeiro teste, não precisa configurar.

Depois você pode criar no Railway:

```text
API_KEY=sua-chave
```

E enviar:

```http
X-API-Key: sua-chave
```

## Calibração atual

Foto-base:

```text
1254 x 1254
```

Cantos do papel:

```python
PAPER_QUAD_REFERENCE = [
    (648, 636),
    (1153, 679),
    (1107, 1081),
    (592, 999),
]
```

Área do nome:

```python
TEXT_BOX = (45, 85, 475, 185)
```

Esses pontos já estão configurados para a foto-base incluída.

## Integração posterior

Você poderá usar diretamente:

```python
from generator import generate_jpeg_bytes

imagem = generate_jpeg_bytes(
    "Henrique"
)
```

Isso retorna o JPEG em memória, sem precisar criar arquivo temporário.
