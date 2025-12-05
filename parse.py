import pandas as pd
import re
from typing import Dict, Any
import numpy as np

# Regex to capture the common start of every log line
# Groups: (Command), (PID/TID), (CPU), (Timestamp), (Event_Details)
LOG_PATTERN = re.compile(
    r'^\s*([\w\-]+)\s+(\d+)\s+\[(\d+)]\s+(\d+\.\d+):\s+(.*)$'
)

def parse_and_calculate_worker_metrics(log_file_path: str, workload_root_pid: int) -> Dict[str, float]:
    """
    Parses a perf script trace log, tracks worker lifecycles, and calculates 
    the Average TAT and Average RT for the entire experiment run.
    """
    worker_data: Dict[int, Dict[str, float | bool]] = {}

    # worker_data[workload_root_pid] = {
    #     'T_Arrival': None,  # Will be set to experiment_start_time later
    #     'T_First_CPU': None,
    #     'T_Completion': None,
    # }
    
    # Store the start and end time of the entire experiment for rate calculation
    experiment_start_time = float('inf')
    experiment_end_time = float('-inf')

    try:
        with open(log_file_path, 'r') as f:
            for line in f:
                match = LOG_PATTERN.match(line)
                if not match:
                    continue

                command, pid_str, cpu, timestamp_str, details = match.groups()
                timestamp = float(timestamp_str)
                pid = int(pid_str)

                # Update experiment duration trackers
                experiment_start_time = min(experiment_start_time, timestamp)
                experiment_end_time = max(experiment_end_time, timestamp)

                # --- 1. SCHED_PROCESS_FORK (Arrival Time, T_Arrival) ---
                if 'sched:sched_process_fork' in details:
                    # Look for the child_pid which is the new worker
                    child_pid_match = re.search(r'child_pid=(\d+)', details)
                    if child_pid_match:
                        worker_pid = int(child_pid_match.group(1))
                        
                        # Initialize worker tracking dictionary
                        if worker_pid not in worker_data:
                            worker_data[worker_pid] = {
                                'T_Arrival': timestamp,
                                'T_First_CPU': None,
                                'T_Completion': None,
                                'Total_CPU_Time': 0.0,
                                'T_Last_Scheduled_In': None
                            }
                
                # --- 2. SCHED_PROCESS_EXIT (Completion Time, T_Completion) ---
                elif 'sched:sched_process_exit' in details:
                    # The PID/TID in the main log column is the process exiting
                    if pid in worker_data:
                        worker_data[pid]['T_Completion'] = timestamp
                
                # --- 3. SCHED_SWITCH (First CPU Time, T_First_CPU) ---
                elif 'sched:sched_switch' in details:
                    # We are looking for the 'next_pid' which is scheduled in
                    if pid in worker_data and worker_data[pid]['T_Last_Scheduled_In'] is not None:
                        
                        time_slice = timestamp - worker_data[pid]['T_Last_Scheduled_In']
                        worker_data[pid]['Total_CPU_Time'] += time_slice
                        
                        # Reset the 'in' time, as the process is now off the CPU
                        worker_data[pid]['T_Last_Scheduled_In'] = None 
                    
                    # 2b. Track the process being scheduled IN (next_pid)
                    next_pid_match = re.search(r'==>\s+([\w\-]+):(\d+)\s+', details)
                    if next_pid_match:
                        next_pid = int(next_pid_match.group(2))
                        
                        if next_pid in worker_data:
                            # Record T_First_CPU (RT) only the first time
                            if worker_data[next_pid]['T_First_CPU'] is None:
                                worker_data[next_pid]['T_First_CPU'] = timestamp
                                
                            # Set the start of the current CPU slice for the next_pid
                            worker_data[next_pid]['T_Last_Scheduled_In'] = timestamp

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
        return {}

    # --- Step 2: Calculate Final Averages ---

    total_tat = 0.0
    total_rt = 0.0
    valid_tat_count = 0
    valid_rt_count = 0
    
    # Filter out workers that didn't complete (censored runs)
    for pid, data in worker_data.items():
        # FIX 2: Add final CPU slice if the worker was running at the end of the trace
        if data['T_Last_Scheduled_In'] is not None:
            time_slice = experiment_end_time - data['T_Last_Scheduled_In']
            data['Total_CPU_Time'] += time_slice
        
        if data['T_Arrival'] is not None and data['T_Completion'] is not None:
            # Calculate TAT
            tat = data['T_Completion'] - data['T_Arrival']
            total_tat += tat
            valid_tat_count += 1

            # Calculate RT
            if data['T_First_CPU'] is not None:
                rt = data['T_First_CPU'] - data['T_Arrival']
                total_rt += rt
                valid_rt_count += 1
            # Note: If T_First_CPU is null, it means the worker never ran, 
            # or the first run occurred outside the traced window (rare).

    # Handle division by zero if no workers completed
    avg_tat = total_tat / valid_tat_count if valid_tat_count > 0 else 0.0
    avg_rt = total_rt / valid_rt_count if valid_rt_count > 0 else 0.0

    cpu_times = []
    
    # 1. Collect all Total_CPU_Time for completed workers
    for pid, data in worker_data.items():
        # Only include workers with a completed TAT, as they represent full runs
        if data['T_Completion'] is not None:
             cpu_times.append(data['Total_CPU_Time'])
             
    if not cpu_times:
        return {'Average_TAT': avg_tat, 'Average_RT': avg_rt, 'CV_Fairness': 0.0, 'Total_Experiment_Duration': experiment_end_time - experiment_start_time}
        
    cpu_times_array = np.array(cpu_times)

    # 2. Calculate Mean and Standard Deviation using NumPy
    mean_time = np.mean(cpu_times_array)
    std_dev = np.std(cpu_times_array)

    # 3. Calculate the Coefficient of Variation (CV)
    # The CV is the fairness metric: StdDev / Mean
    cv_fairness = std_dev / mean_time if mean_time > 0 else 0.0

    return {
        'Average_TAT': avg_tat,
        'Average_RT': avg_rt,
        # The total duration is needed for calculating *rates* in a later step
        'Total_Experiment_Duration': experiment_end_time - experiment_start_time,
        'CV_Fairness': cv_fairness.item()
    }