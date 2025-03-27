FROM python:3.11.6-slim-bookworm AS base

# Install dependencies
RUN apt-get update && \
    apt-get install -y sudo && \
    rm -rf /var/lib/apt/lists/*

# Enable in-project virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

FROM base AS dependencies
WORKDIR /home/worker/app
COPY pyproject.toml poetry.lock ./

# Install dependencies using pip
RUN pip install --no-cache-dir -r <(poetry export --format=requirements.txt --without-hashes)

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
RUN adduser --system --gid ${GID} --uid ${UID} --home /home/worker worker && \
    echo "worker ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chmod 0440 /etc/sudoers

WORKDIR /home/worker/app
RUN chown worker /home/worker/app
RUN mkdir local_data && chown worker local_data
RUN mkdir models && chown worker models
RUN mkdir -p /home/worker/app/local_data/bridgewell_gpt/templates

# Copy files with correct ownership
COPY templates/benefit_comparison_template.xlsx /home/worker/app/local_data/bridgewell_gpt/templates/
COPY --chown=worker --from=dependencies /opt/venv/ /opt/venv/
COPY --chown=worker bridgewell_gpt/ bridgewell_gpt
COPY --chown=worker *.yaml .
COPY --chown=worker scripts/ scripts

USER worker
ENTRYPOINT ["python", "-m", "bridgewell_gpt"]