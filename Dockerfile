FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# 1) Copy metadata only for cache deps
COPY pyproject.toml /app
COPY uv.lock       /app 

# 2) Venv
RUN uv venv .venv

# 3) Copy code and install editable
COPY src /app/src
RUN uv pip install -e /app
# Comando por defecto: ejecutar Streamlit vía uv
CMD ["uv", "run", "streamlit", "run", "src/streamlit/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
