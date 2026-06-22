FROM python:3.11-slim

LABEL maintainer="API Autotest Team"
LABEL version="3.0"
LABEL description="API Automation Test Framework"

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件并安装
COPY requirements.txt .
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
RUN mkdir -p outputs/report outputs/log outputs/mock_recordings outputs/download_files

# 生成测试用例
RUN python -c "from core.case_generate_utils.case_fun_generate import generate_cases_for_projects; generate_cases_for_projects()"

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# 入口点
ENTRYPOINT ["python", "run.py"]
CMD ["-env", "test", "-report", "no"]