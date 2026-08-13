"""
EvOLve — model/pretrain.py
Self-supervised pretraining loss: MTAE reconstruction + contrastive.

Loss = λ_recon × ReconstructionLoss + λ_contrast × ContrastiveLoss

Reconstruction Loss:
  MSE between predicted and actual pixel values at MASKED positions only.

Contrastive Loss (SimCLR-style):
  Two random augmentations of the same patch = positive pair.
  Different patches = negative pairs.
  NT-Xent (InfoNCE) loss on mean-pooled embeddings.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# ── Reconstruction Loss (masked MSE) ──────────────────────────────────────────

class MaskedReconstructionLoss(nn.Module):
    """
    MSE only on the time steps that were masked.
    mask: (B, T) — 1 = was masked, 0 = was visible
    """

    def forward(
        self,
        recon: torch.Tensor,   # (B, T, 8, 64, 64) — reconstructed
        target: torch.Tensor,  # (B, T, 8, 64, 64) — original
        mask: torch.Tensor,    # (B, T)
    ) -> torch.Tensor:
        # Expand mask to match image dims: (B, T, 1, 1, 1) → (B, T, 8, 64, 64)
        mask_exp = mask.unsqueeze(-1).unsqueeze(-1).unsqueeze(-1)
        mask_exp = mask_exp.expand_as(recon)

        diff = (recon - target) ** 2
        masked_mse = (diff * mask_exp).sum() / (mask_exp.sum() + 1e-8)
        return masked_mse


# ── NT-Xent Contrastive Loss ───────────────────────────────────────────────────

class NTXentLoss(nn.Module):
    """
    NT-Xent (Normalized Temperature-scaled Cross Entropy) loss.
    Used in SimCLR. Maximizes agreement between two views of the same patch.

    z1, z2 : (B, D) — embeddings from two augmented views of same patch
    temperature: lower = sharper distribution (harder negatives)
    """

    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, z1: torch.Tensor, z2: torch.Tensor) -> torch.Tensor:
        B = z1.size(0)

        # L2 normalize
        z1 = F.normalize(z1, dim=1)
        z2 = F.normalize(z2, dim=1)

        # Concatenate all representations: (2B, D)
        z = torch.cat([z1, z2], dim=0)

        # Similarity matrix: (2B, 2B)
        sim = torch.matmul(z, z.T) / self.temperature

        # Mask self-similarities
        eye_mask = torch.eye(2 * B, device=z.device, dtype=torch.bool)
        sim = sim.masked_fill(eye_mask, -1e9)

        # Positive pairs: (i, i+B) and (i+B, i)
        labels = torch.arange(B, device=z.device)
        labels = torch.cat([labels + B, labels])   # (2B,)

        loss = F.cross_entropy(sim, labels)
        return loss


# ── Temporal Augmentation for Contrastive Views ────────────────────────────────

def temporal_augment(patch: torch.Tensor, drop_ratio: float = 0.2) -> torch.Tensor:
    """
    Create an augmented view of a patch time series by:
    1. Random temporal dropout (drop ~20% of months → set to 0)
    2. Gaussian noise injection
    patch: (B, T, 8, 64, 64)
    """
    B, T, C, H, W = patch.shape
    aug = patch.clone()

    # Random temporal dropout
    n_drop = max(1, int(T * drop_ratio))
    drop_idx = torch.randint(0, T, (n_drop,))
    aug[:, drop_idx] = 0.0

    # Gaussian noise
    noise = torch.randn_like(aug) * 0.02
    aug = aug + noise

    return aug


# ── Combined Pretraining Loss ──────────────────────────────────────────────────

class PretrainingLoss(nn.Module):
    """
    Combined MTAE reconstruction + contrastive loss.

    lambda_recon   : weight for reconstruction loss
    lambda_contrast: weight for contrastive loss
    temperature    : NT-Xent temperature
    """

    def __init__(
        self,
        lambda_recon: float = 1.0,
        lambda_contrast: float = 0.5,
        temperature: float = 0.07,
    ):
        super().__init__()
        self.lambda_recon    = lambda_recon
        self.lambda_contrast = lambda_contrast
        self.recon_loss      = MaskedReconstructionLoss()
        self.contrast_loss   = NTXentLoss(temperature)

    def forward(
        self,
        recon: torch.Tensor,    # (B, T, 8, 64, 64)
        target: torch.Tensor,   # (B, T, 8, 64, 64)
        mask: torch.Tensor,     # (B, T)
        z: torch.Tensor,        # (B, T, D) — encoder embeddings
    ) -> dict:
        # Reconstruction loss
        loss_recon = self.recon_loss(recon, target, mask)

        # Contrastive loss: create two augmented views, pool embeddings
        B, T, D = z.shape

        # Use mean-pooled z as summary vector (approximation)
        z1 = z.mean(dim=1)                             # (B, D)
        # Second view summary: add noise in embedding space
        z2 = z1 + torch.randn_like(z1) * 0.1          # (B, D)

        loss_contrast = self.contrast_loss(z1, z2)

        total = self.lambda_recon * loss_recon + self.lambda_contrast * loss_contrast

        return {
            'total':     total,
            'recon':     loss_recon,
            'contrast':  loss_contrast,
        }
