"""
EvOLve — model/pretrain_runner.py
Self-supervised pretraining loop for the EvOLve encoder.

Usage:
    python model/pretrain_runner.py

Outputs:
    results/encoder_pretrained.pt   — saved model weights
    results/pretrain_log.json       — loss history
"""

import os
import json
import numpy as np
import torch
from torch.utils.data import DataLoader, random_split

# ── Path setup (run from project root) ────────────────────────────────────────
PATCH_DIR  = 'data/patches'
INDEX_PATH = 'data/patches/patch_index.json'
RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)

# ── Device selection ──────────────────────────────────────────────────────────
if torch.backends.mps.is_available():
    DEVICE = torch.device('mps')
    print("✅ Using Apple Silicon MPS (GPU)")
elif torch.cuda.is_available():
    DEVICE = torch.device('cuda')
    print("✅ Using CUDA GPU")
else:
    DEVICE = torch.device('cpu')
    print("⚠️  Using CPU — will be slower")

# ── Hyperparameters ───────────────────────────────────────────────────────────
CONFIG = {
    'embed_dim':       128,
    'nhead':           4,
    'num_layers':      4,
    'dim_feedforward': 256,
    'dropout':         0.1,
    'mask_ratio':      0.40,
    'lr':              3e-4,
    'weight_decay':    1e-4,
    'epochs':          25,
    'batch_size':      8,        # 64 patches → ~8 per batch, small dataset
    'lambda_recon':    1.0,
    'lambda_contrast': 0.5,
    'temperature':     0.07,
    'val_split':       0.15,     # 15% patches for validation
}


