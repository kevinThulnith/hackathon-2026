FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run the Django server
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
