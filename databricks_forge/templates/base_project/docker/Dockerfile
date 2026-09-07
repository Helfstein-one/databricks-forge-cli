# docker/Dockerfile - Local Lakehouse development & test container
FROM python:3.11-slim-bullseye

LABEL maintainer="{{author_name}} <{{author_email}}>"
LABEL description="Container environment for {{project_name}} running PySpark 3.5 and Delta Lake 3.0"

# Install OpenJDK 11 and foundational build utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Prevent PySpark from attempting to connect to external driver IPs
ENV SPARK_LOCAL_IP="127.0.0.1"
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

WORKDIR /app

# Cache dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
      build \
      pytest \
      pytest-benchmark \
      pytest-mock \
      chispa \
      ruff \
      typer \
      pyyaml \
      pyspark==3.5.0 \
      delta-spark==3.0.0 \
      "databricks-connect>=14.0.0,<15.0.0"

# Copy source code and install project in editable mode
COPY . .
RUN pip install --no-cache-dir -e .

# Default test command
CMD ["pytest", "tests/unit/", "-v"]
