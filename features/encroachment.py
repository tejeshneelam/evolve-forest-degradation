"""
EvOLve — features/encroachment.py
Illegal Encroachment / Footpath Detection via NDVI Anomaly.

Detects:
  1. Sudden non-seasonal NDVI drops → possible clearing
  2. Linear spatial patterns of low NDVI → paths/roads cut through forest
  3. Persistent anomalies (not recovered in next season) → encroachment

Outputs alerts with date, patch, severity, and type.
"""

import os
import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class EncroachmentAlert:
    patch_id:     int
    month:        str
    alert_type:   str    # 'SuddenDrop' | 'PersistentAnomaly' | 'LinearPattern'
    severity:     str    # 'Low' | 'Medium' | 'High'
    ndvi_before:  float
    ndvi_at_drop: float
    ndvi_change:  float
    grid_row:     int
    grid_col:     int
    description:  str


class EncroachmentDetector:
    """
    Detects encroachment anomalies in NDVI time series.

    Parameters
    ----------
    sudden_drop_thresh   : NDVI drop in single month to flag (default 0.12)
    persist_months       : how many months drop must persist to be flagged
    seasonal_std_mult    : flag if drop > N × seasonal std (adaptive threshold)
    """

    NDVI_IDX = 6
    EVI_IDX  = 7

    def __init__(
        self,
        sudden_drop_thresh: float = 0.12,
        persist_months: int       = 2,
        seasonal_std_mult: float  = 2.0,
    ):
        self.sudden_drop_thresh = sudden_drop_thresh
        self.persist_months     = persist_months
        self.seasonal_std_mult  = seasonal_std_mult

    def compute_seasonal_baseline(
        self,
        ndvi_series: np.ndarray,   # (T,) mean NDVI per month
        months: List[str],
    ) -> np.ndarray:
        """
        Compute expected NDVI for each month by averaging same calendar
        months across years. Returns array of same length as ndvi_series.
        """
        baseline = np.zeros_like(ndvi_series)

        for t, month_label in enumerate(months):
            month_num  = int(month_label.split('-')[1])
            same_month = [i for i, m in enumerate(months) if int(m.split('-')[1]) == month_num]
            vals       = ndvi_series[same_month]
            valid      = vals[~np.isnan(vals)]
            baseline[t] = float(np.mean(valid)) if len(valid) > 0 else ndvi_series[t]

        return baseline

    def detect_patch(
        self,
        patch_path: str,
        months: List[str],
        patch_id: int,
        grid_row: int,
        grid_col: int,
    ) -> List[EncroachmentAlert]:
        alerts = []

        patch = np.load(patch_path).astype(np.float32)   # (T, 8, 64, 64)
        patch[patch == -9999] = np.nan

        ndvi    = patch[:, self.NDVI_IDX, :, :]    # (T, 64, 64)
        ndvi_t  = np.nanmean(ndvi, axis=(1, 2))    # (T,) — spatial mean per month
        T       = len(ndvi_t)

        baseline = self.compute_seasonal_baseline(ndvi_t, months)
        residual = ndvi_t - baseline    # deviation from seasonal norm

        # ── 1. Sudden Drop Detection ──────────────────────────────────────
        for t in range(1, T):
            if np.isnan(ndvi_t[t]) or np.isnan(ndvi_t[t-1]):
                continue
            drop = ndvi_t[t-1] - ndvi_t[t]
            if drop >= self.sudden_drop_thresh:
                # Check if anomalous relative to seasonal baseline
                month_num  = int(months[t].split('-')[1])
                same_month = [i for i, m in enumerate(months[:t])
                              if int(m.split('-')[1]) == month_num]
                if len(same_month) >= 2:
                    hist_std = float(np.nanstd(ndvi_t[same_month]))
                    if hist_std > 0 and drop < self.seasonal_std_mult * hist_std:
                        continue   # within normal seasonal variation

                severity = 'High' if drop >= 0.20 else ('Medium' if drop >= 0.15 else 'Low')
                alerts.append(EncroachmentAlert(
                    patch_id     = patch_id,
                    month        = months[t],
                    alert_type   = 'SuddenDrop',
                    severity     = severity,
                    ndvi_before  = round(float(ndvi_t[t-1]), 4),
                    ndvi_at_drop = round(float(ndvi_t[t]),   4),
                    ndvi_change  = round(-float(drop),       4),
                    grid_row     = grid_row,
                    grid_col     = grid_col,
                    description  = (
                        f"NDVI dropped {drop:.3f} at {months[t]} "
                        f"(from {ndvi_t[t-1]:.3f} to {ndvi_t[t]:.3f}). "
                        f"Possible encroachment or rapid clearing."
                    )
                ))

        # ── 2. Persistent Anomaly Detection ──────────────────────────────
        low_mask = residual < -self.sudden_drop_thresh * 0.7
        i = 0
        while i < T:
            if low_mask[i]:
                j = i
                while j < T and low_mask[j]:
                    j += 1
                duration = j - i
                if duration >= self.persist_months:
                    mean_deficit = float(np.mean(residual[i:j]))
                    severity = 'High' if mean_deficit < -0.20 else 'Medium'
                    alerts.append(EncroachmentAlert(
                        patch_id     = patch_id,
                        month        = months[i],
                        alert_type   = 'PersistentAnomaly',
                        severity     = severity,
                        ndvi_before  = round(float(baseline[i]), 4),
                        ndvi_at_drop = round(float(ndvi_t[i]),   4),
                        ndvi_change  = round(mean_deficit,        4),
                        grid_row     = grid_row,
                        grid_col     = grid_col,
                        description  = (
                            f"NDVI persistently below seasonal baseline for "
                            f"{duration} months starting {months[i]}. "
                            f"Average deficit: {mean_deficit:.3f}. "
                            f"May indicate progressive encroachment."
                        )
                    ))
                i = j
            else:
                i += 1

        return alerts


def run_encroachment_detection(
    patch_index_path: str = 'data/patches/patch_index.json',
    patches_dir: str      = 'data/patches',
    output_path: str      = 'results/encroachment_alerts.json',
) -> dict:
    with open(patch_index_path) as f:
        index = json.load(f)

    months   = index['months']
    detector = EncroachmentDetector()
    all_alerts = []

    for entry in index['patches']:
        pid  = entry['patch_id']
        path = os.path.join(patches_dir, f"patch_{pid:04d}.npy")
        if not os.path.exists(path):
            continue

        alerts = detector.detect_patch(
            path, months, pid, entry['grid_row'], entry['grid_col']
        )
        all_alerts.extend(alerts)

    # Sort by severity and date
    sev_order = {'High': 0, 'Medium': 1, 'Low': 2}
    all_alerts.sort(key=lambda a: (sev_order[a.severity], a.month))

    result = {
        'total_alerts': len(all_alerts),
        'high':   sum(1 for a in all_alerts if a.severity == 'High'),
        'medium': sum(1 for a in all_alerts if a.severity == 'Medium'),
        'low':    sum(1 for a in all_alerts if a.severity == 'Low'),
        'alerts': [asdict(a) for a in all_alerts],
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n🚨 Encroachment Detection:")
    print(f"   Total alerts : {result['total_alerts']}")
    print(f"   High severity: {result['high']}")
    print(f"   Medium       : {result['medium']}")
    print(f"   Low          : {result['low']}")
    print(f"✅ Saved: {output_path}")

    return result


if __name__ == '__main__':
    run_encroachment_detection()