def main():
    from model.dataset import PatchDataset, compute_stats
    from model.encoder import EvOLveEncoder, MaskedTemporalAutoEncoder
    from model.pretrain import PretrainingLoss

    # ── Compute normalization stats ────────────────────────────────────────────
    stats_path = os.path.join(RESULTS_DIR, 'band_stats.json')
    if os.path.exists(stats_path):
        print("Loading saved band stats...")
        with open(stats_path) as f:
            stats = json.load(f)
        mean = np.array(stats['mean'], dtype=np.float32)
        std  = np.array(stats['std'],  dtype=np.float32)
    else:
        print("Computing band statistics (first run, takes ~1 min)...")
        mean, std = compute_stats(PATCH_DIR, INDEX_PATH)
        with open(stats_path, 'w') as f:
            json.dump({'mean': mean.tolist(), 'std': std.tolist()}, f, indent=2)
        print(f"  Mean: {mean.round(4)}")
        print(f"  Std:  {std.round(4)}")

    # ── Dataset & DataLoader ───────────────────────────────────────────────────
    dataset = PatchDataset(
        patch_dir=PATCH_DIR,
        index_path=INDEX_PATH,
        mean=mean, std=std,
        mask_ratio=CONFIG['mask_ratio'],
        mode='pretrain',
    )

    n_val   = max(1, int(len(dataset) * CONFIG['val_split']))
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val],
                                    generator=torch.Generator().manual_seed(42))

    train_loader = DataLoader(train_ds, batch_size=CONFIG['batch_size'],
                              shuffle=True,  num_workers=0, pin_memory=False)
    val_loader   = DataLoader(val_ds,   batch_size=CONFIG['batch_size'],
                              shuffle=False, num_workers=0, pin_memory=False)

    print(f"\nDataset: {len(dataset)} patches → {n_train} train / {n_val} val")

    # ── Model ──────────────────────────────────────────────────────────────────
    encoder = EvOLveEncoder(
        in_channels=8,
        embed_dim=CONFIG['embed_dim'],
        nhead=CONFIG['nhead'],
        num_layers=CONFIG['num_layers'],
        dim_feedforward=CONFIG['dim_feedforward'],
        dropout=CONFIG['dropout'],
    )
    model = MaskedTemporalAutoEncoder(encoder).to(DEVICE)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {n_params:,}")

    # ── Optimizer & Scheduler ─────────────────────────────────────────────────
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=CONFIG['lr'],
        weight_decay=CONFIG['weight_decay'],
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=CONFIG['epochs'], eta_min=1e-6
    )

    criterion = PretrainingLoss(
        lambda_recon=CONFIG['lambda_recon'],
        lambda_contrast=CONFIG['lambda_contrast'],
        temperature=CONFIG['temperature'],
    )

    # ── Training Loop ─────────────────────────────────────────────────────────
    log = []
    best_val_loss = float('inf')
    best_epoch    = 0

    print(f"\n{'='*60}")
    print(f"Starting pretraining for {CONFIG['epochs']} epochs on {DEVICE}")
    print(f"{'='*60}\n")

    for epoch in range(1, CONFIG['epochs'] + 1):
        # ── Train ──────────────────────────────────────────────────────────
        model.train()
        train_losses = {'total': 0, 'recon': 0, 'contrast': 0}

        for batch in train_loader:
            patch        = batch['patch'].to(DEVICE)         # (B, T, 8, 64, 64)
            masked_patch = batch['masked_patch'].to(DEVICE)  # (B, T, 8, 64, 64)
            mask         = batch['mask'].to(DEVICE)          # (B, T)

            optimizer.zero_grad()
            recon, z = model(masked_patch, mask)
            losses   = criterion(recon, patch, mask, z)
            losses['total'].backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            for k in train_losses:
                train_losses[k] += losses[k].item()

        scheduler.step()
        n_train_batches = max(1, len(train_loader))
        for k in train_losses:
            train_losses[k] /= n_train_batches

        # ── Validate ───────────────────────────────────────────────────────
        model.eval()
        val_losses = {'total': 0, 'recon': 0, 'contrast': 0}

        with torch.no_grad():
            for batch in val_loader:
                patch        = batch['patch'].to(DEVICE)
                masked_patch = batch['masked_patch'].to(DEVICE)
                mask         = batch['mask'].to(DEVICE)
                recon, z     = model(masked_patch, mask)
                losses       = criterion(recon, patch, mask, z)
                for k in val_losses:
                    val_losses[k] += losses[k].item()

        n_val_batches = max(1, len(val_loader))
        for k in val_losses:
            val_losses[k] /= n_val_batches

        # ── Logging ────────────────────────────────────────────────────────
        entry = {
            'epoch':         epoch,
            'train_total':   round(train_losses['total'],    4),
            'train_recon':   round(train_losses['recon'],    4),
            'train_contrast':round(train_losses['contrast'], 4),
            'val_total':     round(val_losses['total'],      4),
            'val_recon':     round(val_losses['recon'],      4),
            'val_contrast':  round(val_losses['contrast'],   4),
            'lr':            round(scheduler.get_last_lr()[0], 6),
        }
        log.append(entry)

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:3d}/{CONFIG['epochs']} | "
                  f"Train: {train_losses['total']:.4f} "
                  f"(recon={train_losses['recon']:.4f}, contrast={train_losses['contrast']:.4f}) | "
                  f"Val: {val_losses['total']:.4f} | "
                  f"LR: {scheduler.get_last_lr()[0]:.6f}")

        # ── Save best model ────────────────────────────────────────────────
        if val_losses['total'] < best_val_loss:
            best_val_loss = val_losses['total']
            best_epoch    = epoch
            torch.save({
                'epoch':       epoch,
                'model_state': model.state_dict(),
                'encoder_state': encoder.state_dict(),
                'optimizer':   optimizer.state_dict(),
                'config':      CONFIG,
                'val_loss':    best_val_loss,
                'mean':        mean.tolist(),
                'std':         std.tolist(),
            }, os.path.join(RESULTS_DIR, 'encoder_pretrained.pt'))

    # ── Save log ───────────────────────────────────────────────────────────────
    with open(os.path.join(RESULTS_DIR, 'pretrain_log.json'), 'w') as f:
        json.dump({'config': CONFIG, 'log': log}, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Pretraining complete!")
    print(f"   Best val loss: {best_val_loss:.4f} at epoch {best_epoch}")
    print(f"   Checkpoint: results/encoder_pretrained.pt")
    print(f"   Log:        results/pretrain_log.json")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
