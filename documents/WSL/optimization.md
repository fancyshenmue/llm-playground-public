# Optimizing WSL Disk Space

Over time, the WSL virtual hard disk (VHDX) grows as you write data but does not automatically shrink when data is deleted. This guide shows how to manually compact the VHDX file.

## Prerequisites

- You must know the path to your VHDX file.
- WSL must be completely shut down.

## Step-by-Step Guide

### 1. Identify VHDX Location
If you followed the migration guide, your VHDX is at `D:\WSL\Ubuntu-24.04\ext4.vhdx`.

### 2. Shutdown WSL

```powershell
wsl --shutdown
```

### 3. run Diskpart
Open a command prompt or PowerShell as **Administrator** and run:

```cmd
diskpart
```

### 4. Compact the Disk
Run the following commands within the `DISKPART>` prompt:

```diskpart
select vdisk file="D:\WSL\Ubuntu-24.04\ext4.vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit
```

> **Note:** The `compact vdisk` step may take some time depending on the size of the disk and the speed of your drive.
