"""ResNet-18 model splitting at coarse and block-level architectural boundaries.

Coarse split points correspond to the four named residual-block stages:
  layer1, layer2, layer3, layer4

Block-level split points use dot notation to target individual BasicBlocks
within a stage, e.g. "layer3.0" splits after the first BasicBlock of layer3.

Each split produces:
  PartA  – initial block (conv1/bn1/relu/maxpool) + stages/blocks up to and
           including the split point
  PartB  – remaining blocks/stages + avgpool + fc
"""

import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights

# Ordered stage names in ResNet-18
STAGE_ORDER = ("layer1", "layer2", "layer3", "layer4")

# Coarse split points (after full stages)
COARSE_SPLIT_POINTS = STAGE_ORDER

# All recognised split points (coarse + block-level)
ALL_SPLIT_POINTS = (
    "layer1", "layer2",
    "layer3.0", "layer3",
    "layer4",
)

# Backward-compatible alias used by RQ1.1 code paths
SPLIT_POINTS = COARSE_SPLIT_POINTS

# Expected intermediate tensor shapes for batch_size=1, FP32
INTERMEDIATE_SHAPES = {
    "layer1":   (1, 64, 56, 56),    # 200,704 floats  ~784 KB
    "layer2":   (1, 128, 28, 28),   # 100,352 floats  ~392 KB
    "layer3.0": (1, 256, 14, 14),   #  50,176 floats  ~196 KB
    "layer3":   (1, 256, 14, 14),   #  50,176 floats  ~196 KB
    "layer4":   (1, 512, 7, 7),     #  25,088 floats  ~ 98 KB
}


def _parse_split_point(split_after: str):
    """Parse a split point name into (stage_name, block_index_or_None).

    Examples:
        'layer2'  -> ('layer2', None)   # after full stage
        'layer3.0' -> ('layer3', 0)     # after block 0 of layer3
    """
    if "." in split_after:
        stage, block_str = split_after.rsplit(".", 1)
        return stage, int(block_str)
    return split_after, None


def get_full_model() -> nn.Module:
    """Load pretrained ResNet-18 in eval mode on CPU."""
    model = resnet18(weights=ResNet18_Weights.DEFAULT)
    model.eval()
    return model


class PartA(nn.Module):
    """First part of ResNet-18: initial block through the named split point."""

    def __init__(self, model: nn.Module, split_after: str):
        super().__init__()
        if split_after not in ALL_SPLIT_POINTS:
            raise ValueError(
                f"Invalid split point: {split_after}. "
                f"Valid: {ALL_SPLIT_POINTS}"
            )
        stage_name, block_idx = _parse_split_point(split_after)

        modules = [model.conv1, model.bn1, model.relu, model.maxpool]
        for name in STAGE_ORDER:
            stage = getattr(model, name)
            if name == stage_name:
                if block_idx is not None:
                    # Partial stage: include blocks 0..block_idx
                    for i in range(block_idx + 1):
                        modules.append(stage[i])
                else:
                    # Full stage
                    modules.append(stage)
                break
            else:
                modules.append(stage)

        self.net = nn.Sequential(*modules)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class PartB(nn.Module):
    """Second part of ResNet-18: layers after the split through fc."""

    def __init__(self, model: nn.Module, split_after: str):
        super().__init__()
        if split_after not in ALL_SPLIT_POINTS:
            raise ValueError(
                f"Invalid split point: {split_after}. "
                f"Valid: {ALL_SPLIT_POINTS}"
            )
        stage_name, block_idx = _parse_split_point(split_after)

        remaining = []
        found_stage = False
        for name in STAGE_ORDER:
            stage = getattr(model, name)
            if name == stage_name:
                if block_idx is not None:
                    # Remaining blocks from the partially-split stage
                    for i in range(block_idx + 1, len(stage)):
                        remaining.append(stage[i])
                found_stage = True
                continue
            if found_stage:
                remaining.append(stage)

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


