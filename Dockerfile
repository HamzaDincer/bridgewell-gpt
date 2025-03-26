FROM python:3.11.6-slim-bookworm AS base

FROM base AS dependencies
WORKDIR /home/worker/app
COPY pyproject.toml poetry.lock ./

# Install Poetry in dependencies stage
RUN pip install pipx
RUN python3 -m pipx ensurepath
RUN pipx install poetry==1.8.3
ENV PATH="/root/.local/bin:$PATH"
ENV PATH=".venv/bin/:$PATH"

# Enable in-project virtual environment
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

ARG POETRY_EXTRAS="ui vector-stores-qdrant llms-openai embeddings-openai rerank-sentence-transformers"
RUN poetry install --no-root --extras "${POETRY_EXTRAS}"

FROM base AS app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV APP_ENV=prod
ENV PYTHONPATH="$PYTHONPATH:/home/worker/app/private_gpt/"
EXPOSE 8080

# Install Poetry in final stage
RUN pip install pipx
RUN python3 -m pipx ensurepath
RUN pipx install poetry==1.8.3
ENV PATH="/root/.local/bin:$PATH"
ENV PATH=".venv/bin/:$PATH"

# Create a non-root user
ARG UID=100
ARG GID=65534
RUN adduser --system --gid ${GID} --uid ${UID} --home /home/worker worker

WORKDIR /home/worker/app
RUN chown worker /home/worker/app
RUN mkdir local_data && chown worker local_data
RUN mkdir models && chown worker models
RUN mkdir -p /home/worker/app/local_data/private_gpt/templates

# Fix permissions for poetry
RUN chmod -R 755 /root/.local/bin/poetry
RUN chmod -R 755 /root/.local
RUN ln -sf /root/.local/bin/poetry /usr/local/bin/poetry

COPY templates/benefit_comparison_template.xlsx /home/worker/app/local_data/private_gpt/templates/
COPY --chown=worker --from=dependencies /home/worker/app/.venv/ .venv
COPY --chown=worker private_gpt/ private_gpt
COPY --chown=worker *.yaml .
COPY --chown=worker scripts/ scripts

USER worker
ENTRYPOINT ["poetry", "run", "python", "-m", "private_gpt"]