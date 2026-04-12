FROM python:3.11-slim

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Build frontend
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci

COPY frontend/ ./frontend/
ENV VITE_CLERK_PUBLISHABLE_KEY=${VITE_CLERK_PUBLISHABLE_KEY:-pk_test_dG91Y2hpbmctaGFsaWJ1dC03MS5jbGVyay5hY2NvdW50cy5kZXYk}
ENV VITE_STRIPE_PUBLISHABLE_KEY=${VITE_STRIPE_PUBLISHABLE_KEY:-}
ENV VITE_API_URL=${VITE_API_URL:-}
RUN cd frontend && npm run build

# Copy backend
COPY app/ ./app/
COPY scripts/schema.sql ./scripts/
COPY static/ ./static/

# Serve frontend static files from FastAPI
RUN cp -r frontend/dist/* static/ 2>/dev/null || true

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
