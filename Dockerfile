FROM python:3.13-slim

ARG ALLURE_VERSION=3.3.1
ARG INSTALL_JAVA=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Jenkins will mount the host project into /app at runtime.
# This image only prepares the execution environment.
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    if [ "$INSTALL_JAVA" = "true" ]; then \
      apt-get install -y --no-install-recommends openjdk-17-jre-headless; \
    fi && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    npm install -g allure@${ALLURE_VERSION} && \
    allure --version && \
    pytest --version && \
    playwright --version && \
    playwright install --with-deps chromium && \
    python -c "import importlib.metadata as m; pkgs=['playwright','pytest','allure-pytest','allure-python-commons','pyyaml']; print('Installed package versions:'); [print(f'{p}=={m.version(p)}') for p in pkgs]"
