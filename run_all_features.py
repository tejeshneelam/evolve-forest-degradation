"""
EvOLve — run_all_features.py
Master script: runs all extended feature analyses after classifier is trained.

Usage (from project root):
    python run_all_features.py

Requires:
    results/classifier_results.json  — from model/train_classifier.py
    results/patch_labels.json        — from model/label_prep.py
"""

import os
import sys

RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)

def check_prerequisite(path: str, name: str):
    if not os.path.exists(path):
        print(f"❌ Missing prerequisite: {path}")
        print(f"   Run {name} first.")
        sys.exit(1)


def main():
    check_prerequisite('results/classifier_results.json', 'model/train_classifier.py')

    print("\n" + "="*60)
    print("EvOLve Extended Feature Analysis")
    print("="*60)

    # 1. Wildlife Corridors
    print("\n[1/5] Wildlife Corridor Analysis...")
    try:
        from features.corridor import run_corridor_analysis
        run_corridor_analysis()
    except Exception as e:
        print(f"  ⚠️  Corridor analysis error: {e}")

    # 2. Landslide Vulnerability
    print("\n[2/5] Landslide Vulnerability...")
    try:
        from features.landslide import compute_landslide_vulnerability
        compute_landslide_vulnerability()
    except Exception as e:
        print(f"  ⚠️  Landslide analysis error: {e}")

    # 3. Fire Risk
    print("\n[3/5] Fire Risk Prediction...")
    try:
        from features.fire_risk import run_fire_risk_analysis
        run_fire_risk_analysis()
    except Exception as e:
        print(f"  ⚠️  Fire risk analysis error: {e}")

    # 4. Encroachment Detection
    print("\n[4/5] Encroachment Detection...")
    try:
        from features.encroachment import run_encroachment_detection
        run_encroachment_detection()
    except Exception as e:
        print(f"  ⚠️  Encroachment analysis error: {e}")

    # 5. Carbon Stock
    print("\n[5/5] Carbon Stock Estimation...")
    try:
        from features.carbon import run_carbon_analysis
        run_carbon_analysis()
    except Exception as e:
        print(f"  ⚠️  Carbon analysis error: {e}")

    # 6. Reforestation Priority (needs corridor data)
    print("\n[6/6] Reforestation Priority Map...")
    try:
        from features.reforestation import compute_reforestation_priorities
        compute_reforestation_priorities()
    except Exception as e:
        print(f"  ⚠️  Reforestation analysis error: {e}")

    print("\n" + "="*60)
    print("✅ All feature analyses complete!")
    print("   Results saved in: results/")
    print("   Files generated:")
    for f in ['corridor_analysis.json', 'landslide_risk.json',
              'fire_risk.json', 'encroachment_alerts.json',
              'carbon_stock.json', 'reforestation_priority.json']:
        path = os.path.join(RESULTS_DIR, f)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"     ✅ {f} ({size:,} bytes)")
        else:
            print(f"     ❌ {f} (not generated)")
    print("="*60)


if __name__ == '__main__':
    main()
