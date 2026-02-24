# Processor & Graphics Information

This document details commands for retrieving CPU and GPU specifications.

## Processor (CPU)

Get detailed information about the CPU, including cores, threads, and clock speed.

```powershell
Get-CimInstance Win32_Processor | Select-Object Name, Manufacturer, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, SocketDesignation, ThreadCount
```

## Video Controller (GPU)

Get information about the graphics card(s), including VRAM and driver version.

```powershell
Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, VideoProcessor, CurrentHorizontalResolution, CurrentVerticalResolution
```

**Note:** `AdapterRAM` is returned in bytes. To view in GB, you can calculate it:

```powershell
Get-CimInstance Win32_VideoController | Select-Object Name, @{N="VRAM(GB)";E={$_.AdapterRAM / 1GB}}, DriverVersion
```
