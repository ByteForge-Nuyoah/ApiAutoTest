FROM python:3.13-slim

LABEL maintainer="API Autotest Team"
LABEL version="2.0"
LABEL description="API Automation Test Framework"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RUN_ENV=test
ENV REPORT=no
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY core/ ./core/
COPY config/ ./config/
COPY utils/ ./utils/
COPY interfaces/ ./interfaces/
COPY testcases/ ./testcases/
COPY conftest.py pytest.ini run.py ./

RUN python -c "from core.case_generate_utils.case_fun_generate import generate_cases; generate_cases()" && \
    echo "Test cases generated successfully"

RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

RUN mkdir -p outputs/report outputs/logs

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

ENTRYPOINT ["python", "run.py"]
CMD ["-env", "test", "-report", "no"]
