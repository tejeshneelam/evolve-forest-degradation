"""
EvOLve — model/train_classifier.py
Fine-tune degradation classifier on Hansen labels.
Benchmarks 3 models: EvOLve (pretrained), Supervised baseline, Random Forest.

Usage:
    python model/train_classifier.py

Requires:
    results/encoder_pretrained.pt   — from pretrain_runner.py
    results/patch_labels.json       — from label_prep.py

Outputs:
    results/classifier.pt               — best EvOLve classifier
    results/classifier_results.json     — all metrics + comparison
    results/heatmaps/                   — Grad-CAM heatmaps per patch
"""

import os
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    precision_score, recall_score, classification_report
)
from sklearn.model_selection import StratifiedKFold

RESULTS_DIR = 'results'
PATCH_DIR   = 'data/patches'
INDEX_PATH  = 'data/patches/patch_index.json'

# Device
if torch.backends.mps.is_available():
    DEVICE = torch.device('mps')
elif torch.cuda.is_available():
    DEVICE = torch.device('cuda')
else:
    DEVICE = torch.device('cpu')
print(f"Device: {DEVICE}")

CONFIG = {
    'lr':           1e-3,
    'weight_decay': 1e-4,
    'epochs':       60,
    'batch_size':   8,
    'dropout':      0.3,
    'val_split':    0.20,
    'threshold':    0.5,
}


def load_checkpoint():
    """Load pretrained encoder + band stats."""
    ckpt_path = os.path.join(RESULTS_DIR, 'encoder_pretrained.pt')
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(
            f"Pretrained checkpoint not found at {ckpt_path}.\n"
            "Run: python model/pretrain_runner.py first."
        )
    ckpt = torch.load(ckpt_path, map_location='cpu')
    mean = np.array(ckpt['mean'], dtype=np.float32)
    std  = np.array(ckpt['std'],  dtype=np.float32)
    return ckpt, mean, std


def load_labels() -> dict:
    labels_path = os.path.join(RESULTS_DIR, 'patch_labels.json')
    if not os.path.exists(labels_path):
        print("Labels not found — running label_prep.py first...")
        import subprocess, sys
        subprocess.run([sys.executable, 'model/label_prep.py'], check=True)
    with open(labels_path) as f:
        data = json.load(f)
    return {int(k): v['label'] for k, v in data['labels'].items()}


def compute_metrics(y_true, y_pred, y_score=None) -> dict:
    metrics = {
        'accuracy':  round(accuracy_score(y_true, y_pred), 4),
        'f1':        round(f1_score(y_true, y_pred, zero_division=0), 4),
        'precision': round(precision_score(y_true, y_pred, zero_division=0), 4),
        'recall':    round(recall_score(y_true, y_pred, zero_division=0), 4),
    }
    if y_score is not None and len(set(y_true)) > 1:
        metrics['auc'] = round(roc_auc_score(y_true, y_score), 4)
    return metrics


# ── 1. EvOLve Fine-Tuned Classifier ───────────────────────────────────────────

