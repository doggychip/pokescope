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
ARG VITE_CLERK_PUBLISHABLE_KEY=pk_test_PLACEHOLDER
ARG VITE_STRIPE_PUBLISHABLE_KEY=""
ARG VITE_API_URL=""
RUN cd frontend && npm run build

# Copy backend
COPY app/ ./app/
COPY scripts/schema.sql ./scripts/
COPY static/ ./static/

# Serve frontend static files from FastAPI
RUN cp -r frontend/dist/* static/ 2>/dev/null || true

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
