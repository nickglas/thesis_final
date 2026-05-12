FROM python:3.10-slim

WORKDIR /app
ENV TORCH_HOME=/opt/torch-cache
ARG TORCH_VERSION=2.11.0
ARG TORCHVISION_VERSION=0.26.0

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
	"torch==${TORCH_VERSION}+cpu" \
	"torchvision==${TORCHVISION_VERSION}+cpu" \
	&& grep -vE '^(torch|torchvision)([<>=!~].*)?$' requirements.txt > /tmp/requirements.container.txt \
	&& pip install --no-cache-dir -r /tmp/requirements.container.txt \
	&& rm /tmp/requirements.container.txt

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
