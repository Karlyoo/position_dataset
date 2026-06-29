# Dataset folder
## training model
This folder contains the environment JSON files used for training.

Contents
- `labphy_env.json` — raw environment capture (large time-series of samples). Leave the canonical copy in the repo root of `ue_position` and/or add a copy here if you prefer a local dataset copy.


How this data is collected and used

- How the data is collected:
	- The raw SRS IQ files are written by the C xApp ( `xapp_oran_llc_srs.c`) into the configured `DATA_DIR`. The filenames look like `iq_srs_{kind}_ant{N}_symbol{...}_nbid..._ueid....txt`.
	- The Python worker in `position_lab.py` reads the 4 antenna files that share the same timestamp, merges them into one sample, and can also collect labeled data through the web UI or the `/calib/capture` API.

- What each sample field means:
	- `t`: Unix timestamp (float) for the sample.
	- `x`, `y`: Ground-truth coordinates (float) used as training targets.
	- `dx`, `dy`: Left-right and top-bottom energy differences across the four antennas (float), derived from the dB energies.
	- `db_raw`: Raw antenna energy values in dB (list of 4 floats), ordered according to `ant_map`.
	- `cir_feat`: CIR features (list of 24 floats) = normalized PDP taps (`cir_taps` taps, usually 16) + per-antenna relative phase encoded as cos/sin values (8 floats total), giving 24 dimensions.
	- `cir_taps`: Number of CIR taps used (int), for example 16.
	- `agg_n`: Aggregation count (int), meaning how many stable snapshots were accumulated for this sample.
	- `label`: Optional text label (string), such as a position ID or note.
	- Other fields may appear, such as `cir_feat_smooth_n` and `db_smooth_n`, which describe smoothing or buffer length.

- How the JSON becomes the 32-D training feature:
	- The `_build_feature_from_sample()` function in `random_forest.py` shows the exact pipeline:
		1. Read `cir_feat` (24 dims), `db_raw` (4 dims), and `dx`, `dy` from the sample.
		2. Compute `mean_db` and `max_db`.
		3. Concatenate them as `feat = cir_feat + db_raw + [dx, dy, mean_db, max_db]` → 32 dimensions.

- Quick usage steps:
	1. Put `labphy_env.json` in `ue_position/`
	2. Train the model:
		```bash
		python3 random_forest.py
		```
		- Note: `random_forest.py` expects `labphy_env.json` in the same directory, or you can change the `file_path` variable in the script.

- Notes:
	- If a sample is missing `cir_feat` or `db_raw` (or contains NaN/Inf), it will be skipped. Check the valid sample count with `inspect_dataset.py` before training.
	- The `t` field is a Unix epoch timestamp. Convert it if you need human-readable time or alignment with other logs.
	- To reproduce the capture flow, start `position_lab.py` and use the Capture or Auto Capture buttons in the UI. The captured data will be added to the calibration state or saved as a downloadable JSON.
	- The training script `random_forest.py` produces three deployment files: the trained regressor (`rf_regressor_v26.pkl`), the feature scaler (`scaler_v26.pkl`), and the metadata file (`model_meta_v26.json`). The runtime script `position.py` loads these files, rebuilds the same 32-D feature from live SRS data, scales it, and predicts the final `(x, y)` coordinate.

- What the two `.pkl` files are for:
	- `rf_regressor_v26.pkl` is the trained RandomForestRegressor itself. It stores the learned tree ensemble that maps the 32-D feature vector to the final 2-D output `(x, y)`. In other words, this file contains the model brain.
	- `scaler_v26.pkl` is the fitted StandardScaler used during training. It stores the mean and standard deviation of each of the 32 input features, so the runtime code can normalize live features in the same way as the training data.
	- Both files are required together. If you load the regressor without the same scaler, the feature values seen by the model will be different from training, and the prediction quality will drop or fail.
	- In `position.py`, the flow is: build live 32-D features from current SRS samples -> call `scaler.transform([live_features])` -> call `rf_regressor.predict(...)` -> get predicted `(x, y)`.
	- `model_meta_v26.json` is not used for prediction directly. It is a safety and documentation file that records the feature spec, model version, tap count, and evaluation metrics such as MAE and RMSE.

- Why this matters:
	- The regressor learns from normalized input, not raw values.
	- The scaler makes live inference consistent with training.
	- The metadata file helps verify that the runtime feature dimension is still 32 and matches the trained model version.
## real test
### 1. `detection_dataset.jsonl` (Real-Time SRS plot)
**Description:** To optimize for high sampling rates and minimize file I/O overhead, the raw time-domain Channel Impulse Response (CIR) arrays have been deliberately omitted. Instead, this dataset captures the essential frequency-domain signatures needed to instantly detect sudden physical disturbances (e.g., human movement or obstacles) in the sensing environment.

