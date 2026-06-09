# Dataset folder

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


