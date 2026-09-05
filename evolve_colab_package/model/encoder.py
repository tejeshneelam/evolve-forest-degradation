"""
EvOLve — model/encoder.py
Spatial CNN encoder + Temporal Transformer backbone.

Architecture:
  Input  : (B, T, 8, 64, 64)            — batch × time × bands × H × W
  Stage 1: Per-timestep CNN → (B, T, D)  — spatial feature extraction
  Stage 2: Temporal Transformer          — learns inter-month relationships
  Output : (B, T, D)                     — contextual temporal embeddings

Also includes the MTAE decoder for reconstruction.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


# ── Spatial CNN Encoder (per time step) ───────────────────────────────────────

class SpatialEncoder(nn.Module):
    """
    Lightweight CNN that maps one month's (8, 64, 64) image → embedding of size D.
    Applied independently to each time step via vmap / loop.
    """

    def __init__(self, in_channels: int = 8, embed_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            # 64→32
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.GELU(),
            nn.MaxPool2d(2),

            # 32→16
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.GELU(),
            nn.MaxPool2d(2),

            # 16→8
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.GELU(),
            nn.MaxPool2d(2),

            # 8→4
            nn.Conv2d(128, embed_dim, 3, padding=1),
            nn.BatchNorm2d(embed_dim),
            nn.GELU(),
            nn.AdaptiveAvgPool2d(1),   # → (B, embed_dim, 1, 1)
        )
        self.embed_dim = embed_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, C, H, W) → (B, D)"""
        return self.net(x).squeeze(-1).squeeze(-1)


# ── Positional Encoding (sinusoidal, for Transformer) ─────────────────────────

class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 200, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer('pe', pe.unsqueeze(0))   # (1, max_len, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, T, D)"""
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


# ── Temporal Transformer Encoder ──────────────────────────────────────────────

class TemporalTransformer(nn.Module):
    """
    Standard Transformer encoder operating on the time dimension.
    Input:  (B, T, D)
    Output: (B, T, D)  — each timestep has context from all others
    """

    def __init__(
        self,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 4,
        dim_feedforward: int = 256,
        dropout: float = 0.1,
        max_len: int = 200,
    ):
        super().__init__()
        self.pos_enc = SinusoidalPositionalEncoding(d_model, max_len, dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,   # (B, T, D) convention
            norm_first=True,    # pre-norm for training stability
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

    def forward(self, x: torch.Tensor, src_key_padding_mask: torch.Tensor = None) -> torch.Tensor:
        """
        x                    : (B, T, D)
        src_key_padding_mask : (B, T) bool — True = ignore this position (masked)
        """
        x = self.pos_enc(x)
        return self.transformer(x, src_key_padding_mask=src_key_padding_mask)


# ── MTAE Decoder (reconstruction) ─────────────────────────────────────────────

class SpatialDecoder(nn.Module):
    """
    Decodes a D-dimensional embedding back to (8, 64, 64) image.
    Mirror of SpatialEncoder.
    """

    def __init__(self, embed_dim: int = 128, out_channels: int = 8):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 4 * 4),
            nn.GELU(),
        )
        self.up = nn.Sequential(
            # 4→8
            nn.ConvTranspose2d(embed_dim, 128, 2, stride=2),
            nn.BatchNorm2d(128), nn.GELU(),
            # 8→16
            nn.ConvTranspose2d(128, 64, 2, stride=2),
            nn.BatchNorm2d(64), nn.GELU(),
            # 16→32
            nn.ConvTranspose2d(64, 32, 2, stride=2),
            nn.BatchNorm2d(32), nn.GELU(),
            # 32→64
            nn.ConvTranspose2d(32, out_channels, 2, stride=2),
        )
        self.embed_dim = embed_dim

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """z: (B, D) → (B, 8, 64, 64)"""
        x = self.net(z)                                   # (B, D*16)
        x = x.view(x.size(0), self.embed_dim, 4, 4)      # (B, D, 4, 4)
        return self.up(x)                                  # (B, 8, 64, 64)


# ── Full EvOLve Encoder (spatial CNN + temporal transformer) ──────────────────

class EvOLveEncoder(nn.Module):
    """
    Full encoder: maps a patch time series → temporal embeddings.

    Input  : (B, T, 8, 64, 64)
    Output : (B, T, D)

    Also exposes a single-vector summary via .encode_summary() → (B, D)
    for classification tasks.
    """

    def __init__(
        self,
        in_channels: int = 8,
        embed_dim: int = 128,
        nhead: int = 4,
        num_layers: int = 4,
        dim_feedforward: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.spatial_enc = SpatialEncoder(in_channels, embed_dim)
        self.temporal_enc = TemporalTransformer(
            d_model=embed_dim,
            nhead=nhead,
            num_layers=num_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
        )
        self.embed_dim = embed_dim

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor = None,
    ) -> torch.Tensor:
        """
        x    : (B, T, 8, 64, 64)
        mask : (B, T) float — 1 = masked timestep (passed as padding mask)
        Returns: (B, T, D)
        """
        B, T, C, H, W = x.shape

        # Apply spatial encoder to all time steps at once
        x_flat = x.view(B * T, C, H, W)               # (B*T, 8, 64, 64)
        z_flat = self.spatial_enc(x_flat)              # (B*T, D)
        z      = z_flat.view(B, T, -1)                 # (B, T, D)

        # Convert float mask to bool padding mask for Transformer
        pad_mask = mask.bool() if mask is not None else None

        # Temporal transformer
        out = self.temporal_enc(z, src_key_padding_mask=pad_mask)  # (B, T, D)
        return out

    def encode_summary(self, x: torch.Tensor) -> torch.Tensor:
        """
        Encode to single vector by mean-pooling over time.
        x: (B, T, 8, 64, 64) → (B, D)
        """
        z = self.forward(x)              # (B, T, D)
        return z.mean(dim=1)             # (B, D)


# ── Full MTAE (Encoder + Decoder) for pretraining ─────────────────────────────

class MaskedTemporalAutoEncoder(nn.Module):
    """
    Full Masked Temporal AutoEncoder for self-supervised pretraining.

    Forward pass:
      - Takes masked_patch (zeroed at masked positions) + mask
      - Encodes to temporal embeddings
      - Decodes each time step back to image space
      - Loss computed only on masked positions
    """

    def __init__(self, encoder: EvOLveEncoder):
        super().__init__()
        self.encoder = encoder
        self.decoder = SpatialDecoder(encoder.embed_dim, out_channels=8)

    def forward(self, masked_patch: torch.Tensor, mask: torch.Tensor):
        """
        masked_patch : (B, T, 8, 64, 64) — zeroed at masked time steps
        mask         : (B, T) — 1 = masked
        Returns:
          recon      : (B, T, 8, 64, 64) — reconstructed full series
          z          : (B, T, D)         — embeddings (for contrastive loss)
        """
        B, T = masked_patch.shape[:2]

        # Encode
        z = self.encoder(masked_patch, mask)   # (B, T, D)

        # Decode each time step
        z_flat    = z.view(B * T, -1)          # (B*T, D)
        recon_flat = self.decoder(z_flat)       # (B*T, 8, 64, 64)
        recon     = recon_flat.view(B, T, 8, 64, 64)

        return recon, z
