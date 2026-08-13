"""
EvOLve — model/label_prep.py
Align Hansen GFC labels to each patch and generate training labels.

Output:
  results/patch_labels.json  — {patch_id: {label, soft_label, loss_pixels, loss_year_counts}}

Hansen bands:
  [0] treecover2000  — tree cover percentage in 2000 (0-100)
  [1] loss           — 1 if forest loss occurred 2001-2025
  [2] lossyear       — year of loss (1=2001, 19=2019, ..., 25=2025)
"""

import os
import json
import numpy as np

LABELS_DIR  = 'data/labels'
PATCHES_DIR = 'data/patches'
RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)

# ── Load Hansen labels (558 × 557) ────────────────────────────────────────────
hansen = np.load(os.path.join(LABELS_DIR, 'hansen_aligned.npy'))  # (3, 558, 557)
treecover  = hansen[0]   # 0–100 %
loss_flag  = hansen[1]   # 0 or 1
loss_year  = hansen[2]   # 0 (no loss) or 1–25 (year offset from 2000)

print(f"Hansen shape       : {hansen.shape}")
print(f"Mean tree cover    : {treecover.mean():.1f}%")
print(f"Total loss pixels  : {(loss_flag == 1).sum()} / {loss_flag.size} ({(loss_flag==1).mean()*100:.2f}%)")
print("\nLoss by year (2019–2025):")
for yr in range(19, 26):
    count = (loss_year == yr).sum()
    print(f"  20{yr}: {count:5d} pixels")

# ── Load patch index ───────────────────────────────────────────────────────────
with open(os.path.join(PATCHES_DIR, 'patch_index.json')) as f:
    index = json.load(f)

# ── Build per-patch labels ─────────────────────────────────────────────────────
patch_labels = {}
THRESHOLD_SOFT = 0.03   # ≥3% pixel loss → label as degraded

for entry in index['patches']:
    pid   = entry['patch_id']
    y0, y1, x0, x1 = entry['pixel_bounds']   # [row_start, row_end, col_start, col_end]

    # Crop Hansen to this patch's spatial extent
    patch_loss      = loss_flag[y0:y1, x0:x1]
    patch_lossyear  = loss_year[y0:y1, x0:x1]
    patch_treecover = treecover[y0:y1, x0:x1]

    total_pixels     = patch_loss.size
    loss_pixels      = int((patch_loss == 1).sum())
    soft_label       = round(loss_pixels / total_pixels, 4)  # fraction of degraded pixels

    # Binary label: 1 = degraded, 0 = healthy
    binary_label = int(soft_label >= THRESHOLD_SOFT)

    # Year-by-year breakdown (only years in our data window 2019-2025)
    loss_by_year = {}
    for yr in range(19, 26):
        count = int((patch_lossyear == yr).sum())
        if count > 0:
            loss_by_year[f'20{yr}'] = count

    # Mean tree cover in 2000 (context)
    mean_cover_2000 = round(float(patch_treecover.mean()), 1)

    patch_labels[pid] = {
        'patch_id':        pid,
        'label':           binary_label,        # 0 or 1
        'soft_label':      soft_label,          # 0.0–1.0 (fraction degraded)
        'loss_pixels':     loss_pixels,
        'total_pixels':    total_pixels,
        'loss_by_year':    loss_by_year,
        'mean_cover_2000': mean_cover_2000,
        'pixel_bounds':    [y0, y1, x0, x1],
    }

# ── Summary ────────────────────────────────────────────────────────────────────
degraded = sum(1 for v in patch_labels.values() if v['label'] == 1)
healthy  = sum(1 for v in patch_labels.values() if v['label'] == 0)
print(f"\nPatch label summary (threshold={THRESHOLD_SOFT*100:.0f}% loss):")
print(f"  Degraded (label=1): {degraded} patches")
print(f"  Healthy  (label=0): {healthy} patches")
print(f"  Total             : {len(patch_labels)} patches")

# Soft label distribution
soft_vals = [v['soft_label'] for v in patch_labels.values()]
print(f"\nSoft label stats:")
print(f"  Min  : {min(soft_vals):.4f}")
print(f"  Max  : {max(soft_vals):.4f}")
print(f"  Mean : {np.mean(soft_vals):.4f}")
print(f"  Std  : {np.std(soft_vals):.4f}")

# Save
out_path = os.path.join(RESULTS_DIR, 'patch_labels.json')
with open(out_path, 'w') as f:
    json.dump({
        'threshold': THRESHOLD_SOFT,
        'n_degraded': degraded,
        'n_healthy': healthy,
        'labels': patch_labels,
    }, f, indent=2)

print(f"\n✅ Saved to {out_path}")
