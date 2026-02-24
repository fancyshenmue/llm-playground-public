// Binance API client for fetching OHLCV data
// Public endpoints, no authentication required

export interface Kline {
    openTime: number
    open: string
    high: string
    low: string
    close: string
    volume: string
    closeTime: number
    quoteAssetVolume: string
    numberOfTrades: number
    takerBuyBaseAssetVolume: string
    takerBuyQuoteAssetVolume: string
}

export class BinanceClient {
    private baseUrl = 'https://api.binance.com'

    /**
     * Fetch klines (candlestick data) from Binance
     * @param symbol Trading pair (e.g., BTCUSDT)
     * @param interval Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
     * @param limit Number of candles to fetch (max 1000)
     * @param startTime Start timestamp in milliseconds
     * @param endTime End timestamp in milliseconds (optional)
     */
    async fetchKlines(
        symbol: string,
        interval: string,
        limit: number = 1000,
        startTime?: number,
        endTime?: number
    ): Promise<Kline[]> {
        const params = new URLSearchParams({
            symbol,
            interval,
            limit: Math.min(limit, 1000).toString()
        })

        if (startTime) params.append('startTime', startTime.toString())
        if (endTime) params.append('endTime', endTime.toString())

        const url = `${this.baseUrl}/api/v3/klines?${params}`

        try {
            const response = await fetch(url)
            if (!response.ok) {
                const error = await response.json().catch(() => ({ msg: response.statusText }))
                throw new Error(`Binance API error: ${error.msg || response.statusText}`)
            }

            const data = await response.json()

            // Map raw array response to Kline objects
            return data.map((k: any[]) => ({
                openTime: k[0],
                open: k[1],
                high: k[2],
                low: k[3],
                close: k[4],
                volume: k[5],
                closeTime: k[6],
                quoteAssetVolume: k[7],
                numberOfTrades: k[8],
                takerBuyBaseAssetVolume: k[9],
                takerBuyQuoteAssetVolume: k[10]
            }))
        } catch (error: any) {
            throw new Error(`Failed to fetch klines: ${error.message}`)
        }
    }

    /**
     * Fetch all klines from a start date, automatically paginating
     * @param symbol Trading pair
     * @param interval Timeframe
     * @param startTime Start timestamp in milliseconds
     * @param endTime End timestamp in milliseconds (optional, defaults to now)
     * @param onProgress Progress callback
     */
    async fetchAllKlines(
        symbol: string,
        interval: string,
        startTime: number,
        endTime?: number,
        onProgress?: (current: number, total: number) => void
    ): Promise<Kline[]> {
        const allKlines: Kline[] = []
        let currentStart = startTime
        const batchSize = 1000
        const finalEndTime = endTime || Date.now()

        // Estimate total batches for progress tracking
        const intervalMs = this.getIntervalMilliseconds(interval)
        const estimatedTotal = Math.ceil((finalEndTime - startTime) / (intervalMs * batchSize))

        let batchCount = 0

        while (currentStart < finalEndTime) {
            const klines = await this.fetchKlines(
                symbol,
                interval,
                batchSize,
                currentStart,
                finalEndTime
            )

            if (klines.length === 0) break

            allKlines.push(...klines)
            batchCount++

            if (onProgress) {
                onProgress(batchCount, Math.max(batchCount, estimatedTotal))
            }

            // If we got less than batch size, we've reached the end
            if (klines.length < batchSize) break

            // Set next start time to the last candle's close time + 1ms
            const lastKline = klines[klines.length - 1]
            currentStart = lastKline.closeTime + 1
        }

        return allKlines
    }

    /**
     * Convert timeframe string to milliseconds
     */
    getIntervalMilliseconds(interval: string): number {
        const mapping: Record<string, number> = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000,
            '1M': 30 * 24 * 60 * 60 * 1000, // Approximate
            '1y': 365 * 24 * 60 * 60 * 1000 // Approximate
        }
        return mapping[interval] || mapping['1d']
    }

    /**
     * Validate and normalize timeframe
     */
    normalizeInterval(tf: string): string {
        const mapping: Record<string, string> = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w',
            '1M': '1M',
            '1y': '1M' // Binance doesn't have 1y, use 1M
        }
        return mapping[tf] || '1d'
    }
}
