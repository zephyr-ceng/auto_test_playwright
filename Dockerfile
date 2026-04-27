FROM python:3.13-slim

ARG ALLURE_VERSION=3.3.1
ARG INSTALL_JAVA=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Allure Report 3 uses Node.js (not Java). Keep Java optional for compatibility.
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    if [ "$INSTALL_JAVA" = "true" ]; then \
      apt-get install -y --no-install-recommends openjdk-17-jre-headless; \
    fi && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    npm install -g allure@${ALLURE_VERSION} && \
    allure --version && \
    playwright install --with-deps chromium

COPY . .

CMD ["python", "run_tests.py"]
