
export interface LLMConfig {
    provider: string;
    model: string;
    baseUrl?: string;
    apiKey?: string;
    format?: 'json';
}

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    images?: string[]; // Base64 encoded images
}

export interface LLMProvider {
    chat(messages: ChatMessage[], config: LLMConfig): Promise<string>;
    listModels(baseUrl?: string): Promise<string[]>;
}

export interface ForgeConfig {
    baseUrl: string;
    model: string;
}

export interface Txt2ImgRequest {
    prompt: string;
    negativePrompt?: string;
    steps?: number;
    width?: number;
    height?: number;
    cfgScale?: number;
    samplerName?: string;
    overrideSettings?: Record<string, any>;
}

export interface DataGenOptions {
    total: number;
    topic: string;
    outputDir: string;
    lora?: string;
    loraWeight?: number;
    trigger?: string;
    noCaption?: boolean;
    manualPrompt?: string;
    useTimestamp?: boolean;
}

export interface DataGenProgress {
    current: number;
    total: number;
    status: string;
    imagePath?: string;
    captionPath?: string;
}

export interface Candle {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export interface TimeframeData {
    timeframe: string;
    candles: Candle[];
    filename: string;
}

export interface QuantAnalystOptions {
    inputs: string[];
    logic: string;
    limit: number;
    useAnalyst: boolean;
    distill: boolean;
    promptOnly: boolean;
    outputFile: string;
    analystModel?: string;
}

export interface FetchDataOptions {
    symbol: string;
    timeframes: string[];  // e.g., ['1h', '4h', '1d']
    startDate: string;     // ISO 8601 format (YYYY-MM-DD)
    endDate?: string;      // Optional
    outputDir: string;
    limit?: number;
}

export interface FetchProgress {
    current: number;
    total: number;
    timeframe: string;
    status: string;  // 'fetching', 'writing', 'complete'
}

export interface FetchResult {
    success: boolean;
    filesCreated: string[];
    totalRecords: number;
    error?: string;
}

export interface TagOptions {
    path: string;
    model: string;
    threshold: number;
    generalThreshold: number;
    characterThreshold: number;
    batchSize: number;
    undesired?: string;
    recursive: boolean;
    debug: boolean;
    frequency: boolean;
    maxWorkers: number;
}

export interface TagProgress {
    status: string;
    type: 'stdout' | 'stderr';
}

export interface TagResult {
    success: boolean;
    error?: string;
}
export interface RankOptions {
    dir: string;
    model: string;
    outputFile?: string;
    format: 'md' | 'html';
    prompt?: string;
}

export interface RankResult {
    filename: string;
    score: number;
    reason: string;
    imagePath: string;
}

export interface RankProgress {
    current: number;
    total: number;
    status: string;
    currentImage?: string;
}
