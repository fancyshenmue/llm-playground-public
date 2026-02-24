import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      chat: (messages: any[], config: any) => Promise<string>
      listModels: (provider: string, baseUrl?: string) => Promise<string[]>
      minimize: () => void
      maximize: () => void
      close: () => void
      zoomIn: () => void
      zoomOut: () => void
      zoomReset: () => void
      startDataGen: (options: any, llmConfig: any, forgeConfig: any) => Promise<{ success: boolean }>
      onDataGenProgress: (callback: (progress: any) => void) => () => void
      generateQuantStrategy: (options: any, llmConfig: any) => Promise<{ code: string; filePath?: string }>
      runQuantAnalyst: (options: any, llmConfig: any) => Promise<{ prompt: string; analysis?: string; filePath?: string }>
      selectFiles: (options?: any) => Promise<string[]>
      listItems: (path: string, showFiles?: boolean) => Promise<{ name: string; isDirectory: boolean }[]>
      fetchTradingData: (options: any) => Promise<{ success: boolean; filesCreated: string[]; totalRecords: number; error?: string }>
      onFetchProgress: (callback: (progress: any) => void) => () => void
      startTagging: (options: any) => Promise<{ success: boolean; error?: string }>
      onTagProgress: (callback: (progress: any) => void) => () => void
      cancelDataGen: () => Promise<{ success: boolean }>
      cancelTagging: () => Promise<{ success: boolean }>
      startTraining: (configPath: string) => Promise<{ success: boolean, error?: string }>
      onTrainProgress: (callback: (progress: any) => void) => () => void
      cancelTraining: () => Promise<{ success: boolean }>
      isTrainingRunning: () => Promise<boolean>
      isTaggingRunning: () => Promise<boolean>
      isDataGenBusy: () => Promise<boolean>
      promoteDataset: (sourcePath: string, topicName: string, repeats: number) => Promise<{ success: boolean; error?: string; destPath?: string }>
      startRank: (options: any, llmConfig: any) => Promise<{ success: boolean; results: any[]; error?: string }>
      onRankProgress: (callback: (progress: any) => void) => () => void
      cancelRank: () => Promise<{ success: boolean }>
      isRankRunning: () => Promise<boolean>
      openPath: (path: string) => Promise<{ success: boolean; error?: string }>
      getConfig: () => Promise<any>
    }
  }
}
