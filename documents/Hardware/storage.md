# Storage Information

This document provides PowerShell commands to inspect physical disks, partitions, and logical volumes.

## Physical Disks

Get information about connected physical drives (HDD, SSD, NVMe).

```powershell
Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, BusType, SpindleSpeed, Size, HealthStatus
```

### Concise View (User Example)
```powershell
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, BusType, Size
```

**Example Output:**
```text
FriendlyName            MediaType BusType          Size
------------            --------- -------          ----
Samsung SSD 990 PRO 2TB SSD       NVMe     2000398934016
Samsung SSD 990 PRO 1TB SSD       NVMe     1000204886016
Msft Virtual Disk       SSD       File Backed Virtual 33554432
```

Alternatively, using CIM:

```powershell
Get-CimInstance Win32_DiskDrive | Select-Object Model, InterfaceType, Size, MediaType, Caption
```

## Logical Disks (Volumes)

Check drive letters, file system types, and free space.

```powershell
Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID, VolumeName, FileSystem, Size, FreeSpace
```

## Partitions

List all partitions on all disks.

```powershell
Get-Partition | Select-Object DiskNumber, PartitionNumber, DriveLetter, Type, Size, IsBoot
```
