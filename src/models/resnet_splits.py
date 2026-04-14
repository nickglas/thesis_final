"""ResNet-18 model splitting at coarse architectural boundaries.

Split points correspond to the four named residual-block stages in ResNet-18:
  layer1, layer2, layer3, layer4

Each split produces:
  PartA  – initial block (conv1/bn1/relu/maxpool) + stages up to and including split_after
  PartB  – remaining stages + avgpool + fc
"""

import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights

SPLIT_POINTS = ("layer1", "layer2", "layer3", "layer4")

# Expected intermediate tensor shapes for batch_size=1, FP32
INTERMEDIATE_SHAPES = {
    "layer1": (1, 64, 56, 56),    # 200,704 floats  ~784 KB
    "layer2": (1, 128, 28, 28),   # 100,352 floats  ~392 KB
    "layer3": (1, 256, 14, 14),   #  50,176 floats  ~196 KB
    "layer4": (1, 512, 7, 7),     #  25,088 floats  ~ 98 KB
}


def get_full_model() -> nn.Module:
    """Load pretrained ResNet-18 in eval mode on CPU."""
    model = resnet18(weights=ResNet18_Weights.DEFAULT)
    model.eval()
    return model


class PartA(nn.Module):
    """First part of ResNet-18: initial block through the named split layer."""

    def __init__(self, model: nn.Module, split_after: str):
        super().__init__()
        if split_after not in SPLIT_POINTS:
            raise ValueError(f"Invalid split point: {split_after}")
        modules = [model.conv1, model.bn1, model.relu, model.maxpool]
        for name in SPLIT_POINTS:
            modules.append(getattr(model, name))
            if name == split_after:
                break
        self.net = nn.Sequential(*modules)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class PartB(nn.Module):
    """Second part of ResNet-18: layers after the split through fc."""

    def __init__(self, model: nn.Module, split_after: str):
        super().__init__()
        if split_after not in SPLIT_POINTS:
            raise ValueError(f"Invalid split point: {split_after}")
        idx = SPLIT_POINTS.index(split_after)
        remaining = []
        for name in SPLIT_POINTS[idx + 1:]:
            remaining.append(getattr(model, name))
        self.stages = nn.Sequential(*remaining) if remaining else nn.Identity()
        self.avgpool = model.avgpool
        self.fc = model.fc

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stages(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        return x


def get_split_models(split_after: str):
    """Return (PartA, PartB) for the given split point, sharing the same pretrained weights."""
    model = get_full_model()
    part_a = PartA(model, split_after)
    part_b = PartB(model, split_after)
    part_a.eval()
    part_b.eval()
    return part_a, part_b
