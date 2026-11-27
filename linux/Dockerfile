# Same environment as linux/setup.sh, for machines where Docker is preferred.
#   docker build -f linux/Dockerfile -t tesis-linux .
#   docker run --rm tesis-linux                                   # tests + soil check
#   docker run --rm -v "$PWD:/app" tesis-linux bash linux/run_all.sh --full
FROM python:3.12.5-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY linux/requirements-linux.txt linux/requirements-linux.lock linux/
RUN python -m venv .venv-linux \
    && .venv-linux/bin/pip install -q -r linux/requirements-linux.txt -c linux/requirements-linux.lock
COPY . .
CMD ["bash", "linux/run_all.sh"]
