import pandas as pd
import numpy as np

df = pd.read_csv('output.csv')

W1, W2, W3 = 1.0, 1.0, 1.0 

df['Cost'] = (W1 * df['Average_TAT']) + (W2 * df['Average_RT']) + (W3 * df['CV_Fairness'])

# --- A. Create a Consistent Workload ID ---
# Use the input factors to create a unique, non-random ID for the workload configuration
df['Workload_Config_ID'] = (
    df['cpu'].astype(str) + '_' + 
    df['io'].astype(str) + '_' + 
    df['nice'].astype(str) + '_' + 
    df['mem_load'].astype(str)
)

# Your DataFrame will now have 3 rows per Workload_Config_ID (CFS, tickless, rustland)
# --- STEP 1: Calculate Cost C and Identify Optimal Policy ---

optimal_rename_map = {
    'scheduler': 'Optimal_Policy', 
    'Cost': 'Optimal_Cost'
}

# for col in AVG_FEATURE_COLUMNS:
#     optimal_rename_map[col] = f'Optimal_{col}'

# Find the Optimal Policy and Cost for each Workload_ID
optimal_policy_info = df.loc[
    df.groupby('Workload_Config_ID')['Cost'].idxmin()
][['Workload_Config_ID', 'scheduler', 'Cost']].rename(columns=optimal_rename_map)

df = pd.merge(df, optimal_policy_info, on='Workload_Config_ID', how='left')

df['Z_Score'] = df['Cost'] - df['Optimal_Cost']

# 1. Pivot the costs to align C_CFS, C_RR, and C_FIFO (150 rows)
cost_pivot = df.pivot_table(index='Workload_Config_ID', columns='scheduler', values='Cost')
# 2. Calculate the 6 Z Targets simultaneously
z_targets_wide = pd.DataFrame(index=cost_pivot.index)

# # Example: CFS as Baseline
z_targets_wide['Z_CFS_rustland'] = cost_pivot['rustland'] - cost_pivot['CFS']
z_targets_wide['Z_CFS_tickless'] = cost_pivot['tickless'] - cost_pivot['CFS']

# # Example: rustland as Baseline
z_targets_wide['Z_rustland_CFS'] = cost_pivot['CFS'] - cost_pivot['rustland']
z_targets_wide['Z_rustland_tickless'] = cost_pivot['tickless'] - cost_pivot['rustland']

z_targets_wide['Z_tickless_CFS'] = cost_pivot['CFS'] - cost_pivot['tickless']
z_targets_wide['Z_tickless_rustland'] = cost_pivot['rustland'] - cost_pivot['tickless']

z_targets_wide.to_csv('output_with_costs.csv', index=False)

# --- 0. Setup and Constants (Ensure these match your actual data) ---

# Replace 'df' and 'z_targets_wide' with the actual names of your DataFrames
# Assuming df is your 450-row raw data with all features, and z_targets_wide is the 150-row Z table.
# For execution purposes, I will use placeholder names if they don't exist.

# The 7 base feature columns (already mean/aggregate values)
BASE_FEATURE_COLUMNS = [
    'T_run_queue', 'T_nvcsw_rate', 'T_vcsw_rate', 'T_cpu_percent', 
    'T_io_read_rate', 'T_io_write_rate', 'T_swap_rate'
]
SCHEDULERS = ['CFS', 'rustland', 'tickless']


# --- 1. Prepare Feature Maps (X_Current and X_Target) ---

# Create a clean DataFrame containing only the workload ID and the 7 features
features_base_df = df[['Workload_Config_ID', 'scheduler'] + BASE_FEATURE_COLUMNS].copy()

# A. Create X_Current Map (Features used when starting from a policy)
CURRENT_FEATURE_COLUMNS = [f'Current_{col}' for col in BASE_FEATURE_COLUMNS]
current_rename_map = dict(zip(BASE_FEATURE_COLUMNS, CURRENT_FEATURE_COLUMNS))

current_features_map = features_base_df.rename(columns=current_rename_map)
# current_features_map = current_features_map.drop_duplicates(subset=['Workload_Config_ID', 'scheduler'])


# B. Create X_Target Map (Features used when switching TO a policy)
TARGET_FEATURE_COLUMNS = [f'Target_{col}' for col in BASE_FEATURE_COLUMNS]
target_rename_map = dict(zip(BASE_FEATURE_COLUMNS, TARGET_FEATURE_COLUMNS))

target_features_map = features_base_df.rename(columns=target_rename_map)
# target_features_map = target_features_map.drop_duplicates(subset=['Workload_Config_ID', 'scheduler'])

if 'Workload_Config_ID' not in z_targets_wide.columns:
    z_targets_wide.reset_index(inplace=True)

# --- 2. Melt (Unpivot) the Z Targets ---

# Identify the columns that contain the Z scores
z_cols = [col for col in z_targets_wide.columns if col.startswith('Z_')]

# Melt the wide Z table into a long format (150 workloads * 6 switches = 900 rows)
z_targets_long = z_targets_wide.melt(
    id_vars=['Workload_Config_ID'],
    value_vars=z_cols,
    var_name='Z_Switch_Name',
    value_name='Differential_Cost_Z'
)

# Extract the Current and Target policies from the Z column name (e.g., 'Z_CFS_rustland' -> CFS, rustland)
z_targets_long['Current_Policy'] = z_targets_long['Z_Switch_Name'].apply(lambda x: x.split('_')[1])
z_targets_long['Target_Policy'] = z_targets_long['Z_Switch_Name'].apply(lambda x: x.split('_')[2])

# Drop the intermediate Z column name
z_targets_long.drop(columns=['Z_Switch_Name'], inplace=True)


# --- 3. Final Merge: Combine Z, X_Current, and X_Target ---

# Start with the 900-row Z table
final_training_set = z_targets_long.copy()

# Merge 1: Join X_Current Features (7 columns)
final_training_set = pd.merge(
    final_training_set,
    current_features_map,
    left_on=['Workload_Config_ID', 'Current_Policy'],
    right_on=['Workload_Config_ID', 'scheduler'],
    how='left'
).drop(columns=['scheduler'])

# Merge 2: Join X_Target Features (7 columns)
final_training_set = pd.merge(
    final_training_set,
    target_features_map,
    left_on=['Workload_Config_ID', 'Target_Policy'],
    right_on=['Workload_Config_ID', 'scheduler'],
    how='left'
).drop(columns=['scheduler'])


# --- 4. Final Output and Verification ---

# Define the final feature list for verification
FINAL_X_COLS = CURRENT_FEATURE_COLUMNS + TARGET_FEATURE_COLUMNS

print(f"✅ Final Training Dataset created with {len(final_training_set)} rows.")
print(f"    (150 Workloads * 6 Switch Scenarios = 900 rows)")
print(f"    Features (X) count: {len(FINAL_X_COLS)} (7 Current + 7 Target)")
print(f"    Target (Y) column: Differential_Cost_Z")

# Display the resulting table structure
print("\n--- Example Feature Row Structure (X-vectors and Target Z) ---")
print(final_training_set[['Workload_Config_ID', 'Current_Policy', 'Target_Policy', 'Differential_Cost_Z'] + FINAL_X_COLS].head().T)

# Save the final training data
final_training_set.to_csv('ml_training_data_900_samples.csv', index=False)