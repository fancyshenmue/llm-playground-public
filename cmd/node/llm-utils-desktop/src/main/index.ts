import { app, shell, BrowserWindow, ipcMain, dialog, globalShortcut } from 'electron'
import { join } from 'path'
import { readFile } from 'fs/promises'

// Disable hardware acceleration to avoid GPU errors in WSL
app.disableHardwareAcceleration()

// Module-level reference for IPC handlers
let mainWindow: BrowserWindow | null = null

const createWindow = (): void => {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    center: true,
    show: true,
    backgroundColor: '#181818',
    frame: false, // Frameless window for custom title bar
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true
    }
  })

  // IPC handlers for window controls
  ipcMain.on('window-minimize', () => {
    mainWindow?.minimize()
  })

  ipcMain.on('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow?.maximize()
    }
  })

  ipcMain.on('window-close', () => {
    mainWindow?.close()
  })

  // IPC handlers for zoom
  ipcMain.on('window-zoom-in', () => {
    const zoom = mainWindow?.webContents.getZoomLevel() || 0
    mainWindow?.webContents.setZoomLevel(zoom + 0.5)
  })

  ipcMain.on('window-zoom-out', () => {
    const zoom = mainWindow?.webContents.getZoomLevel() || 0
    mainWindow?.webContents.setZoomLevel(zoom - 0.5)
  })

  ipcMain.on('window-zoom-reset', () => {
    mainWindow?.webContents.setZoomLevel(0)
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
    mainWindow?.focus()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  const isDev = !app.isPackaged
  if (isDev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  // IPC handlers for Configuration
  ipcMain.handle('config:get', async () => {
    try {
      const { ConfigLoader } = await import('@internal/services/config-loader')
      return await ConfigLoader.load()
    } catch (error) {
      console.error('Config Get Error:', error)
      throw error
    }
  })

  // IPC handlers for LLM
  ipcMain.handle('llm:chat', async (_event, messages, config) => {
    try {
      const { OllamaProvider } = await import('@internal/services/ollama')
      const provider = new OllamaProvider()
      return await provider.chat(messages, config)
    } catch (error) {
      console.error('LLM Chat Error:', error)
      throw error
    }
  })

  ipcMain.handle('llm:models', async (_event, providerName, baseUrl) => {
    try {
      if (providerName === 'ollama') {
        const { OllamaProvider } = await import('@internal/services/ollama')
        const provider = new OllamaProvider()
        return await provider.listModels(baseUrl)
      }
      return []
    } catch (error) {
      console.error('LLM Models Error:', error)
      throw error
    }
  })

  // DataGen IPC Handler
  ipcMain.handle('datagen:start', async (event, options, llmConfig, forgeConfig) => {
    try {
      const { DataGenService } = await import('@internal/services/datagen-service')
      const { OllamaProvider } = await import('@internal/services/ollama')
      const service = DataGenService.getInstance()
      const provider = new OllamaProvider()

      await service.generate(provider, llmConfig, forgeConfig, options, (progress) => {
        event.sender.send('datagen:progress', progress)
      })
      return { success: true }
    } catch (error) {
      console.error('DataGen Error:', error)
      throw error
    }
  })

  // Quant IPC Handler
  ipcMain.handle('quant:generate', async (_event, options, llmConfig) => {
    try {
      const { QuantService } = await import('@internal/services/quant-service')
      const { OllamaProvider } = await import('@internal/services/ollama')
      const service = new QuantService()
      const provider = new OllamaProvider()
      const response = await service.generateStrategy(provider, llmConfig, options)
      return response
    } catch (error) {
      console.error('Quant Generation Error:', error)
      throw error
    }
  })

  // Quant Analyst IPC Handler
  ipcMain.handle('quant:analyst', async (_event, options, llmConfig) => {
    try {
      const { QuantService } = await import('@internal/services/quant-service')
      const { OllamaProvider } = await import('@internal/services/ollama')
      const service = new QuantService()
      const provider = new OllamaProvider()
      return await service.runAnalystWorkflow(provider, llmConfig, options)
    } catch (error) {
      console.error('Quant Analyst Error:', error)
      throw error
    }
  })

  // System File Selection IPC Handler
  ipcMain.handle('system:selectFiles', async (_event, options) => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile', 'multiSelections'],
      filters: [{ name: 'CSV Files', extensions: ['csv'] }],
      ...options
    })
    return result.filePaths
  })

  ipcMain.handle('system:listItems', async (_event, dirPath, showFiles = false) => {
    try {
      const { readdir, stat, mkdir } = await import('fs/promises')
      const { join } = await import('path')

      // Auto-create directory if it doesn't exist
      await mkdir(dirPath, { recursive: true })

      const entries = await readdir(dirPath)
      const items: { name: string; isDirectory: boolean }[] = []
      for (const entry of entries) {
        if (entry.startsWith('.')) continue
        const fullPath = join(dirPath, entry)
        const s = await stat(fullPath)
        if (s.isDirectory()) {
          items.push({ name: entry, isDirectory: true })
        } else if (showFiles) {
          items.push({ name: entry, isDirectory: false })
        }
      }
      return items.sort((a, b) => {
        if (a.isDirectory !== b.isDirectory) return a.isDirectory ? -1 : 1
        return a.name.localeCompare(b.name)
      })
    } catch (error) {
      console.error('List Items Error:', error)
      return []
    }
  })
  ipcMain.handle('system:openPath', async (_event, path: string) => {
    try {
      const { exec } = await import('child_process')
      const { promisify } = await import('util')
      const execAsync = promisify(exec)

      // Try Electron's native openPath first
      const error = await shell.openPath(path)
      if (!error) return { success: true }

      // If native failed, especially in WSL, try explorer.exe
      // Check if we are in WSL
      const isWsl = await readFile('/proc/version', 'utf8').then(v => v.toLowerCase().includes('microsoft')).catch(() => false)

      if (isWsl) {
        // Convert Linux path to Windows path for explorer.exe (though it often works if passed as-is to powershell)
        // A safer way in WSL is using powershell.exe -c start
        await execAsync(`powershell.exe -c start "${path}"`)
        return { success: true }
      }

      return { success: false, error }
    } catch (error) {
      console.error('Open Path Error:', error)
      return { success: false, error: String(error) }
    }
  })

  // Data Fetch IPC Handler
  ipcMain.handle('data:fetch', async (event, options) => {
    try {
      const { QuantService } = await import('@internal/services/quant-service')
      const service = new QuantService()

      return await service.fetchTradingData(options, (progress) => {
        event.sender.send('data:fetchProgress', progress)
      })
    } catch (error) {
      console.error('Data Fetch Error:', error)
      throw error
    }
  })

  // Tag IPC Handler
  ipcMain.handle('tag:start', async (event, options) => {
    try {
      const { TagService } = await import('@internal/services/tag-service')
      const service = TagService.getInstance()

      return await service.tagImages(options, (progress) => {
        event.sender.send('tag:progress', progress)
      })
    } catch (error) {
      console.error('Tag Error:', error)
      throw error
    }
  })

  // DataGen Cancel Handler
  ipcMain.handle('datagen:cancel', async () => {
    try {
      const { DataGenService } = await import('@internal/services/datagen-service')
      const service = DataGenService.getInstance()
      service.cancel()
      return { success: true }
    } catch (error) {
      console.error('DataGen Cancel Error:', error)
      return { success: false }
    }
  })

  ipcMain.handle('datagen:isBusy', async () => {
    const { DataGenService } = await import('@internal/services/datagen-service')
    return DataGenService.getInstance().isBusy()
  })

  // Tag Cancel Handler
  ipcMain.handle('tag:cancel', async () => {
    try {
      const { TagService } = await import('@internal/services/tag-service')
      const service = TagService.getInstance()
      service.cancel()
      return { success: true }
    } catch (error) {
      console.error('Tag Cancel Error:', error)
      return { success: false }
    }
  })

  ipcMain.handle('tag:isRunning', async () => {
    const { TagService } = await import('@internal/services/tag-service')
    return TagService.getInstance().isRunning()
  })

  // Train handlers
  ipcMain.handle('train:start', async (_event, configPath: string) => {
    try {
      const { TrainService } = await import('@internal/services/train-service')
      const service = TrainService.getInstance()

      const result = await service.train(configPath, (progress) => {
        mainWindow?.webContents.send('train:progress', progress)
      })

      return result
    } catch (error) {
      console.error('Train Error:', error)
      return { success: false, error: String(error) }
    }
  })

  ipcMain.handle('train:cancel', async () => {
    try {
      const { TrainService } = await import('@internal/services/train-service')
      const service = TrainService.getInstance()
      service.cancel()
      return { success: true }
    } catch (error) {
      console.error('Train Cancel Error:', error)
      return { success: false }
    }
  })

  ipcMain.handle('train:isRunning', async () => {
    const { TrainService } = await import('@internal/services/train-service')
    return TrainService.getInstance().isRunning()
  })

  // Rank IPC Handlers
  ipcMain.handle('rank:start', async (event, options, llmConfig) => {
    try {
      const { RankService } = await import('@internal/services/rank-service')
      const service = RankService.getInstance()

      return await service.rank(options, llmConfig, (progress) => {
        event.sender.send('rank:progress', progress)
      })
    } catch (error) {
      console.error('Rank Error:', error)
      throw error
    }
  })

  ipcMain.handle('rank:cancel', async () => {
    try {
      const { RankService } = await import('@internal/services/rank-service')
      const service = RankService.getInstance()
      service.cancel()
      return { success: true }
    } catch (error) {
      console.error('Rank Cancel Error:', error)
      return { success: false }
    }
  })

  ipcMain.handle('rank:isRunning', async () => {
    const { RankService } = await import('@internal/services/rank-service')
    return RankService.getInstance().isRunning()
  })

  // Dataset Promotion
  ipcMain.handle('dataset:promote', async (_event, sourcePath: string, topicName: string, repeats: number) => {
    try {
      const { DatasetService } = await import('@internal/services/dataset-service')
      return await DatasetService.getInstance().promote(sourcePath, topicName, repeats)
    } catch (error) {
      console.error('Dataset Promotion IPC Error:', error)
      return { success: false, error: String(error) }
    }
  })

  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })

  // Register shortcuts for zoom when window is focused
  app.on('browser-window-focus', () => {
    globalShortcut.register('CommandOrControl+Plus', () => {
      const zoom = mainWindow?.webContents.getZoomLevel() || 0
      mainWindow?.webContents.setZoomLevel(zoom + 0.5)
    })
    globalShortcut.register('CommandOrControl+=', () => {
      const zoom = mainWindow?.webContents.getZoomLevel() || 0
      mainWindow?.webContents.setZoomLevel(zoom + 0.5)
    })
    globalShortcut.register('CommandOrControl+-', () => {
      const zoom = mainWindow?.webContents.getZoomLevel() || 0
      mainWindow?.webContents.setZoomLevel(zoom - 0.5)
    })
    globalShortcut.register('CommandOrControl+0', () => {
      mainWindow?.webContents.setZoomLevel(0)
    })
  })

  app.on('browser-window-blur', () => {
    globalShortcut.unregisterAll()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
