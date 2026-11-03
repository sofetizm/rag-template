FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 HF_HOME=/models
WORKDIR /app

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Dependencies change rarely: install them from a stub package so code edits keep this layer cached.
COPY pyproject.toml README.md ./
RUN mkdir -p src/rag_template && touch src/rag_template/__init__.py && pip install ".[ml]" && pip uninstall -y rag-template

ARG EMBEDDING_MODEL=intfloat/multilingual-e5-small
ARG RERANKER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('${EMBEDDING_MODEL}'); CrossEncoder('${RERANKER_MODEL}')"

COPY src ./src
RUN pip install --no-deps .
COPY data ./data

RUN useradd --create-home app && mkdir -p /app/logs && chown -R app /app /models
USER app
ENV HF_HUB_OFFLINE=1 RAG_EMBEDDING_MODEL=${EMBEDDING_MODEL} RAG_RERANKER_MODEL=${RERANKER_MODEL}
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=300s --retries=12 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)"
CMD ["rag", "serve", "--host", "0.0.0.0", "--port", "8000"]
