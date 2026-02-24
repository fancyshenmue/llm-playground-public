# Motherboard & System Information

This document covers commands to identify the motherboard model, BIOS version, and system slots.

## Motherboard (BaseBoard)

Get the manufacturer, product (model), and serial number of the motherboard.

```powershell
Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, SerialNumber, Version
```

## BIOS / UEFI

Check the BIOS version, release date, and manufacturer.

```powershell
Get-CimInstance Win32_BIOS | Select-Object Manufacturer, Name, Version, ReleaseDate, SerialNumber, SMBIOSBIOSVersion
```

## System Slots (PCIe, PCI)

List available expansion slots on the motherboard and their status.

```powershell
Get-CimInstance Win32_SystemSlot | Select-Object SlotDesignation, Usage, Status, CurrentUsage, MaxDataWidth
```

### Slot Status & HotPlug (User Example)
Use `Get-WmiObject` or `Get-CimInstance` to view slot population and health.

```powershell
Get-WmiObject Win32_SystemSlot | Select-Object SlotDesignation, CurrentUsage, Status, SupportsHotPlug
```

**Example Output:**
```text
SlotDesignation CurrentUsage Status SupportsHotPlug
--------------- ------------ ------ ---------------
PCIEX16(G5)_1              4 OK     False
PCIEX16(G5)_2              4 OK     False
PCIEX4(G4)                 5 Error  False
M.2_1                      4 OK     False
M.2_2                      3 OK     False
M.2_3                      5 Error  False
```

## Computer System

General system information including model and total physical memory.

```powershell
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, TotalPhysicalMemory, SystemType
```
