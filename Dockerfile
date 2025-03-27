FROM python:3.11.6-slim-bookworm AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN rm -f /usr/local/bin/poetry && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    mv /root/.local/bin/poetry /usr/local/bin/poetry && \
    chmod +x /usr/local/bin/poetry
ENV PATH="/usr/local/bin:$PATH"
ENV PATH=".venv/bin/:$PATH"

# Enable in-project virtual environment
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

FROM base AS dependencies
WORKDIR /home/worker/app
COPY pyproject.toml poetry.lock ./

ARG POETRY_EXTRAS="ui vector-stores-qdrant llms-openai embeddings-openai rerank-sentence-transformers"
RUN poetry install --no-root --extras "${POETRY_EXTRAS}"

FROM base AS app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV APP_ENV=prod
ENV PYTHONPATH="$PYTHONPATH:/home/worker/app/bridgewell_gpt/"
ENV PGPT_PROFILES=openai
EXPOSE 8080

# Create a non-root user
ARG UID=100
ARG GID=65534
RUN adduser --system --gid ${GID} --uid ${UID} --home /home/worker worker

WORKDIR /home/worker/app
RUN chown worker /home/worker/app
RUN mkdir local_data && chown worker local_data
RUN mkdir models && chown worker models
RUN mkdir -p /home/worker/app/local_data/bridgewell_gpt/templates

# Copy files with correct ownership
COPY templates/benefit_comparison_template.xlsx /home/worker/app/local_data/bridgewell_gpt/templates/
COPY --chown=worker --from=dependencies /home/worker/app/.venv/ .venv
COPY --chown=worker bridgewell_gpt/ bridgewell_gpt
COPY --chown=worker *.yaml .
COPY --chown=worker scripts/ scripts

USER worker
ENTRYPOINT ["python", "-m", "bridgewell_gpt"]