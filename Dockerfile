# ============================================================
# Ombre Brain Docker Build
# Docker 构建文件
#
# Build: docker build -t ombre-brain .
# Run:   docker run -e OMBRE_API_KEY=your-key -p 8000:8000 ombre-brain
# ============================================================

FROM python:3.12-slim

WORKDIR /app

# Install dependencies
# 安装依赖
ARG CACHEBUST=1
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy project files / 复制项目文件
COPY *.py .
COPY resources ./resources
COPY scripts ./scripts
COPY dashboard.html .
COPY dashboard_assets ./dashboard_assets
COPY public ./public
COPY config.example.yaml ./config.yaml
RUN chmod +x scripts/*.sh

# Persistent mount point: bucket data
# 持久化挂载点：记忆数据
VOLUME ["/app/buckets"]

# Default to streamable-http for container (remote access)
# 容器场景默认用 streamable-http
ENV OMBRE_TRANSPORT=streamable-http
ENV OMBRE_BUCKETS_DIR=/app/buckets
ENV OMBRE_STATE_DIR=/app/state

# server.py: 8000 (MCP + Dashboard)
# gateway.py: 8010 (OpenAI-compatible Gateway)
EXPOSE 8000 8010

COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
