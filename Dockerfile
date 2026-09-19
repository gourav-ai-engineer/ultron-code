FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY web ./web
COPY docs ./docs

RUN pip install --no-cache-dir -e ".[api]"

ENV ULTRON_API_HOST=0.0.0.0
ENV ULTRON_API_PORT=8765
ENV ULTRON_DRY_RUN=true

EXPOSE 8765

CMD ["python", "-c", "from ultron.api import create_app; import uvicorn; uvicorn.run(create_app(), host='0.0.0.0', port=8765)"]
