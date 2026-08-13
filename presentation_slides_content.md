# 🧬 Review 1 Presentation Content Map
**Project Title**: An Evolutionary AI Framework for Forest Cover Monitoring and Vegetation Analysis Using Sentinel-2 Satellite Data

### 🏷️ Project Acronym:
**EvOLve** — **Ev**olutionary **O**ptimization, **L**earning, and **v**egetation **e**nvironmental adaptive systems.
*(This explicitly justifies our use of the Genetic Algorithm (GA) as a core framework element, rather than just a side tool!)*

---

## Slide 1: Title Slide
- **Project Title**: An Evolutionary AI Framework for Forest Cover Monitoring and Vegetation Analysis Using Sentinel-2 Satellite Data
- **Project Tagline**: **EvOLve** — **Ev**olutionary **O**ptimization, **L**earning, and **v**egetation **e**nvironmental adaptive systems.
- **Project Members**: *[Insert Your Names & Roll Numbers here]*
- **Keywords**: Forest cover monitoring, Vegetation health, Wildlife corridors, Wayanad 2024, Landslide vulnerability, Monsoon anomalies, Self-Supervised Learning, Genetic Algorithm, Sentinel-2.

---

## Slide 2: Contents
- **Introduction & Motivation** (Wayanad 2024 Disaster Context & Project Tagline)
- **Literature Survey & Research Gaps**
- **Problem Statement & Objectives**
- **Research Questions & Technical Answers** (Complexity, Compute, Location Dependency)
- **Proposed Methodology** (MTAE Architecture + Genetic Algorithm Evolving)
- **Dataset Details** (Sentinel-2 72-month time series)
- **Sem 7 Action Accomplished** (Version 1.0 complete with live React-FastAPI dashboard)
- **Sem 8 Action Plan** (Version 2.0 Google Earth Engine dynamic global expansion)

---

## Slide 3: Questions to Address (CRITICAL — Professors will check this!)

### 1. Complexity of the Algorithm
- **Spatial Encoder (CNN)**: $O(C \cdot H \cdot W)$ per time step (highly efficient $3 \times 3$ convolutions).
- **Temporal Transformer**: $O(T^2 \cdot D)$ self-attention complexity where $T=72$ months and $D=128$ embedding dimensions.
- **Classifier Head**: Light MLP ($O(D^2)$) with attention-pooling, making training on GPU take milliseconds.
- **Total Model Parameters**: **1,145,288 parameters** (combining spatial CNN, Temporal Transformer, and Attention Head).

### 2. Compute Requirements (T4 Colab & Local Mac)
- **Training**: Google Colab T4 GPU (supports CUDA acceleration) or Apple Silicon Mac (supports PyTorch MPS GPU).
- **Runtime**:
  - Self-Supervised Pretraining: **~2 minutes** (25 epochs).
  - Classifier Fine-tuning: **~30 seconds** (60 epochs).
  - Genetic Algorithm: **~1 minute** (30 generations of 20 chromosomes using our custom embedding cache).

### 3. Land Location Dependency
- **Current (Version 1.0)**: Region-dependent on Wayanad Wildlife Sanctuary (Muthanga Range) boundaries (`[11.625, 76.325]` to `[11.675, 76.375]`).
- **Future (Version 2.0)**: Location-agnostic. The UI Leaflet map will pass user-drawn coordinates to the Google Earth Engine (GEE) API to fetch Sentinel-2 bands for *any* place on Earth in real-time.

### 4. Landslide Prediction & Monsoon Integration
- **Rainfall + Forest Loss + Slope Interaction**: We integrate Sentinel-2 derived **dynamic canopy loss rate** (root binding cohesion) with **slope gradients** (SRTM DEM) and **antecedent rainfall** (CHIRPS precipitation dataset).
- **Monsoon Adaptive Thresholds**: The GA evolves season-aware NDVI warning boundaries (`dry=0.333`, `monsoon=0.554`). This allows the system to ignore natural leaf shedding in the dry season but immediately trigger high-sensitivity alerts if canopy loss occurs during monsoon rainfall, predicting landslides before they happen.

---

## Slide 4: Introduction
- **Early Signs of Degradation**: Forest degradation begins long before deforestation is visible. Disease, logging, and climatic stresses cause gradual changes in the canopy.
- **Wayanad 2024 Disaster**: Forest canopy degradation on steep hillsides in Mundakkai and Chooralmala stripped the soil of root cohesion, causing catastrophic landslides during heavy monsoon rains.
- **The Challenge**: Traditional forest surveys (e.g., ISFR) are published once every 2 years. Satellite AI exists, but depends on fixed thresholds that cannot adapt to seasons, leading to false alarms.

---

## Slide 5: Motivation
- **Real-Time Disaster Mitigation**: Evolving warning thresholds based on rainfall and canopy health can give forest rangers and disaster management forces a 48-hour early warning for landslides and forest fires.
- **Carbon Asset Economics**: Estimating forest biomass carbon value dynamically creates financial incentives for forest preservation (Carbon Credits).
- **Ranger Safety**: Rangers need automated, safe patrol route planning to inspect alerts while avoiding active forest fires and animal migration corridors.

---

## Slide 6: Literature Survey

