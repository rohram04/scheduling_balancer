# -----------------------------------------------------------------------------
# Modular Stress Profile Library for Dynamic Workload Generation
#
# These are the atomic building blocks used to create complex dynamic workloads.
# The 'params' dictionary defines the stress-ng command line arguments.
# -----------------------------------------------------------------------------

# Single, unified duration for every stress phase.
# NOTE: 30 seconds is used to ensure enough time for system metrics 
# to stabilize and for accurate time-series data collection.
PHASE_DURATION_SECONDS = 30 
TIMEOUT_VALUE = f'{PHASE_DURATION_SECONDS}s'

STRESS_PROFILES = {
    # CATEGORY 1: High-Intensity Extremes (5 Profiles)
    
    # P1: High CPU Utilization (Simulates heavy computation)
    'P1_CPU_BOUND': {
        'params': {
            'cpu': 8,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'CPU_INTENSE'
    },
    
    # P2: I/O and Disk Contention (Simulates file access/database queries)
    'P2_IO_INTENSE': {
        'params': {
            'io': 4,
            'hdd': 2,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'IO_INTENSE'
    },

    # P3: Mutex Contention (Simulates heavy concurrency/synchronization issues - corrected from 'lock')
    'P3_LOCK_CONTENTION': {
        'params': {
            'mutex': 4,
            'mutex-ops': 100, # High rate of mutex operations per second
            'timeout': TIMEOUT_VALUE
        },
        'type': 'CONTENTION_INTENSE'
    },
    
    # P4: Context Switching (Simulates high number of threads/processes swapping in and out)
    'P4_CONTEXT_SWITCH': {
        'params': {
            'switch': 8,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'SWITCH_INTENSE'
    },

    # P5: Mixed Load (Simulates a blend of computation and memory usage)
    'P5_MIXED_MEM_CPU': {
        'params': {
            'cpu': 4,
            'mmap': 4,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'MIXED_LOAD'
    },

    # CATEGORY 2: Subtlety, Moderate, and Complex Edge Loads (9 Profiles)
    
    # P6: High Fork Rate (Simulates frequent, short-lived process creation overhead)
    'P6_FORK_INTENSE': {
        'params': {
            'fork': 16,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'LOW_CPU_OVERHEAD'
    },

    # P7: Memory/Cache Thrashing (Simulates poor memory locality)
    'P7_CACHE_THRASH': {
        'params': {
            'cache': 4,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'MEMORY_BOUND'
    },

    # P8: Moderate CPU/Moderate IO (The ambiguous state, hard for simple schedulers)
    'P8_MODERATE_MIX': {
        'params': {
            'cpu': 2,
            'io': 2,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'MODERATE_MIXED'
    },
    
    # P9: CPU/Mutex Contention Mix (High concurrent and synchronization demand)
    'P9_CPU_LOCK_MIX': {
        'params': {
            'cpu': 4,
            'mutex': 2,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'HIGH_CONTENTION_MIX'
    },
    
    # P11: Mutex and Switch Mix (Critical pathology where frequent switching exacerbates locking delays)
    'P11_LOCK_SWITCH_MIX': {
        'params': {
            'mutex': 4,
            'mutex-ops': 100,
            'switch': 4,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'CRITICAL_CONCURRENT_MIX'
    },

    # P17: I/O and Mutex Mix (Simulates highly concurrent, I/O intensive databases)
    'P17_IO_LOCK_MIX': {
        'params': {
            'io': 3,
            'mutex': 3,
            'mutex-ops': 50,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'CRITICAL_CONCURRENT_MIX'
    },

    # P18: I/O and Switch Mix (Simulates high-throughput networking or web server)
    'P18_IO_SWITCH_MIX': {
        'params': {
            'io': 3,
            'switch': 4,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'CRITICAL_CONCURRENT_MIX'
    },

    # P19: CPU and Switch Mix (High CPU load running alongside high context switching)
    'P19_CPU_SWITCH_MIX': {
        'params': {
            'cpu': 4,
            'switch': 4,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'CRITICAL_CONCURRENT_MIX'
    },

    # P20: Mutex and Cache Mix (Mutex contention on data that also causes cache thrashing)
    'P20_LOCK_CACHE_MIX': {
        'params': {
            'mutex': 2,
            'mutex-ops': 50,
            'cache': 2,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'CRITICAL_CONCURRENT_MIX'
    },
    
    # CATEGORY 3: Low-Intensity Isolated Loads (5 Profiles)

    # P12: Low CPU (Isolated, light computation)
    'P12_LOW_CPU': {
        'params': {
            'cpu': 1,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'LOW_INTENSITY_CPU'
    },
    
    # P13: Low I/O (Isolated, light disk activity)
    'P13_LOW_IO': {
        'params': {
            'io': 1,
            'hdd': 1,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'LOW_INTENSITY_IO'
    },
    
    # P14: Low Mutex Contention (Isolated, light synchronization overhead)
    'P14_LOW_LOCK': {
        'params': {
            'mutex': 1,
            'mutex-ops': 20,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'LOW_INTENSITY_CONTENTION'
    },

    # P15: Low Context Switching (Isolated, light thread swapping)
    'P15_LOW_SWITCH': {
        'params': {
            'switch': 2,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'LOW_INTENSITY_SWITCH'
    },

    # P16: Low Cache Thrashing (Isolated, light memory pressure)
    'P16_LOW_CACHE': {
        'params': {
            'cache': 1,
            'timeout': TIMEOUT_VALUE
        },
        'type': 'LOW_INTENSITY_MEMORY'
    },
}

# List of all profile keys for rotation (Total 20 profiles now)
ALL_PROFILES = list(STRESS_PROFILES.keys())