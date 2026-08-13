"""
EvOLve — model/classifier.py
Degradation classifier fine-tuned on top of the pretrained encoder.

Two modes:
  1. frozen_encoder  — encoder weights frozen, only head trained (few-shot)
  2. full_finetune   — entire model trained end-to-end

Output: degradation_score (0.0–1.0) per patch
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DegradationClassifier(nn.Module):
    """
    Fine-tuning head on top of EvOLveEncoder.

    encoder        : pretrained EvOLveEncoder
    freeze_encoder : if True, encoder weights are frozen
    """

    def __init__(self, encoder, freeze_encoder: bool = True, dropout: float = 0.3):
        super().__init__()
        self.encoder = encoder
        self.freeze_encoder = freeze_encoder

        if freeze_encoder:
            for param in self.encoder.parameters():
                param.requires_grad = False

        D = encoder.embed_dim

        # Classification head: summary embedding → degradation score
        self.head = nn.Sequential(
            nn.Linear(D, D // 2),
            nn.LayerNorm(D // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(D // 2, D // 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(D // 4, 1),     # single logit → sigmoid → score
        )

        # Temporal attention pooling (learnable weighting of time steps)
        self.time_attn = nn.Linear(D, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (B, T, 8, 64, 64)
        Returns: (B,) — degradation score in [0, 1]
        """
        if self.freeze_encoder:
            with torch.no_grad():
                z = self.encoder(x)     # (B, T, D)
        else:
            z = self.encoder(x)         # (B, T, D)

        # Attention-weighted temporal pooling
        attn_weights = F.softmax(self.time_attn(z), dim=1)   # (B, T, 1)
        summary = (z * attn_weights).sum(dim=1)               # (B, D)

        logit = self.head(summary).squeeze(-1)                # (B,)
        score = torch.sigmoid(logit)                          # (B,) in [0,1]
        return score

    def predict(self, x: torch.Tensor, threshold: float = 0.5):
        """
        Returns (score, binary_prediction).
        x: (B, T, 8, 64, 64) or (T, 8, 64, 64) for single patch
        """
        if x.dim() == 4:
            x = x.unsqueeze(0)
        score = self.forward(x)
        pred  = (score >= threshold).long()
        return score, pred


class SupervisedBaseline(nn.Module):
    """
    Supervised-only baseline: same architecture but trained from scratch.
    Used for comparison — EvOLve (pretrained) should outperform this.
    """

    def __init__(self, in_channels=8, embed_dim=128, nhead=4,
                 num_layers=4, dim_feedforward=256, dropout=0.3):
        super().__init__()
        from model.encoder import EvOLveEncoder
        self.encoder = EvOLveEncoder(
            in_channels=in_channels,
            embed_dim=embed_dim,
            nhead=nhead,
            num_layers=num_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
        )
        D = embed_dim
        self.head = nn.Sequential(
            nn.Linear(D, D // 2), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(D // 2, 1),
        )
        self.time_attn = nn.Linear(D, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z            = self.encoder(x)
        attn_weights = F.softmax(self.time_attn(z), dim=1)
        summary      = (z * attn_weights).sum(dim=1)
        return torch.sigmoid(self.head(summary).squeeze(-1))
