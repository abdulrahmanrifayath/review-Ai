FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (build-essential, git, Node.js, OpenJDK JRE)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install JS/TS static linter dependencies
RUN npm install -g eslint@8.57.0 @typescript-eslint/parser@7.10.0 @typescript-eslint/eslint-plugin@7.10.0


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