1. **"Deep Learning for Forest Degradation Detection using Sentinel-2"** (Author: *Gomez et al., 2021*)
   - **Method**: 3D CNNs on Sentinel-2 patches.
   - **Limitation**: Requires thousands of manually labeled pixel maps (highly expensive) and fails when applied to different seasonal regions.
2. **"Seasonal Vegetation Thresholding using Remote Sensing"** (Author: *Venkatesh et al., 2022*)
   - **Method**: Historical static NDVI baseline thresholding.
   - **Limitation**: Static thresholds trigger false alarms during natural seasonal droughts (leaf-shedding) and do not reflect climate change.
3. **"Landslide Hazard Mapping using Machine Learning"** (Author: *Sajinkumar et al., 2023*)
   - **Method**: Random Forest using slope and soil type.
   - **Limitation**: Static model; does not integrate live satellite-derived tree root decay or dynamic rainfall changes.

---

## Slide 7: Research Gaps
- **Lack of Adaptive Thresholding**: Existing remote sensing systems use static NDVI boundaries that trigger false alerts during dry seasons.
- **High Label Dependency**: Most deep learning models require pixel-level segmentation maps, which do not exist for most dense tropical forests.
- **Lack of Actionable Conservation Tools**: Earth observation models produce research papers but do not output ranger routes, reforestation rankings, or economic carbon valuations in a unified dashboard.

---

## Slide 8: Problem Statement & Objectives

### Problem Statement:
Develop a self-supervised AI framework that monitors gradual forest cover degradation in tropical regions, adapts dynamically to seasonal shifts, and provides actionable disaster and conservation intelligence.

### Objectives:
1. **Self-Supervised Feature Learning**: Train a Masked Temporal Autoencoder (MTAE) to learn normal forest patterns from unlabeled Sentinel-2 imagery.
2. **Adaptive Season-Aware Alerting**: Implement a Genetic Algorithm to evolve optimal warning thresholds for dry, monsoon, and retreat seasons.
3. **Actionable Conservation Modules**: Compute wildlife corridors, landslide vulnerability, fire risk index, carbon stock assets, and safe ranger routes.
4. **Deploy Dashboard**: Launch a high-performance web dashboard (React + Leaflet + FastAPI).

---

## Slide 9: Methodology

### Model Architecture (MTAE):
1. **Spatial CNN**: Extracts spatial texture features from Sentinel-2 bands (8 bands: Red, Green, Blue, NIR, SWIR1, SWIR2, NDVI, EVI).
2. **Temporal Transformer**: Learns the temporal sequence of forest changes over 72 months.
3. **Masked Reconstruction**: Mask 40% of the months randomly and force the decoder to reconstruct the missing vegetation profiles, learning robust representations without labels.

### Optimization (Genetic Algorithm):
- **Chromosome**: Evolves hyperparameters (learning rate, dropout) and alert boundaries:
  $$\text{Chromosome} = [\text{lr}, \text{dropout}, \text{ndvi\_thresh\_dry}, \text{ndvi\_thresh\_monsoon}, \text{ndvi\_thresh\_retreat}]$$
- **Fitness Function**: Evaluates F1-score on a 3-fold stratified cross-validation split of labeled patches.

---

## Slide 10: Dataset Details
- **Satellite Source**: Sentinel-2 Level-2A (Bottom of Atmosphere reflectance).
- **Time Window**: 72 months (Jan 2019 to Dec 2025).
- **Bands Collected (8)**: B2 (Blue), B3 (Green), B4 (Red), B8 (NIR), B11 (SWIR1), B12 (SWIR2), NDVI, EVI.
- **Study Area**: Wayanad Wildlife Sanctuary (Muthanga Range), divided into an 8x8 grid of **64 patches** (each patch is $64 \times 64$ pixels at 10m resolution = $640\text{m} \times 640\text{m}$).

---

## Slide 11: Plan of Action — Semester 7 (Completed Work)
- **MTAE Pretraining**: Trained for 25 epochs on Google Colab CUDA GPU (**Best validation loss: 1.2045**).
- **Classifier Fine-tuning**: Reached **96.88% Accuracy** and **85.71% F1-score**, beating the Supervised DL Baseline (83.33% F1-score).
- **Genetic Algorithm**: Successfully evolved seasonal thresholds (`dry=0.333`, `monsoon=0.554`).
- **Extended Features**: Extracted 6 metrics (195 encroachment alerts, 12 high-hazard landslide patches, $789K tons carbon stock valued at $11.8M USD).
- **Interactive GIS Dashboard**: Fully implemented React frontend and FastAPI backend.

---

## Slide 12: Plan of Action — Semester 8 (Proposed Work)
- **Dynamic Bounding Box Input**: Add custom region drawing controls (`leaflet-draw`) on the React GIS Map.
- **Real-Time Google Earth Engine Ingestion**: Connect the backend to the Google Earth Engine Python API to fetch Sentinel-2 imagery dynamically for *any* custom forest coordinates on Earth.
- **Detailed Landslide Diagnostic Engine**: Fetch SRTM DEM elevation data and CHIRPS Daily Precipitation datasets on-the-fly to output landslide probability curves and diagnostic reason logs.
- **Production Deployment**: Host the backend and frontend on a cloud server (AWS/GCP).
