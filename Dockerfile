FROM python:3.11-slim

LABEL maintainer="API Autotest Team"
LABEL version="2.9"
LABEL description="API Automation Test Framework"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RUN_ENV=test
ENV REPORT=no
ENV PYTHONPATH=/app

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY core/ ./core/
COPY config/ ./config/
COPY utils/ ./utils/
COPY interfaces/ ./interfaces/
COPY testcases/ ./testcases/
COPY files/ ./files/
COPY lib/ ./lib/
COPY conftest.py pytest.ini run.py ./

# 创建输出目录
RUN mkdir -p outputs/report outputs/log

# 生成测试用例
RUN python -c "from core.case_generate_utils.case_fun_generate import generate_cases_for_projects; generate_cases_for_projects()" && \
    echo "Test cases generated successfully"

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

ENTRYPOINT ["python", "run.py"]
CMD ["-env", "test", "-report", "no"]
