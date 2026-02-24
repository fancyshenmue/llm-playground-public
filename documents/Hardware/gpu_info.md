# GPU Information Commands

This document provides PowerShell and command-line instructions for retrieving detailed GPU information, specifically tailored for NVIDIA GPUs.

## Standard PowerShell Commands

Basic information using Windows Management Instrumentation (WMI/CIM).

```powershell
# Get basic video controller info
Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, VideoProcessor

# Get VRAM in GB
Get-CimInstance Win32_VideoController | Select-Object Name, @{N="VRAM(GB)";E={$_.AdapterRAM / 1GB}}, DriverVersion
```

## NVIDIA SMI (Recommended)

`nvidia-smi` is the command-line utility for the NVIDIA Management Library (NVML). It provides monitoring and management capabilities for each of NVIDIA's Tesla, Quadro, GRID and GeForce devices.

### 1. View Current Status (Dashboard)
Displays a summary of all GPUs, including driver version, CUDA version, fan speed, temperature, power usage, memory usage, and running processes.
```powershell
nvidia-smi
```

### 2. Continuous Monitoring
Refreshes the status every 1 second (similar to `top` or `watch` in Linux).
```powershell
nvidia-smi -l 1
```

### 3. Query Specific Metrics (CSV Format)
Useful for logging or programmatic parsing.

**Common Metrics:**
- `name`: GPU model name
- `memory.total`: Total VRAM
- `memory.used`: Used VRAM
- `memory.free`: Free VRAM
- `utilization.gpu`: GPU utilization percent
- `temperature.gpu`: Core temperature

**Command:**
```powershell
nvidia-smi --query-gpu=timestamp,name,pci.bus_id,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu --format=csv
```

### 4. Continuous Logging to CSV
Appends the metrics to a file every second.
```powershell
nvidia-smi --query-gpu=timestamp,name,memory.used,utilization.gpu --format=csv -l 1 > gpu_log.csv
```

### 5. List GPU Processes
Shows which applications are using the GPU and how much VRAM they are consuming.
```powershell
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```
