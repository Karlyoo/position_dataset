import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime

def load_and_parse_dataset(jsonl_file):
    """
    Read and parse the JSONL file, expanding important features into a DataFrame for easy analysis.
    """
    data = []
    with open(jsonl_file, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                
                # Basic filtering: skip records without coordinates or anomalous data
                if 'x' not in record or 'y' not in record:
                    continue
                    
                # Create a flattened dictionary for easy conversion to DataFrame
                parsed_record = {
                    'timestamp': record.get('timestamp', 0),
                    'datetime': record.get('datetime', ''),
                    'x': record.get('x'),
                    'y': record.get('y'),
                    'dx': record.get('dx'),
                    'dy': record.get('dy'),
                    'ueid': str(record.get('ueid', '1')), # Default to 1 (Single UE)
                }
                
                # Extract signal strength (dB) for 4 antennas
                db_vals = record.get('db', [0, 0, 0, 0])
                for i in range(4):
                    parsed_record[f'db_ant_{i}'] = db_vals[i]
                
                # Extract Channel Impulse Response (CIR) features
                # cir_feat typically contains 24 values: first 16 are Tap energies, last 8 are phase features
                cir = record.get('cir_feat', [])
                if len(cir) == 24:
                    for i in range(16):
                        parsed_record[f'cir_tap_{i}'] = cir[i]
                        
                data.append(parsed_record)
            except Exception as e:
                print(f"Parsing error: {e}")
                continue
                
    df = pd.DataFrame(data)
    
    # Convert datetime strings to actual datetime objects for easier time-axis plotting
    if not df.empty and 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        
    return df

def plot_comprehensive_analysis(df):
    """
    Generate three important analysis charts using the parsed DataFrame.
    This demonstrates the richness of the dataset's contents.
    """
    if df.empty:
        print("[!] Dataset is empty, cannot plot.")
        return
        
    print(f"[*] Successfully loaded {len(df)} records. Generating analysis charts...")

    # ==========================================
    # Chart 1: Spatial Trajectory Plot
    # Purpose: Visualize the actual movement path of the UE and the smoothness of the trajectory.
    # ==========================================
    plt.figure(figsize=(8, 8))
    plt.plot(df['x'], df['y'], marker='.', markersize=4, linestyle='-', alpha=0.7, color='#22c55e', label='UE Trajectory')
    plt.scatter(0, 0, color='red', marker='X', s=150, label='RU (Base Station)')
    
    # Mark start and end points
    plt.scatter(df['x'].iloc[0], df['y'].iloc[0], color='blue', s=100, label='Start')
    plt.scatter(df['x'].iloc[-1], df['y'].iloc[-1], color='orange', s=100, label='End')
    
    plt.title("ISAC Dataset: UE Trajectory Analysis")
    plt.xlabel("X Position (m)")
    plt.ylabel("Y Position (m)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.savefig("Fig1_Trajectory.png", dpi=150)
    plt.close()

    # ==========================================
    # Chart 2: Signal Strength (dB) Variation Over Time (4 Antennas)
    # Purpose: Understand signal fading phenomena as the object moves.
    #          This is one of the core features for ML models to estimate direction.
    # ==========================================
    plt.figure(figsize=(10, 5))
    for i in range(4):
        plt.plot(df['datetime'], df[f'db_ant_{i}'], alpha=0.8, label=f'Antenna {i}')
        
    plt.title("Signal Strength (dB) Variation Over Time")
    plt.xlabel("Time")
    plt.ylabel("Signal Strength (dB)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig("Fig2_Signal_Strength.png", dpi=150)
    plt.close()

    # ==========================================
    # Chart 3: CIR Feature Heatmap (Channel Impulse Response Taps)
    # Purpose: Display multipath effects. The energy variation across 16 taps
    #          reveals characteristics of reflected waves in the environment,
    #          which is a crucial input for advanced AI positioning.
    # ==========================================
    # Extract tap-related columns (cir_tap_0 to cir_tap_15)
    tap_cols = [f'cir_tap_{i}' for i in range(16)]
    if set(tap_cols).issubset(df.columns):
        plt.figure(figsize=(10, 6))
        # Transpose the data (Taps on Y-axis, Time on X-axis)
        cir_matrix = df[tap_cols].to_numpy().T 
        
        plt.imshow(cir_matrix, aspect='auto', cmap='viridis', interpolation='nearest',
                   extent=[0, len(df), 15, 0])
        plt.colorbar(label='Normalized Energy')
        plt.title("CIR Multipath Delay Profile (16 Taps) Over Time")
        plt.xlabel("Sample Index (Time Step)")
        plt.ylabel("Tap Index (Delay)")
        plt.savefig("Fig3_CIR_Heatmap.png", dpi=150)
        plt.close()
    
    print("[*] Analysis complete! Generated files:")
    print("    1. Fig1_Trajectory.png (Trajectory plot)")
    print("    2. Fig2_Signal_Strength.png (Signal strength plot)")
    print("    3. Fig3_CIR_Heatmap.png (CIR multipath heatmap)")

if __name__ == "__main__":
    # Use the filename of the single UE dataset you just uploaded
    dataset_file = "dataset_single_ue.jsonl" 
    
    # 1. Load and parse the data
    df_parsed = load_and_parse_dataset(dataset_file)
    
    # 2. Perform visualization
    plot_comprehensive_analysis(df_parsed)
    
    # 3. Future expansion suggestions:
    # If someone taking over wants to train a new AI model (e.g., RandomForest, Neural Network),
    # they can directly export df_parsed to a CSV file.
    # Input Features (X) = db_ant_0~3 + cir_tap_0~15 + additional phase features
    # Target (Y) = x, y coordinates
    # df_parsed.to_csv("parsed_dataset.csv", index=False)
