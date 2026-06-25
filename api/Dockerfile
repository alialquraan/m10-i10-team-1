# Build context: repo root (parent of api/).
# In docker-compose.yml:  build: { context: ., dockerfile: api/Dockerfile }
#
# This preserves package-relative imports (api/main.py: from .deps import ...).
# Running `uvicorn api.main:app` from /app loads the `api` package; running
# `uvicorn main:app` from /app/api would break the relative imports with
# `ImportError: attempted relative import with no known parent package`.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY api/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --timeout 300 --retries 5 -r /app/requirements.txt

RUN pip install --no-cache-dir --timeout 300 --retries 5 \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

COPY api/ /app/api/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]