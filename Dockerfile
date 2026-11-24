FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN npm ci --prefix frontend
COPY . .
RUN npm run build

FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen && uv pip install --python .venv/bin/python waitress==3.0.2
COPY backend ./backend
COPY locales ./locales
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
ENV PYTHONUNBUFFERED=1 FLASK_DEBUG=false
WORKDIR /app/backend
EXPOSE 10000
CMD [".venv/bin/python", "lab_server.py"]
