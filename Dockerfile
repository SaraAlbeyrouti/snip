FROM python:3.11-slim AS builder

# Install C build tools. Needed when a Python package only ships source on
# PyPI for our platform and pip has to compile it. Cleaning the apt lists
# keeps this stage's intermediate layers smaller.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a fresh virtual environment at /opt/venv. We'll copy this whole
# directory into the runtime stage at the end.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Copy project metadata and source. Order matters for Docker's layer cache:
# pyproject.toml first so the deps layer can be reused when only app code
# changes. (For this small project the savings are marginal, but it's the
# right pattern for a real codebase.)
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./

# Install the package and its runtime dependencies (NOT dev deps — production
# images shouldn't ship pytest, ruff, mypy, etc.).
RUN pip install --upgrade pip \
    && pip install --no-cache-dir .


# =============================================================================
# Stage 2: runtime
# Purpose: a slim image with just the venv, the app source, and a non-root
# user. This is what actually gets deployed.
# =============================================================================
FROM python:3.11-slim AS runtime

# Create an unprivileged user. Containers should not run as root in production —
# if the app gets exploited, root inside the container is much more dangerous
# than a regular user.
RUN useradd --create-home --shell /bin/bash snip

WORKDIR /app

# Copy the venv from the builder. This is the magic of multi-stage builds:
# we get all our dependencies without inheriting the apt packages, pip cache,
# or build tools that produced them.
COPY --from=builder /opt/venv /opt/venv

# Copy app source and Alembic config. `--chown` avoids needing to chown later.
COPY --chown=snip:snip app ./app
COPY --chown=snip:snip alembic.ini ./

# Put the venv on PATH so `uvicorn` and `python` resolve to the venv binaries.
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER snip

# Document which port the app listens on. Hosting platforms like Fly.io read
# this. The actual binding happens in the CMD line below.
EXPOSE 8000

# Run the server. `--host 0.0.0.0` is required: by default uvicorn binds to
# 127.0.0.1, which means it would only accept connections from inside the
# container — useless. 0.0.0.0 binds to all interfaces.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