# ---------------------------------------------------------------------------
# N-way chain segmentation for RQ1.4
# ---------------------------------------------------------------------------

class ModelSegment(nn.Module):
    """One segment of an N-way chain decomposition of ResNet-18.

    Each segment covers a contiguous slice of the network between two
    split boundaries (or from the start / to the end).

    Parameters
    ----------
    model : nn.Module
        Full pretrained ResNet-18 (used to extract submodules).
    segment_index : int
        0-based position of this segment in the chain.
    split_points : list[str]
        Ordered list of coarse split-point names that define the chain.
        For N split points, there are N+1 segments (indices 0..N).
    """

    def __init__(self, model: nn.Module, segment_index: int,
                 split_points: list):
        super().__init__()
        n_segments = len(split_points) + 1
        if segment_index < 0 or segment_index >= n_segments:
            raise ValueError(
                f"segment_index={segment_index} out of range for "
                f"{n_segments} segments (split_points={split_points})"
            )
        for sp in split_points:
            if sp not in COARSE_SPLIT_POINTS:
                raise ValueError(
                    f"Chain segmentation only supports coarse split points. "
                    f"Got '{sp}'. Valid: {COARSE_SPLIT_POINTS}"
                )

        self._segment_index = segment_index
        self._split_points = list(split_points)
        self._is_first = (segment_index == 0)
        self._is_last = (segment_index == n_segments - 1)

        # Determine which stages belong to this segment.
        # Boundaries: segment 0 starts at stem, segment N ends at tail.
        # split_points[i] means "after stage split_points[i]" is a boundary.
        #
        # Convert split points to stage indices for slicing.
        stage_indices = [STAGE_ORDER.index(sp) for sp in split_points]

        if len(split_points) == 0:
            # No splits: single segment contains the entire model.
            start_stage_idx = 0
            end_stage_idx = len(STAGE_ORDER) - 1
        elif segment_index == 0:
            start_stage_idx = 0
            end_stage_idx = stage_indices[0]  # inclusive
        elif segment_index == n_segments - 1:
            start_stage_idx = stage_indices[-1] + 1
            end_stage_idx = len(STAGE_ORDER) - 1  # inclusive
        else:
            start_stage_idx = stage_indices[segment_index - 1] + 1
            end_stage_idx = stage_indices[segment_index]  # inclusive

        # Build module list
        modules = []

        # First segment includes the stem
        if self._is_first:
            modules.extend([model.conv1, model.bn1, model.relu, model.maxpool])

        # Add the stages for this segment
        for i in range(start_stage_idx, end_stage_idx + 1):
            modules.append(getattr(model, STAGE_ORDER[i]))

        self.layers = nn.Sequential(*modules) if modules else nn.Identity()

        # Last segment includes avgpool + fc
        if self._is_last:
            self.avgpool = model.avgpool
            self.fc = model.fc
        else:
            self.avgpool = None
            self.fc = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.layers(x)
        if self._is_last:
            x = self.avgpool(x)
            x = torch.flatten(x, 1)
            x = self.fc(x)
        return x

    @property
    def segment_index(self) -> int:
        return self._segment_index

    @property
    def is_first(self) -> bool:
        return self._is_first

    @property
    def is_last(self) -> bool:
        return self._is_last


def get_chain_segments(split_points: list) -> list:
    """Return a list of ModelSegment modules for an N-way chain decomposition.

    Parameters
    ----------
    split_points : list[str]
        Ordered coarse split-point names (e.g. ["layer1", "layer3"]).
        For N split points, returns N+1 segments.
        An empty list returns a single segment containing the full model.

    Returns
    -------
    list[ModelSegment]
        Segments in chain order, all in eval mode, sharing pretrained weights.
    """
    model = get_full_model()
    n_segments = len(split_points) + 1
    segments = []
    for i in range(n_segments):
        seg = ModelSegment(model, i, split_points)
        seg.eval()
        segments.append(seg)
    return segments
