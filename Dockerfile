# Multi-stage, non-root, slim. The hardening is baked in so you don't have to
# think about it — this is the point of the kit.

# ---- build stage: install deps into a venv ----
FROM python:3.12-slim AS build

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# Deps first so the layer caches until requirements change.
COPY app/requirements.txt ./
RUN python -m venv /venv && /venv/bin/pip install -r requirements.txt

COPY app/ ./

# ---- runtime stage: slim, non-root, no build tooling ----
FROM python:3.12-slim AS runtime

# Create an unprivileged user to run as.
RUN groupadd --gid 65532 nonroot \
    && useradd --uid 65532 --gid 65532 --no-create-home --shell /usr/sbin/nologin nonroot

ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY --from=build /venv /venv
COPY --from=build /app /app

USER 65532:65532
EXPOSE 8080

# Probes are driven by Kubernetes (see deploy/); no shell healthcheck needed.
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
