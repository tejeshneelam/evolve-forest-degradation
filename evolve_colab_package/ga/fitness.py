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


def evaluate_chromosome(chrom) -> float:
    """
    Train a lightweight classifier with chromosome's hyperparameters,
    evaluate with 3-fold stratified CV, return mean F1.

    Uses the pretrained encoder weights (frozen) — only trains the head.
    This is FAST (~5–10s per chromosome on MPS).
    """
    from model.encoder import EvOLveEncoder
    from model.classifier import DegradationClassifier
    from model.dataset import PatchDataset

    mean, std = load_band_stats()
    labels    = load_patch_labels()

    # Ensure hidden_dim is divisible by nhead
    hidden = int(chrom.hidden_dim)
    nhead  = int(chrom.nhead)
    valid_nheads = [h for h in [2, 4, 8] if hidden % h == 0]
    if not valid_nheads:
        nhead = 2
    elif nhead not in valid_nheads:
        nhead = valid_nheads[0]

    # Load pretrained encoder
    ckpt_path = os.path.join(RESULTS_DIR, 'encoder_pretrained.pt')
    if not os.path.exists(ckpt_path):
        # No pretrained encoder yet — return random fitness
        return float(np.random.uniform(0.1, 0.4))

    ckpt = torch.load(ckpt_path, map_location='cpu')
    enc_cfg = ckpt['config']

    encoder = EvOLveEncoder(
        in_channels=8,
        embed_dim=enc_cfg['embed_dim'],
        nhead=enc_cfg.get('nhead', 4),
        num_layers=enc_cfg.get('num_layers', 4),
        dim_feedforward=enc_cfg.get('dim_feedforward', 256),
        dropout=float(chrom.dropout),
    )
    mtae_state = ckpt['model_state']
    enc_state  = {k.replace('encoder.', ''): v
                  for k, v in mtae_state.items() if k.startswith('encoder.')}
    encoder.load_state_dict(enc_state)

    dataset = PatchDataset(PATCH_DIR, INDEX_PATH, mean=mean, std=std,
                           mode='finetune', labels=labels)

    patch_ids  = [e['patch_id'] for e in dataset.entries]
    label_list = [labels.get(pid, 0) for pid in patch_ids]

    # 3-fold stratified CV
    skf   = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    f1s   = []

    for train_idx, val_idx in skf.split(patch_ids, label_list):
        model = DegradationClassifier(encoder, freeze_encoder=True,
                                      dropout=float(chrom.dropout)).to(DEVICE)
        optimizer = torch.optim.Adam(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=float(chrom.lr)
        )

        train_loader = DataLoader(dataset, batch_size=4,
                                  sampler=SubsetRandomSampler(train_idx))
        val_loader   = DataLoader(dataset, batch_size=4,
                                  sampler=SubsetRandomSampler(val_idx))

        # Quick training: 20 epochs
        model.train()
        for _ in range(20):
            for batch in train_loader:
                patch = batch['patch'].to(DEVICE)
                label = batch['label'].to(DEVICE)
                score = model(patch)
                loss  = nn.functional.binary_cross_entropy(score, label)
                optimizer.zero_grad(); loss.backward(); optimizer.step()

        # Evaluate
        model.eval()
        y_true, y_pred = [], []
        with torch.no_grad():
            for batch in val_loader:
                score = model(batch['patch'].to(DEVICE)).cpu().numpy()
                y_true.extend(batch['label'].numpy().tolist())
                y_pred.extend([1 if s >= 0.5 else 0 for s in score])

        f1 = f1_score(y_true, y_pred, zero_division=0)
        f1s.append(f1)

    return float(np.mean(f1s))
