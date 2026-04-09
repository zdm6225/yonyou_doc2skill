# Docker Deployment Guide

Complete guide for deploying Yonyou Doc2Skill using Docker.

## Table of Contents

- [Quick Start](#quick-start)
- [Building Images](#building-images)
- [Running Containers](#running-containers)
- [Docker Compose](#docker-compose)
- [Configuration](#configuration)
- [Data Persistence](#data-persistence)
- [Networking](#networking)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Single Container Deployment

```bash
# Pull pre-built image (when available)
docker pull yonyoudoc2skill/yonyoudoc2skill:latest

# Or build locally
docker build -t yonyoudoc2skill:latest .

# Run MCP server
docker run -d \
  --name yonyoudoc2skill-mcp \
  -p 8765:8765 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -v yonyoudoc2skill-data:/app/data \
  --restart unless-stopped \
  yonyoudoc2skill:latest
```

### Multi-Service Deployment

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Building Images

### 1. Production Image

The Dockerfile uses multi-stage builds for optimization:

```dockerfile
# Build stage
FROM python:3.12-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "yonyou_doc2skill.mcp.server_fastmcp"]
```

**Build the image:**

```bash
# Standard build
docker build -t yonyoudoc2skill:latest .

# Build with specific features
docker build \
  --build-arg INSTALL_EXTRAS="all-llms,embedding" \
  -t yonyoudoc2skill:full \
  .

# Build with cache
docker build \
  --cache-from yonyoudoc2skill:latest \
  -t yonyoudoc2skill:v2.9.0 \
  .
```

### 2. Development Image

```dockerfile
# Dockerfile.dev
FROM python:3.12
WORKDIR /app
RUN pip install -e ".[dev]"
COPY . .
CMD ["python", "-m", "yonyou_doc2skill.mcp.server_fastmcp", "--reload"]
```

**Build and run:**

```bash
docker build -f Dockerfile.dev -t yonyoudoc2skill:dev .

docker run -it \
  --name yonyoudoc2skill-dev \
  -p 8765:8765 \
  -v $(pwd):/app \
  yonyoudoc2skill:dev
```

### 3. Image Optimization

**Reduce image size:**

```bash
# Multi-stage build
FROM python:3.12-slim as builder
...
FROM python:3.12-alpine  # Smaller base

# Remove build dependencies
RUN pip install --no-cache-dir ... && \
    rm -rf /root/.cache

# Use .dockerignore
echo ".git" >> .dockerignore
echo "tests/" >> .dockerignore
echo "*.pyc" >> .dockerignore
```

**Layer caching:**

```dockerfile
# Copy requirements first (changes less frequently)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code later (changes more frequently)
COPY . .
```

## Running Containers

### 1. MCP Server

```bash
# HTTP transport (recommended for production)
docker run -d \
  --name yonyoudoc2skill-mcp \
  -p 8765:8765 \
  -e MCP_TRANSPORT=http \
  -e MCP_PORT=8765 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v yonyoudoc2skill-data:/app/data \
  --restart unless-stopped \
  yonyoudoc2skill:latest

# stdio transport (for local tools)
docker run -it \
  --name yonyoudoc2skill-stdio \
  -e MCP_TRANSPORT=stdio \
  yonyoudoc2skill:latest
```

### 2. Embedding Server

```bash
docker run -d \
  --name yonyoudoc2skill-embed \
  -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e VOYAGE_API_KEY=$VOYAGE_API_KEY \
  -v yonyoudoc2skill-cache:/app/cache \
  --restart unless-stopped \
  yonyoudoc2skill:latest \
  python -m yonyou_doc2skill.embedding.server --host 0.0.0.0 --port 8000
```

### 3. Sync Monitor

```bash
docker run -d \
  --name yonyoudoc2skill-sync \
  -e SYNC_WEBHOOK_URL=$SYNC_WEBHOOK_URL \
  -v yonyoudoc2skill-configs:/app/configs \
  --restart unless-stopped \
  yonyoudoc2skill:latest \
  yonyou-doc2skill-sync start --config configs/react.json
```

### 4. Interactive Commands

```bash
# Run scraping
docker run --rm \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -v $(pwd)/output:/app/output \
  yonyoudoc2skill:latest \
  yonyou-doc2skill scrape --config configs/react.json

# Generate skill
docker run --rm \
  -v $(pwd)/output:/app/output \
  yonyoudoc2skill:latest \
  yonyou-doc2skill package output/react/

# Interactive shell
docker run --rm -it \
  yonyoudoc2skill:latest \
  /bin/bash
```

## Docker Compose

### 1. Basic Setup

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  mcp-server:
    image: yonyoudoc2skill:latest
    container_name: yonyoudoc2skill-mcp
    ports:
      - "8765:8765"
    environment:
      - MCP_TRANSPORT=http
      - MCP_PORT=8765
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - yonyoudoc2skill-data:/app/data
      - yonyoudoc2skill-logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8765/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  embedding-server:
    image: yonyoudoc2skill:latest
    container_name: yonyoudoc2skill-embed
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - VOYAGE_API_KEY=${VOYAGE_API_KEY}
    volumes:
      - yonyoudoc2skill-cache:/app/cache
    command: ["python", "-m", "yonyou_doc2skill.embedding.server", "--host", "0.0.0.0"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s

  nginx:
    image: nginx:alpine
    container_name: yonyoudoc2skill-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - mcp-server
      - embedding-server
    restart: unless-stopped

volumes:
  yonyoudoc2skill-data:
  yonyoudoc2skill-logs:
  yonyoudoc2skill-cache:
```

### 2. With Monitoring Stack

**docker-compose.monitoring.yml:**

```yaml
version: '3.8'

services:
  # ... (previous services)

  prometheus:
    image: prom/prometheus:latest
    container_name: yonyoudoc2skill-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: yonyoudoc2skill-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    container_name: yonyoudoc2skill-loki
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
  loki-data:
```

### 3. Commands

```bash
# Start services
docker-compose up -d

# Start with monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f mcp-server

# Scale services
docker-compose up -d --scale mcp-server=3

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Configuration

### 1. Environment Variables

**Using .env file:**

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
OPENAI_API_KEY=sk-...
VOYAGE_API_KEY=...
LOG_LEVEL=INFO
MCP_PORT=8765
```

**Load in docker-compose:**

```yaml
services:
  mcp-server:
    env_file:
      - .env
```

### 2. Config Files

**Mount configuration:**

```bash
docker run -d \
  -v $(pwd)/configs:/app/configs:ro \
  yonyoudoc2skill:latest
```

**docker-compose.yml:**

```yaml
services:
  mcp-server:
    volumes:
      - ./configs:/app/configs:ro
```

### 3. Secrets Management

**Docker Secrets (Swarm mode):**

```bash
# Create secrets
echo $ANTHROPIC_API_KEY | docker secret create anthropic_key -
echo $GITHUB_TOKEN | docker secret create github_token -

# Use in service
docker service create \
  --name yonyoudoc2skill-mcp \
  --secret anthropic_key \
  --secret github_token \
  yonyoudoc2skill:latest
```

**docker-compose.yml (Swarm):**

```yaml
version: '3.8'

secrets:
  anthropic_key:
    external: true
  github_token:
    external: true

services:
  mcp-server:
    secrets:
      - anthropic_key
      - github_token
    environment:
      - ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_key
```

## Data Persistence

### 1. Named Volumes

```bash
# Create volume
docker volume create yonyoudoc2skill-data

# Use in container
docker run -v yonyoudoc2skill-data:/app/data yonyoudoc2skill:latest

# Backup volume
docker run --rm \
  -v yonyoudoc2skill-data:/data \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/backup.tar.gz /data

# Restore volume
docker run --rm \
  -v yonyoudoc2skill-data:/data \
  -v $(pwd):/backup \
  alpine \
  sh -c "cd /data && tar xzf /backup/backup.tar.gz --strip 1"
```

### 2. Bind Mounts

```bash
# Mount host directory
docker run -v /opt/yonyoudoc2skill/output:/app/output yonyoudoc2skill:latest

# Read-only mount
docker run -v $(pwd)/configs:/app/configs:ro yonyoudoc2skill:latest
```

### 3. Data Migration

```bash
# Export from container
docker cp yonyoudoc2skill-mcp:/app/data ./data-backup

# Import to new container
docker cp ./data-backup new-container:/app/data
```

## Networking

### 1. Bridge Network (Default)

```bash
# Containers can communicate by name
docker network create yonyoudoc2skill-net

docker run --network yonyoudoc2skill-net yonyoudoc2skill:latest
```

### 2. Host Network

```bash
# Use host network stack
docker run --network host yonyoudoc2skill:latest
```

### 3. Custom Network

**docker-compose.yml:**

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  nginx:
    networks:
      - frontend

  mcp-server:
    networks:
      - frontend
      - backend

  database:
    networks:
      - backend
```

## Monitoring

### 1. Health Checks

```yaml
services:
  mcp-server:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8765/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 2. Resource Limits

```yaml
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 3. Logging

```yaml
services:
  mcp-server:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=mcp"

    # Or use syslog
    logging:
      driver: "syslog"
      options:
        syslog-address: "udp://192.168.1.100:514"
```

### 4. Metrics

```bash
# Docker stats
docker stats yonyoudoc2skill-mcp

# cAdvisor for metrics
docker run -d \
  --name cadvisor \
  -p 8080:8080 \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:ro \
  -v /sys:/sys:ro \
  -v /var/lib/docker:/var/lib/docker:ro \
  gcr.io/cadvisor/cadvisor:latest
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker logs yonyoudoc2skill-mcp

# Inspect container
docker inspect yonyoudoc2skill-mcp

# Run with interactive shell
docker run -it --entrypoint /bin/bash yonyoudoc2skill:latest
```

#### 2. Port Already in Use

```bash
# Find process using port
sudo lsof -i :8765

# Kill process
kill -9 <PID>

# Or use different port
docker run -p 8766:8765 yonyoudoc2skill:latest
```

#### 3. Volume Permission Issues

```bash
# Run as specific user
docker run --user $(id -u):$(id -g) yonyoudoc2skill:latest

# Fix permissions
docker run --rm \
  -v yonyoudoc2skill-data:/data \
  alpine chown -R 1000:1000 /data
```

#### 4. Network Connectivity

```bash
# Test connectivity
docker exec yonyoudoc2skill-mcp ping google.com

# Check DNS
docker exec yonyoudoc2skill-mcp cat /etc/resolv.conf

# Use custom DNS
docker run --dns 8.8.8.8 yonyoudoc2skill:latest
```

#### 5. High Memory Usage

```bash
# Set memory limit
docker run --memory=4g yonyoudoc2skill:latest

# Check memory usage
docker stats yonyoudoc2skill-mcp

# Enable memory swappiness
docker run --memory=4g --memory-swap=8g yonyoudoc2skill:latest
```

### Debug Commands

```bash
# Enter running container
docker exec -it yonyoudoc2skill-mcp /bin/bash

# View environment variables
docker exec yonyoudoc2skill-mcp env

# Check processes
docker exec yonyoudoc2skill-mcp ps aux

# View logs in real-time
docker logs -f --tail 100 yonyoudoc2skill-mcp

# Inspect container details
docker inspect yonyoudoc2skill-mcp | jq '.[]'

# Export container filesystem
docker export yonyoudoc2skill-mcp > container.tar
```

## Production Best Practices

### 1. Image Management

```bash
# Tag images with versions
docker build -t yonyoudoc2skill:2.9.0 .
docker tag yonyoudoc2skill:2.9.0 yonyoudoc2skill:latest

# Use private registry
docker tag yonyoudoc2skill:latest registry.example.com/yonyoudoc2skill:latest
docker push registry.example.com/yonyoudoc2skill:latest

# Scan for vulnerabilities
docker scan yonyoudoc2skill:latest
```

### 2. Security

```bash
# Run as non-root user
RUN useradd -m -s /bin/bash yonyoudoc2skill
USER yonyoudoc2skill

# Read-only root filesystem
docker run --read-only --tmpfs /tmp yonyoudoc2skill:latest

# Drop capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE yonyoudoc2skill:latest

# Use security scanning
trivy image yonyoudoc2skill:latest
```

### 3. Resource Management

```yaml
services:
  mcp-server:
    # CPU limits
    cpus: 2.0
    cpu_shares: 1024

    # Memory limits
    mem_limit: 4g
    memswap_limit: 8g
    mem_reservation: 2g

    # Process limits
    pids_limit: 200
```

### 4. Backup & Recovery

```bash
# Backup script
#!/bin/bash
docker-compose down
tar czf backup-$(date +%Y%m%d).tar.gz volumes/
docker-compose up -d

# Automated backups
0 2 * * * /opt/yonyoudoc2skill/backup.sh
```

## Next Steps

- See [KUBERNETES_DEPLOYMENT.md](./KUBERNETES_DEPLOYMENT.md) for Kubernetes deployment
- Review [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) for general production guidelines
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues

---

**Need help?** Open an issue on [GitHub](https://github.com/yonyou/yonyou-doc2skill/issues).