def train_evolve_classifier(ckpt, mean, std, labels):
    from model.encoder import EvOLveEncoder, MaskedTemporalAutoEncoder
    from model.classifier import DegradationClassifier
    from model.dataset import PatchDataset

    # Rebuild encoder and load pretrained weights
    encoder_cfg = ckpt['config']
    encoder = EvOLveEncoder(
        in_channels=8,
        embed_dim=encoder_cfg['embed_dim'],
        nhead=encoder_cfg['nhead'],
        num_layers=encoder_cfg['num_layers'],
        dim_feedforward=encoder_cfg['dim_feedforward'],
        dropout=encoder_cfg['dropout'],
    )
    # Load encoder weights from the MTAE checkpoint
    mtae_state = ckpt['model_state']
    encoder_state = {k.replace('encoder.', ''): v
                     for k, v in mtae_state.items() if k.startswith('encoder.')}
    encoder.load_state_dict(encoder_state)

    model = DegradationClassifier(encoder, freeze_encoder=True,
                                  dropout=CONFIG['dropout']).to(DEVICE)

    # Dataset
    dataset = PatchDataset(PATCH_DIR, INDEX_PATH, mean=mean, std=std,
                           mode='finetune', labels=labels)
    n_val   = max(1, int(len(dataset) * CONFIG['val_split']))
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val],
                                    generator=torch.Generator().manual_seed(42))

    train_loader = DataLoader(train_ds, batch_size=CONFIG['batch_size'],
                              shuffle=True, num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=CONFIG['batch_size'],
                              shuffle=False, num_workers=0)

    # Class imbalance weight
    all_labels = [labels[e['patch_id']] for e in dataset.entries]
    n_pos = sum(all_labels)
    n_neg = len(all_labels) - n_pos
    pos_weight = torch.tensor([n_neg / max(n_pos, 1)], dtype=torch.float32).to(DEVICE)
    criterion = nn.BCELoss(weight=None)  # simplified; use BCEWithLogitsLoss for robustness

    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=CONFIG['lr'], weight_decay=CONFIG['weight_decay']
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)

    best_f1, best_state = 0.0, None
    log = []

    print(f"\n--- Training EvOLve Classifier ({n_train} train / {n_val} val) ---")
    for epoch in range(1, CONFIG['epochs'] + 1):
        model.train()
        for batch in train_loader:
            patch = batch['patch'].to(DEVICE)
            label = batch['label'].to(DEVICE)
            score = model(patch)
            loss  = nn.functional.binary_cross_entropy(score, label)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        # Validate
        model.eval()
        y_true, y_score_list = [], []
        with torch.no_grad():
            for batch in val_loader:
                patch = batch['patch'].to(DEVICE)
                score = model(patch).cpu().numpy()
                y_true.extend(batch['label'].numpy().tolist())
                y_score_list.extend(score.tolist())

        y_pred = [1 if s >= CONFIG['threshold'] else 0 for s in y_score_list]
        f1_val = f1_score(y_true, y_pred, zero_division=0)
        scheduler.step(1 - f1_val)

        if f1_val > best_f1:
            best_f1    = f1_val
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch % 15 == 0 or epoch == 1:
            print(f"  Epoch {epoch:3d}/{CONFIG['epochs']} | val F1={f1_val:.4f} (best={best_f1:.4f})")

        log.append({'epoch': epoch, 'val_f1': round(f1_val, 4)})

    # Load best
    model.load_state_dict(best_state)
    torch.save({'model_state': best_state, 'config': CONFIG,
                'encoder_config': encoder_cfg, 'mean': mean.tolist(), 'std': std.tolist()},
               os.path.join(RESULTS_DIR, 'classifier.pt'))

    # Final evaluation on full dataset
    model.eval()
    full_loader = DataLoader(dataset, batch_size=CONFIG['batch_size'],
                             shuffle=False, num_workers=0)
    all_true, all_score = [], []
    with torch.no_grad():
        for batch in full_loader:
            score = model(batch['patch'].to(DEVICE)).cpu().numpy()
            all_true.extend(batch['label'].numpy().tolist())
            all_score.extend(score.tolist())

    all_pred = [1 if s >= CONFIG['threshold'] else 0 for s in all_score]
    metrics  = compute_metrics(all_true, all_pred, all_score)
    print(f"\n  EvOLve final metrics: {metrics}")
    print(classification_report(all_true, all_pred, target_names=['Healthy', 'Degraded']))

    return model, dataset, metrics, log, all_score


# ── 2. Supervised Baseline ────────────────────────────────────────────────────

def train_supervised_baseline(mean, std, labels) -> dict:
    from model.classifier import SupervisedBaseline
    from model.dataset import PatchDataset

    model = SupervisedBaseline(embed_dim=128, dropout=CONFIG['dropout']).to(DEVICE)
    dataset = PatchDataset(PATCH_DIR, INDEX_PATH, mean=mean, std=std,
                           mode='finetune', labels=labels)
    n_val   = max(1, int(len(dataset) * CONFIG['val_split']))
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val],
                                    generator=torch.Generator().manual_seed(42))

    train_loader = DataLoader(train_ds, batch_size=CONFIG['batch_size'], shuffle=True, num_workers=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG['lr'])

    print(f"\n--- Training Supervised Baseline ---")
    for epoch in range(1, CONFIG['epochs'] + 1):
        model.train()
        for batch in train_loader:
            patch = batch['patch'].to(DEVICE)
            label = batch['label'].to(DEVICE)
            score = model(patch)
            loss  = nn.functional.binary_cross_entropy(score, label)
            optimizer.zero_grad(); loss.backward(); optimizer.step()

    model.eval()
    full_loader = DataLoader(dataset, batch_size=8, shuffle=False, num_workers=0)
    all_true, all_score = [], []
    with torch.no_grad():
        for batch in full_loader:
            score = model(batch['patch'].to(DEVICE)).cpu().numpy()
            all_true.extend(batch['label'].numpy().tolist())
            all_score.extend(score.tolist())

    all_pred = [1 if s >= 0.5 else 0 for s in all_score]
    metrics  = compute_metrics(all_true, all_pred, all_score)
    print(f"  Supervised baseline metrics: {metrics}")
    return metrics


# ── 3. Random Forest Baseline ─────────────────────────────────────────────────

