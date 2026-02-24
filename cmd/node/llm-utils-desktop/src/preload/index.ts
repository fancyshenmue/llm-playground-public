import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {
  chat: (messages: any[], config: any) => ipcRenderer.invoke('llm:chat', messages, config),
  listModels: (provider: any, baseUrl: any) => ipcRenderer.invoke('llm:models', provider, baseUrl),
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  zoomIn: () => ipcRenderer.send('window-zoom-in'),
  zoomOut: () => ipcRenderer.send('window-zoom-out'),
  zoomReset: () => ipcRenderer.send('window-zoom-reset'),
  startDataGen: (options: any, llmConfig: any, forgeConfig: any) =>
    ipcRenderer.invoke('datagen:start', options, llmConfig, forgeConfig),
  onDataGenProgress: (callback: (progress: any) => void) => {
    const subscription = (_event: any, progress: any) => callback(progress)
    ipcRenderer.on('datagen:progress', subscription)
    return () => ipcRenderer.removeListener('datagen:progress', subscription)
  },
  generateQuantStrategy: (options: any, llmConfig: any) => ipcRenderer.invoke('quant:generate', options, llmConfig),
  runQuantAnalyst: (options: any, llmConfig: any) => ipcRenderer.invoke('quant:analyst', options, llmConfig),
  selectFiles: (options?: any) => ipcRenderer.invoke('system:selectFiles', options),
  listItems: (path: string, showFiles?: boolean) => ipcRenderer.invoke('system:listItems', path, showFiles),
  fetchTradingData: (options: any) => ipcRenderer.invoke('data:fetch', options),
  onFetchProgress: (callback: (progress: any) => void) => {
    const subscription = (_event: any, progress: any) => callback(progress)
    ipcRenderer.on('data:fetchProgress', subscription)
    return () => ipcRenderer.removeListener('data:fetchProgress', subscription)
  },
  startTagging: (options: any) => ipcRenderer.invoke('tag:start', options),
  onTagProgress: (callback: (progress: any) => void) => {
    const subscription = (_event: any, progress: any) => callback(progress)
    ipcRenderer.on('tag:progress', subscription)
    return () => ipcRenderer.removeListener('tag:progress', subscription)
  },
  cancelDataGen: () => ipcRenderer.invoke('datagen:cancel'),
  cancelTagging: () => ipcRenderer.invoke('tag:cancel'),
  startTraining: (configPath: string) => ipcRenderer.invoke('train:start', configPath),
  onTrainProgress: (callback: (progress: any) => void) => {
    const subscription = (_event: any, progress: any) => callback(progress)
    ipcRenderer.on('train:progress', subscription)
    return () => ipcRenderer.removeListener('train:progress', subscription)
  },
  cancelTraining: () => ipcRenderer.invoke('train:cancel'),
  isTrainingRunning: () => ipcRenderer.invoke('train:isRunning'),
  isTaggingRunning: () => ipcRenderer.invoke('tag:isRunning'),
  isDataGenBusy: () => ipcRenderer.invoke('datagen:isBusy'),
  promoteDataset: (sourcePath: string, topicName: string, repeats: number) =>
    ipcRenderer.invoke('dataset:promote', sourcePath, topicName, repeats),
  startRank: (options: any, llmConfig: any) => ipcRenderer.invoke('rank:start', options, llmConfig),
  onRankProgress: (callback: (progress: any) => void) => {
    const subscription = (_event: any, progress: any) => callback(progress)
    ipcRenderer.on('rank:progress', subscription)
    return () => ipcRenderer.removeListener('rank:progress', subscription)
  },
  cancelRank: () => ipcRenderer.invoke('rank:cancel'),
  isRankRunning: () => ipcRenderer.invoke('rank:isRunning'),
  openPath: (path: string) => ipcRenderer.invoke('system:openPath', path),
  getConfig: () => ipcRenderer.invoke('config:get')
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}
