---
title: "5G SRS Indoor Positioning Dataset"
description: "This dataset contains pre-processed spatial features extracted from uplink Sounding Reference Signals (SRS) in a 5G ISAC (Integrated Sensing and Communication) indoor environment. Utilizing a O-RAN setup, it provides real-time extracted CIR taps, frequency-domain amplitudes, and spatial footprints to enable AI/ML-driven localization and human-blockage detection."
keywords: "5G, SRS, Indoor Positioning, Fingerprinting, Random Forest, OpenAirInterface, O-RAN, Machine Learning, AI/ML, Dataset, Radio Unit"
category: "Dataset"
image: "/images/artifacts/datasets/datasets-default-artifact.png"

# Published Date
date: 2026-06-01

# Weight: Optional number for sorting (lower = higher priority)
weight: 
icon: "/images/icons/dataset-icon.png"

# Managed by /content/authors, Mention title only
artifact_authors:
  - "Ping-Yu Hsieh (Karl)"
  - "Chieh-Chun Chen (CC)"

badge: 
  enable: false 
  text: "Release" 
  backgroundColor: "#22C55E" 
  textColor: "#FFFFFF"

# version (year.month / major.minor.patch)
version: "1.0.0"

# Status: develop | release
grade: "release"

# Ratings: 1-5
#ratings: 5

# Metrics
downloads: 0 
likes: 0

# Tags:
# O-RAN/Monitor/Control/Machine Learning/Artificial Intelligent
# OpenAirInterface/srsRAN/Amarisoft/Open5GS/LITEON/Benetel
tags:
  - OpenAirInterface
  - O-RAN
  - Machine Learning
  - Artificial Intelligent

# Software License, Product License
license: 
  enable: true 
  name: "CC BY-SA 4.0" 
  url: "https://creativecommons.org/licenses/by-sa/4.0/"

# Base: xapp_rapp, network, model, dataset, agent
category_specific:
  - title: "Platform" 
    values: ["OpenAirInterface", "O-RAN"]
  - title: "Data Format" 
    values: ["HDF5"]
  - title: "Network" 
    values: ["5G Standalone"]
  - title: "Hardware" 
    values: ["5G UE, Indoor Radio Units, Directional Antennas"]

source: 
  enable: true 
  list: 
    - label: "indoor-positioning-dataset" 
      link: "https://github.com/bubbleran/open-telco-datasets/tree/main/datasets/indoor-positioning"

# Certified
certified: 
  enable: false

# Managed by /content/artifact-external-resources, Mention filename only without ".md"
external_resources: 
  enable: true 
  title: "Related Publications & Demos" 
  artifact_references: 
    - slug: "[indoor-positioning-demo-video](https://youtu.be/hAeIbw2aTQQ?si=zPmfOb9OaWVTelm4)"

# Mention Artifact filename only without ".md"
related_artifacts: 
  enable: false

comments: 
  enable: false 
---

## Detailed Description

This dataset provides pre-processed spatial features extracted from uplink Sounding Reference Signals (SRS) in a indoor environment. Utilizing a O-RAN 7.2 fronthaul setup with a 4 external antenna array, the data is designed to be immediately ML-ready, avoiding the heavy I/O overhead of raw I/Q signals.

### Key Extracted Factors
Instead of raw I/Q samples, the dataset provides essential pre-processed spatial and signal parameters:
*   **Time-domain CIR Taps:** Normalized Power Delay Profile (PDP) capturing multipath reflections.
*   **Phase Differences:** Relative phase shifts between antennas, encoded to capture spatial variance.
*   **Signal Power (dB):** Total received power across all antennas.
*   **Spatial Power Differentials:** Received power differences (dx, dy) across the antenna array to determine general spatial quadrants.
*   **Frequency-domain Amplitudes:** Subcarrier amplitudes optimized for tracking sudden physical disturbances.

### Supported Use Cases
The dataset is structured to support three primary machine learning-driven use cases:

1.  **Real-Time Human Blockage Detection:** 
    Utilizing frequency-domain signatures and sudden received power (dB) drops to instantly detect physical disturbances, such as human movement or Line-of-Sight (LoS) blockages in the sensing area.
2.  **Single-UE Indoor Localization:** 
    Mapping the extracted multi-antenna CIR footprints to physical 2D ground-truth coordinates. This enables the training of models (e.g., Random Forest) to accurately estimate a single device's position and Angle of Arrival (AoA) in a multipath-heavy indoor environment.
3.  **Multi-UE Spatial Tracking:** 
    Handling simultaneous signal reflections and transmissions from multiple devices. This challenges spatial tracking algorithms to process overlapping signatures, resolve spatial ambiguities, and track multiplexed targets concurrently.
