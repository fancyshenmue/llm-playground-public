# Feature Updates - February 2026

## Project Restructuring & Axolotl Integration
**Date**: February 9, 2026

### Structural refinement
The project structure has been refined to better separate concerns, specifically isolating the Electron application and Docker deployments.

**Changes**:
1. **Electron App Location**: Explicitly defined at `cmd/node/llm-utils-desktop`.
2. **Deployments**: Moved to `deployments/docker-compose/`.
   - `lab/`: Main services (Ollama, Onyx, etc.)
   - `axolotl/`: Dedicated training stack.

### Advanced Training Stack (Axolotl)
Integrated Axolotl for advanced LLM fine-tuning, complementing the existing Kohya_ss LoRA workflow.

- **Capabilities**: Full fine-tuning and QLoRA for large models (e.g., Llama 3, Qwen 2.5).
- **Integration**: Managed via Docker Compose in `deployments/docker-compose/axolotl`.
- **Configuration**: Uses YAML-based configs for reproducible training runs.

---

# Feature Updates - January 2026

## Data Fetch Feature

### Initial Implementation (Shell Execution)
- Used `child_process.spawn()` to execute Go CLI
- Parsed stdout for progress tracking
- Quick to implement but had limitations

### Refactored Implementation (Binance API)
**Date**: January 19, 2026

**Why**: Better cross-platform compatibility, no external dependencies, proper error handling

**Changes**:
1. **Created `binance-client.ts`**:
   - Direct HTTPS calls to `api.binance.com/api/v3/klines`
   - Automatic pagination for limits > 1000
   - Progress callbacks for UI updates
   - Proper TypeScript types

2. **Updated `QuantService.fetchTradingData()`**:
   - Removed `spawn()` and shell execution
   - Import and use `BinanceClient` directly
   - Write CSV files using Node.js `fs/promises`
   - Handle large limits (100,000+) via pagination

**Technical Details**:
```typescript
// Before (Shell)
spawn('llm-utils', ['quant', 'fetch', '--symbol', 'BTCUSDT', ...])

// After (API)
const client = new BinanceClient()
const klines = await client.fetchAllKlines('BTCUSDT', '1h', startTime, endTime)
await this.saveKlinesToCSV(klines, filepath)
```

**Limit Handling**:
- `limit ≤ 1000`: Single API request
- `limit > 1000`: Automatic pagination + trim to limit
- Date range: Pagination from `startTime` to `endTime`

---

## Quant Analyst: Multi-Timeframe Intelligence

### Problem
When analyzing multiple timeframes (e.g., 1H, 4H, 1D, 1W) with the same candle count, each timeframe covers a vastly different time period:

- 1H × 200 candles = ~8 days
- 4H × 200 candles = ~33 days
- 1D × 200 candles = ~200 days
- 1W × 200 candles = ~3.8 years

This causes inconsistent LLM analysis as the context windows don't align.

### Solution: Intelligent Candle Limit Adjustment
**Date**: January 19, 2026

**Implementation**:
1. Detect all timeframes from input filenames
2. Find the largest timeframe (e.g., 1W = 10,080 minutes)
3. Use user's limit as base for largest TF
4. Scale other TFs proportionally to cover same period

**Formula**:
```
adjustedLimit = baseLimit × (largestTF_minutes / currentTF_minutes)
```

**Example**:
```
Input: 4 files (1W, 1D, 4H, 1H), base limit = 200

Calculation:
- 1W (10,080 min): 200 candles (base)
- 1D (1,440 min): 200 × (10,080 / 1,440) = 1,400 candles (7x)
- 4H (240 min): 200 × (10,080 / 240) = 8,400 candles (42x)
- 1H (60 min): 200 × (10,080 / 60) = 33,600 candles (168x)

Result: All timeframes now analyze ~3.8 years of data
```

**Code Added** (`quant-service.ts`):
```typescript
// Map TF to minutes
private getTimeframeMinutes(timeframe: string): number {
    const tfMap = {
        '1M': 1, '5M': 5, '15M': 15, '30M': 30,
        '1H': 60, '2H': 120, '4H': 240,
        '1D': 1440, '1W': 10080
    };
    return tfMap[timeframe] || 60;
}

// Calculate proportional limit
private calculateCandleLimit(currentTf, largestTf, baseLimit): number {
    const ratio = this.getTimeframeMinutes(largestTf) /
                  this.getTimeframeMinutes(currentTf);
    return Math.ceil(baseLimit * ratio);
}
```

