FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        gh \
        git \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/agentic-project-kit

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install .

RUN useradd --create-home --uid 1000 kit
USER kit

WORKDIR /work

ENTRYPOINT ["agentic-kit"]
CMD ["--help"]
