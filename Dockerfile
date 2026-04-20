FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project sources
COPY proto/ proto/
COPY src/ src/
COPY configs/ configs/
COPY run_k8s_experiment.py .
COPY run_analysis.py .

# Default entrypoint runs the chain service; override with pod args
ENTRYPOINT ["python", "-m", "src.services.chain_service_runner"]
