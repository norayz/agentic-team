# Single image for the orchestrator and all 7 agents.
# Built from the repo root so the agents/, tools/, and orchestrator/ packages
# are all importable. Each service in docker-compose.yml overrides `command`.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