def train_random_forest(mean, std, labels) -> dict:
    """
    Hand-crafted features: NDVI trend slope, mean NDVI, std, min, max,
    EVI mean, SWIR ratio, seasonal amplitude.
    """
    import json, glob
    print(f"\n--- Training Random Forest Baseline ---")

    with open(INDEX_PATH) as f:
        index = json.load(f)

    X, y = [], []
    NDVI_IDX, EVI_IDX = 6, 7

    for entry in index['patches']:
        pid   = entry['patch_id']
        patch = np.load(f"data/patches/patch_{pid:04d}.npy").astype(np.float32)
        patch[patch == -9999] = np.nan

        ndvi = patch[:, NDVI_IDX, :, :]    # (T, 64, 64)
        evi  = patch[:, EVI_IDX,  :, :]

        # Spatial mean per time step
        ndvi_t = np.nanmean(ndvi, axis=(1, 2))   # (T,)
        evi_t  = np.nanmean(evi,  axis=(1, 2))   # (T,)

        # NDVI trend slope (linear regression over time)
        t  = np.arange(len(ndvi_t))
        ok = ~np.isnan(ndvi_t)
        if ok.sum() > 2:
            slope = np.polyfit(t[ok], ndvi_t[ok], 1)[0]
        else:
            slope = 0.0

        feats = [
            float(np.nanmean(ndvi_t)),          # mean NDVI over time
            float(np.nanstd(ndvi_t)),           # NDVI variability
            float(np.nanmin(ndvi_t)),           # NDVI minimum (stress)
            float(np.nanmax(ndvi_t)),           # NDVI maximum
            slope,                              # NDVI trend (neg = declining)
            float(np.nanmean(evi_t)),           # mean EVI
            float(np.nanstd(evi_t)),            # EVI variability
            entry['valid_fraction'],            # data quality
        ]
        X.append(feats)
        y.append(labels.get(pid, 0))

    X, y = np.array(X), np.array(y)
    rf = RandomForestClassifier(n_estimators=200, max_depth=8,
                                random_state=42, class_weight='balanced')
    rf.fit(X, y)
    y_pred  = rf.predict(X)
    y_score = rf.predict_proba(X)[:, 1]
    metrics = compute_metrics(y.tolist(), y_pred.tolist(), y_score.tolist())
    print(f"  Random Forest metrics: {metrics}")
    return metrics


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    from model.gradcam import generate_all_heatmaps

    # Load pretrained checkpoint + labels
    ckpt, mean, std = load_checkpoint()
    labels = load_labels()

    print(f"\nLabel distribution: "
          f"{sum(labels.values())} degraded / {len(labels)-sum(labels.values())} healthy "
          f"out of {len(labels)} patches")

    # Train all 3 models
    evolve_model, dataset, evolve_metrics, train_log, all_scores = \
        train_evolve_classifier(ckpt, mean, std, labels)

    baseline_metrics = train_supervised_baseline(mean, std, labels)
    rf_metrics       = train_random_forest(mean, std, labels)

    # Generate Grad-CAM heatmaps for all patches
    print("\n--- Generating Grad-CAM heatmaps ---")
    from model.dataset import PatchDataset
    infer_ds = PatchDataset(PATCH_DIR, INDEX_PATH, mean=mean, std=std, mode='inference')
    heatmap_idx = generate_all_heatmaps(evolve_model, infer_ds, DEVICE)

    # Build degradation score map for all patches
    patch_scores = {}
    with open(INDEX_PATH) as f:
        index = json.load(f)
    for i, entry in enumerate(index['patches']):
        pid = entry['patch_id']
        patch_scores[pid] = {
            'degradation_score': round(all_scores[i], 4) if i < len(all_scores) else 0.5,
            'prediction':        1 if all_scores[i] >= CONFIG['threshold'] else 0,
            'label':             labels.get(pid, -1),
        }

    # Save all results
    results = {
        'evolve_classifier':    evolve_metrics,
        'supervised_baseline':  baseline_metrics,
        'random_forest':        rf_metrics,
        'training_log':         train_log,
        'patch_scores':         patch_scores,
        'config':               CONFIG,
    }
    with open(os.path.join(RESULTS_DIR, 'classifier_results.json'), 'w') as f:
        json.dump(results, f, indent=2)

    # ── Comparison Table ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("BENCHMARK COMPARISON")
    print(f"{'='*60}")
    print(f"{'Model':<30} {'Acc':>6} {'F1':>6} {'AUC':>6} {'Prec':>6} {'Rec':>6}")
    print("-" * 60)
    for name, m in [
        ("EvOLve (self-supervised)",  evolve_metrics),
        ("Supervised baseline",        baseline_metrics),
        ("Random Forest",              rf_metrics),
    ]:
        print(f"{name:<30} {m.get('accuracy',0):>6.4f} {m.get('f1',0):>6.4f} "
              f"{m.get('auc',0):>6.4f} {m.get('precision',0):>6.4f} {m.get('recall',0):>6.4f}")
    print(f"{'='*60}")
    print(f"\n✅ Results saved: results/classifier_results.json")
    print(f"✅ Classifier:    results/classifier.pt")
    print(f"✅ Heatmaps:      results/heatmaps/")


if __name__ == '__main__':
    main()