**Console Output**:
```
Detected timeframes: 1W, 1H, 1D, 4H
Largest timeframe: 1W (base limit: 200)
  1W: 200 candles (base)
  1H: 33600 candles (168.0x base)
  1D: 1400 candles (7.0x base)
  4H: 8400 candles (42.0x base)
```

**Impact**:
- ✅ Consistent temporal coverage across all timeframes
- ✅ Better LLM understanding of market structure
- ✅ Improved multi-timeframe strategy quality
- ✅ Automatic with zero user configuration

---

---

## LoRA Training & Dataset Tooling: Reliability & Display
**Date**: January 19, 2026

### Problem
The initial implementation for LoRA training had several issues:
1. **Performance**: SDXL training was extremely slow (1.5s/it vs 39s/it) due to missing optimization flags.
2. **Cancellation**: The "Cancel" button failed to kill Python subprocesses, leaving GPU memory leaked.
3. **UI State Persistence**: Refreshing the app caused the "Cancel" button and progress bar to disappear while training was still running.
4. **Log Readability**: ANSI codes and Carriage Returns (`\r`) rendered as "tofu" or messy output.

### Improvements
1. **Training Performance (10x Boost)**:
   - Implemented `accelerate` launcher with optimized threading.
   - Added automatic `--network_train_unet_only` when caching text encoder outputs (critical for SDXL).
   - Mapped 50+ missing Kohya parameters from Go CLI.
2. **Robust Cancellation**:
   - Implemented **Singleton Service Pattern** to maintain state.
   - Used **Negative PID Kill Signal** (`process.kill(-pid)`) to terminate entire process groups.
3. **State Re-sync (Persistence)**:
   - Added `isTrainingRunning`, `isTaggingRunning`, and `isDataGenBusy` IPC handlers.
   - UI components now query status on mount to recover active state after refresh.
4. **Professional Terminal Display**:
   - Built a custom log processor to handle ANSI escape codes and Carriage Returns.
   - Implemented in-place line updates for `tqdm` progress bars.
   - Added auto-scrolling and VS Code-inspired terminal styling.

**Services Impacted**:
- `TrainService`
- `TagService`
- `DataGenService`
- `OllamaProvider` (Singleton refactor)

---

## UX & Reliability: LoRA Workflow Polishing
**Date**: January 19, 2026

### Problem
The LoRA workflow had several friction points:
1. **Selection Rigidness**: Users couldn't easily search through long lists of pre-configured LoRAs.
2. **Fixed Directories**: The output directory was partially hardcoded, making it difficult to manage different datasets.
3. **WSL Friction**: "Open in Explorer" buttons failed because WSL Ubuntu lacks the `xdg-open` utility used by Electron.
4. **Logic Bugs**: Manually selected folders were being corrupted by auto-appended suffixes.

### Improvements
1. **Searchable LoRA Selector (Combobox)**:
   - Implemented a "match-as-you-type" filter for LoRA models.
   - Built a custom React dropdown that matches VS Code's search aesthetic.
   - Retained the ability to manually type custom paths or versions.
2. **Flexible Path Management**:
   - Added a **"Browse"** button to the DataGen UI for manual root directory selection.
   - Implemented "Explicit Choice" logic: if a user picks a folder via Browse, the system uses it *exactly* as is, disabling the auto-topic-append behavior.
3. **WSL OS Bridge (Explorer Fallback)**:
   - Refactored `system:openPath` to detect WSL environments (`/proc/version` check).
   - Implemented a fallback to `powershell.exe -c start` to bridge the WSL-Windows directory gap.
4. **Clean, Icon-Driven UI**:
   - Consolidated Output Path actions (View, Copy, Browse) into a single, professional horizontal row.
   - Replaced text buttons with standardized Lucide icons for better space efficiency.

**Services Impacted**:
- `Main / ipcMain` (openPath logic)
- `Renderer / DataGen` (Layout and logic refactor)
- `DataGen.less` (Searchable dropdown styles)

---

## Architecture Consistency (Updated)

All major features now follow a unified API-first or Singleton Service pattern:

```
Electron Desktop App (Node.js)
│
├── Data Fetch
│   └── BinanceClient → HTTPS API (api.binance.com)
│
├── Quant Analyst / Strategy
│   └── OllamaProvider (Singleton) → HTTP API (localhost:11434)
│
└── LoRA Workflow (Train / Tag / DataGen)
    └── Singleton Services → Local Python / APIs
```

**Benefits**:
- **Cross-platform**: No dependency on global binaries besides Python.
- **Persistence**: UI can safely refresh while background tasks continue.
- **Observability**: Precise progress tracking and clean log output.
- **Control**: Reliable cancellation and resource cleanup.
