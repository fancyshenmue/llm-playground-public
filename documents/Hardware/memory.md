# Memory Information

This document contains PowerShell commands to retrieve detailed information about the system's physical and virtual memory.

## Physical Memory (RAM)

Get details about installed RAM modules, including manufacturer, part number, serial number, and speed.

```powershell
Get-CimInstance Win32_PhysicalMemory | Select-Object Manufacturer, PartNumber, SerialNumber, Speed, ConfiguredClockSpeed, Capacity, DeviceLocator
```

**Example Output:**
```text
Manufacturer         : Kingston
PartNumber           : KF560C36-32
SerialNumber         : 185B0108
Speed                : 4800
ConfiguredClockSpeed : 4800
Capacity             : 34359738368
DeviceLocator        : DIMM 0
```

## Page File Usage

Check the size and current usage of the Windows Page File.

```powershell
Get-CimInstance Win32_PageFileUsage | Select-Object Name, AllocatedBaseSize, CurrentUsage, PeakUsage
```

**Example Output:**
```text
Name            AllocatedBaseSize CurrentUsage
----            ----------------- ------------
C:\pagefile.sys             30720          389
```

## Virtual Memory Statistics

View total and free virtual memory available to the operating system.

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVirtualMemorySize, FreeVirtualMemorySize, TotalVisibleMemorySize, FreePhysicalMemory
```

**Example Output:**
```text
TotalVirtualMemorySize FreeVirtualMemorySize
---------------------- ---------------------
             192614132             150234112
```