**Key Features:**
* `timestamp`: High-precision hardware epoch time for frame synchronization.
* `db`: Total received power (dB) across the 4 antennas. Sudden drops below the baseline median reliably indicate potential LoS blockages.
* `amp_db`: Frequency-domain amplitude across subcarriers (rounded and optimized for storage).
* `phase`: Subcarrier phase angles (radians). Phase shifts serve as critical indicators of spatial variance and reflection changes.
#### In this dataset,I first put the UE near antenna3 and walk by twice. Then move the UE near to antenna1 and walk by again.

### 2. `dataset_single_ue.jsonl` (Single-UE Localization)
**Description:** This dataset maps complete radio channel profiles to physical ground-truth coordinates. It is used to train and evaluate our core machine learning models to accurately estimate a single user's 2D position and transmission angle based on multipath propagation characteristics.
**Key Features:**
1. Spatial Coordinates & Localization Output
* These parameters represent the final geometric output after passing through the Random Forest regressor and the Exponential Moving Average (EMA) filter.
* `x / y`: The final estimated 2D coordinates of the User Equipment (UE) in meters, relative to the Radio Unit (RU) at (0,0).
* `target_angle_deg`: The estimated Angle of Arrival (AoA) of the UE, calculated directly from the x and y coordinates using the arctangent function (math.atan2).
* `quadrant`: A string indicating the current status of the UI/system. "Regressor Active" means the AI model successfully generated the coordinates. If the model fails or is initializing, it defaults to "Init".

2. Core Machine Learning Features (The input of model)
* `cir_feat`: The 24-dimensional spatial fingerprint vector. Based on your code, this is constructed by:
  - Indices 0-15: The normalized Power Delay Profile (PDP) across 16 time-domain taps (cir_taps). It aligns the peak signal paths across antennas to understand multipath reflections.
  - Indices 16-23: The relative phase differences (represented as cosine and sine pairs) of the peak signal between the reference antenna and the other antennas.
* `db / db_raw`: An array of 4 values representing the median-smoothed Total Received Power (in decibels) for each of the 4 antennas. This is used by the model to understand macro-level signal strength and distance.
* `dx / dy`: A heuristic calculation of power differentials across the antenna array. dx compares the right vs. left antennas, and dy compares the top vs. bottom antennas. The model uses this to help determine the general quadrant of the UE.

3. Signal Filtering & Stability Metrics
These parameters track how the system handles noisy 5G SRS signals and filters out anomalies before making a prediction.
* `energies`: The raw, un-converted sum of squared I/Q samples (I^2 + Q^2) for each antenna.
* `db_raw_instant`: The instantaneous decibel power of the current frame, before any median smoothing is applied.
* `db_smooth_n`: The number of historical frames currently stored in the rolling buffer to calculate the median db (up to a maximum defined by DB_MEDIAN_N).
* `cir_feat_smooth_n`: The number of historical frames used to calculate the median of the cir_feat fingerprint.
* `db_jump_max`: The maximum sudden change (delta) in decibels across any antenna between the db_raw_instant and the smoothed db.
* `pred_reject`: A string indicating if the current frame's prediction was thrown out. If it is empty (""), the frame was accepted. If it shows "noisy_srs" (because db_jump_max was too high) or "nan_pred", the system ignores the AI output and holds the previous coordinate.
#### In this dataset,I hold the UE and walk around the lab in a U shape(end in the door).

### 3. `dataset_multiues.jsonl` (Multi-UE Spatial Tracking and collision detection)
**Description:** Extending the baseline localization capabilities, this dataset introduces user multiplexing to handle simultaneous signal reflections and transmissions from multiple devices. It challenges the tracking algorithms to resolve spatial ambiguities and process overlapping signals concurrently.

**Key Features:**
* Contains all core spatial features present in the single-UE dataset (`cir_feat`, `x`, `y`, `energies`, `target_angle_deg`).
* `cir_feat`, `energies`: Extracted spatial fingerprints and energy distributions, now containing overlapping signatures from multiple sources.
* `ueid`: Specific User Equipment Identifier. Essential for filtering, isolating multiplexed targets, and evaluating the scalability of the Service Model (SM) in complex scenarios.
* `x`, `y`, `target_angle_deg`: Ground-truth physical coordinates and Angle of Arrival (AoA) for the specific `ueid`.
* `heatmap` (`x`, `y`, `prob`): The spatial probability distribution generated by the model,assessing prediction certainty, and resolving spatial ambiguities.
