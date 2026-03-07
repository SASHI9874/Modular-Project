FROM python:3.11-slim

WORKDIR /app

# 1. Install build dependencies (gcc, make, etc.) required for bcrypt/cryptography
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

# 2. Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

RUN python -m pip install --upgrade setuptools wheel

# Install feature requirements automatically
COPY library ./library
RUN find library -name "requirements.txt" -exec pip install -r {} \;

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]