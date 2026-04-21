FROM python:3.10-slim

WORKDIR /app
ENV TORCH_HOME=/opt/torch-cache

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Prefetch the pretrained ResNet-18 weights so benchmark pods do not need
# to download them during startup or parity validation.
RUN python - <<'PY'
from torchvision.models import ResNet18_Weights, resnet18

resnet18(weights=ResNet18_Weights.DEFAULT)
PY

# Copy project sources
COPY proto/ proto/
COPY src/ src/
COPY configs/ configs/
COPY run_k8s_experiment.py .
COPY run_analysis.py .

# Default entrypoint runs the chain service; override with pod args
ENTRYPOINT ["python", "-m", "src.services.chain_service_runner"]
