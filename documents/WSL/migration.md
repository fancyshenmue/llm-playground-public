# Migrating WSL Distributions

This guide details how to move a WSL distribution (e.g., Ubuntu 24.04) to a different drive or location.

## Prerequisites

- Ensure WSL is installed and running.
- Ensure you have sufficient disk space on the target drive `D:\`.
- **Note:** Replace `Ubuntu-24.04` with your specific distribution name if different.

## Step-by-Step Guide

### 1. Shutdown WSL
Ensure all WSL instances are stopped before proceeding.

```powershell
wsl --shutdown
```

### 2. Export the Distribution
Export the current distribution to a tar file.

```powershell
# Create directory for export if it doesn't exist
mkdir D:\WSL\Export

# Export the distribution
wsl --export Ubuntu-24.04 D:\WSL\Export\ubuntu_24_04.tar
```

### 3. Unregister the Old Distribution
This removes the distribution from WSL. **Warning:** This will delete the existing filesystem for this distro, so ensure the export was successful first.

```powershell
wsl --unregister Ubuntu-24.04
```

### 4. Import to New Location
Import the tar file to the new location.

```powershell
# Create directory for the new instance
mkdir D:\WSL\Ubuntu-24.04

# Import the distribution
wsl --import Ubuntu-24.04 D:\WSL\Ubuntu-24.04 D:\WSL\Export\ubuntu_24_04.tar --version 2
```

### 5. Verify Installation
Start the distribution and check the user. You will likely be logged in as `root` by default.

```powershell
wsl -d Ubuntu-24.04
whoami
exit
```

### 6. Restore Default User (PowerShell)
By default, imported distros log in as root. Use this PowerShell command to set the default user back to your standard user (usually UID 1000).

```powershell
Get-ItemProperty HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\* | Where-Object { $_.DistributionName -eq "Ubuntu-24.04" } | Set-ItemProperty -Name DefaultUid -Value 1000
```

### 7. Cleanup
Remove the export tar file to save space.

```powershell
Remove-Item D:\WSL\Export\ubuntu_24_04.tar
```
