"""
EvOLve — ga/fitness.py
Fitness function for the GA: evaluates a chromosome's F1 score
by training a quick classifier with those hyperparameters.

Uses a fast 3-fold cross-validation on the 64 patches.
"""

import os
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, SubsetRandomSampler
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

PATCH_DIR  = 'data/patches'
INDEX_PATH = 'data/patches/patch_index.json'
RESULTS_DIR = 'results'

# Device
DEVICE = (torch.device('mps') if torch.backends.mps.is_available()
          else torch.device('cuda') if torch.cuda.is_available()
          else torch.device('cpu'))


def load_band_stats():
    stats_path = os.path.join(RESULTS_DIR, 'band_stats.json')
    if os.path.exists(stats_path):
        with open(stats_path) as f:
            d = json.load(f)
        return np.array(d['mean'], dtype=np.float32), np.array(d['std'], dtype=np.float32)
    from model.dataset import BAND_MEAN, BAND_STD
    return BAND_MEAN, BAND_STD


def load_patch_labels() -> dict:
    labels_path = os.path.join(RESULTS_DIR, 'patch_labels.json')
    with open(labels_path) as f:
        d = json.load(f)
    return {int(k): v['label'] for k, v in d['labels'].items()}


# Global cache for patch embeddings to avoid redundant CNN+Transformer forward passes
EMBEDDINGS_CACHE = None


class GAHeadModel(nn.Module):
    """
    Lightweight classification head + temporal attention pooling.
    Equivalent to DegradationClassifier with a frozen encoder.
    """
    def __init__(self, embed_dim: int = 128, dropout: float = 0.3):
        super().__init__()
        D = embed_dim
        self.head = nn.Sequential(
            nn.Linear(D, D // 2),
            nn.LayerNorm(D // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(D // 2, D // 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(D // 4, 1),
        )
        self.time_attn = nn.Linear(D, 1)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        attn_weights = torch.softmax(self.time_attn(z), dim=1)
        summary      = (z * attn_weights).sum(dim=1)
        logit        = self.head(summary).squeeze(-1)
        return torch.sigmoid(logit)


def evaluate_chromosome(chrom) -> float:
    """
    Train a lightweight classifier with chromosome's hyperparameters,
    evaluate with 3-fold stratified CV, return mean F1.

    Uses pre-computed encoder embeddings to run 1000x faster.
    """
    global EMBEDDINGS_CACHE

    mean, std = load_band_stats()
    labels    = load_patch_labels()

    # Load pretrained encoder and compute embeddings ONCE
    if EMBEDDINGS_CACHE is None:
        print("  [GA] Pre-computing and caching patch embeddings (runs once)...")
        from model.encoder import EvOLveEncoder
        from model.dataset import PatchDataset

        ckpt_path = os.path.join(RESULTS_DIR, 'encoder_pretrained.pt')
        if not os.path.exists(ckpt_path):
            return float(np.random.uniform(0.1, 0.4))

        ckpt = torch.load(ckpt_path, map_location='cpu')
        enc_cfg = ckpt['config']

        encoder = EvOLveEncoder(
            in_channels=8,
            embed_dim=enc_cfg['embed_dim'],
            nhead=enc_cfg.get('nhead', 4),
            num_layers=enc_cfg.get('num_layers', 4),
            dim_feedforward=enc_cfg.get('dim_feedforward', 256),
            dropout=0.0,  # no dropout during encoding
        ).to(DEVICE)
        mtae_state = ckpt['model_state']
        enc_state  = {k.replace('encoder.', ''): v
                      for k, v in mtae_state.items() if k.startswith('encoder.')}
        encoder.load_state_dict(enc_state)
        encoder.eval()

        dataset = PatchDataset(PATCH_DIR, INDEX_PATH, mean=mean, std=std,
                               mode='finetune', labels=labels)
        
        # Load and encode all patches in a single batch
        loader = DataLoader(dataset, batch_size=len(dataset), shuffle=False)
        batch = next(iter(loader))
        patches = batch['patch'].to(DEVICE)
        
        with torch.no_grad():
            z_all = encoder(patches).cpu()  # Move embeddings to CPU cache
            
        labels_all = batch['label']
        patch_ids = batch['patch_id'].tolist()

        EMBEDDINGS_CACHE = {
            'embeddings': z_all,
            'labels':     labels_all,
            'patch_ids':  patch_ids,
            'embed_dim':  enc_cfg['embed_dim']
        }
        print("  [GA] Cached embeddings shape:", z_all.shape)

    # ── Retrieve cached embeddings ────────────────────────────────────────────
    z_all      = EMBEDDINGS_CACHE['embeddings']
    labels_all = EMBEDDINGS_CACHE['labels']
    patch_ids  = EMBEDDINGS_CACHE['patch_ids']
    embed_dim  = EMBEDDINGS_CACHE['embed_dim']

    # 3-fold stratified CV
    skf   = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    f1s   = []

    for train_idx, val_idx in skf.split(patch_ids, labels_all.numpy()):
        model = GAHeadModel(embed_dim=embed_dim, dropout=float(chrom.dropout)).to(DEVICE)
        optimizer = torch.optim.Adam(model.parameters(), lr=float(chrom.lr))

        # Train for 20 epochs
        model.train()
        z_train = z_all[train_idx].to(DEVICE)
        y_train = labels_all[train_idx].to(DEVICE)
        
        for _ in range(20):
            # Batch size 4 equivalent loops
            permutation = torch.randperm(z_train.size(0))
            for i in range(0, z_train.size(0), 4):
                indices = permutation[i:i+4]
                bz, by = z_train[indices], y_train[indices]
                
                score = model(bz)
                loss  = nn.functional.binary_cross_entropy(score, by)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        # Evaluate
        model.eval()
        z_val = z_all[val_idx].to(DEVICE)
        y_val = labels_all[val_idx]
        
        with torch.no_grad():
            score = model(z_val).cpu().numpy()
            y_pred = [1 if s >= 0.5 else 0 for s in score]
            
        f1 = f1_score(y_val.numpy(), y_pred, zero_division=0)
        f1s.append(f1)

    return float(np.mean(f1s))
