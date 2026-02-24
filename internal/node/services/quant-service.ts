
import { LLMProvider, ChatMessage as LLMMessage, LLMConfig, Candle, TimeframeData, QuantAnalystOptions, FetchDataOptions, FetchProgress, FetchResult } from '../types';
import * as fs from 'fs/promises';
import * as path from 'path';

export interface QuantOptions {
    strategyName: string;
    description: string;
    indicators: string[];
    riskManagement: string;
    outputFile?: string;
}

export class QuantService {
    async generateStrategy(
        provider: LLMProvider,
        llmConfig: LLMConfig,
        options: QuantOptions
    ): Promise<{ code: string; filePath?: string }> {
        const prompt = this.buildPrompt(options);

        const messages: LLMMessage[] = [
            {
                role: 'system',
                content: `You are an expert Pine Script v6 developer.
Your goal is to generate high-quality, functional TradingView strategies.
Always use Pine Script v6 syntax.
Follow best practices: proper variable naming, clear comments, and robust risk management.`
            },
            {
                role: 'user',
                content: prompt
            }
        ];

        const response = await provider.chat(messages, llmConfig);
        const code = this.extractCode(response);

        let filePath: string | undefined;
        if (options.outputFile) {
            // Respect project root for generation as well
            const projectRoot = path.resolve(__dirname, '../../../../../');
            filePath = path.resolve(projectRoot, options.outputFile);
            await fs.mkdir(path.dirname(filePath), { recursive: true });
            await fs.writeFile(filePath, code, 'utf-8');
        }

        return { code, filePath };
    }

    async runAnalystWorkflow(
        provider: LLMProvider,
        llmConfig: LLMConfig,
        options: QuantAnalystOptions
    ): Promise<{ prompt: string; analysis?: string; filePath?: string }> {
        // Calculate project root
        // out/main -> out -> llm-utils-desktop -> node -> cmd -> llm-playground
        const projectRoot = path.resolve(__dirname, '../../../../../');

        console.log('QuantAnalyst Options Received:', {
            inputs: options.inputs.length,
            logic: options.logic,
            promptOnly: options.promptOnly,
            outputFile: options.outputFile,
            distill: options.distill,
            useAnalyst: options.useAnalyst,
            projectRoot
        });

        // 1. Parse all input files
        const allData: TimeframeData[] = [];

        // First pass: detect all timeframes
        const timeframes: string[] = [];
        for (const inputPath of options.inputs) {
            const tf = this.detectTimeframe(inputPath);
            timeframes.push(tf);
        }

        // Find the largest timeframe (highest minutes value)
        let largestTf = timeframes[0];
        let largestMinutes = this.getTimeframeMinutes(largestTf);
        for (const tf of timeframes) {
            const minutes = this.getTimeframeMinutes(tf);
            if (minutes > largestMinutes) {
                largestMinutes = minutes;
                largestTf = tf;
            }
        }

        console.log(`Detected timeframes: ${timeframes.join(', ')}`);
        console.log(`Largest timeframe: ${largestTf} (base limit: ${options.limit})`);

        // Second pass: parse with adjusted limits
        for (let i = 0; i < options.inputs.length; i++) {
            const inputPath = options.inputs[i];
            const tf = timeframes[i];

            // Calculate the appropriate limit for this timeframe
            const adjustedLimit = this.calculateCandleLimit(tf, largestTf, options.limit);

            console.log(`  ${tf}: ${adjustedLimit} candles (${adjustedLimit === options.limit ? 'base' : `${(adjustedLimit / options.limit).toFixed(1)}x base`})`);

            // Allow both absolute and relative paths (relative to projectRoot)
            const absolutePath = path.isAbsolute(inputPath) ? inputPath : path.resolve(projectRoot, inputPath);
            const candles = await this.parseTradingViewCSV(absolutePath, adjustedLimit);
            allData.push({
                timeframe: tf,
                candles,
                filename: path.basename(inputPath)
            });
        }


        // 2. Format market data
        let marketDataStr = '';
        if (allData.length === 1) {
            marketDataStr = this.formatCandlesForLLM(allData[0].candles);
        } else {
            marketDataStr = this.formatMultiTimeframeData(allData);
        }

        // 3. Optional: Analyst Stage
        let analystInsight = '';
        if (options.useAnalyst) {
            const analystConfig = {
                ...llmConfig,
                model: options.analystModel || llmConfig.model
            };
            analystInsight = await this.analyzeMarketData(provider, analystConfig, allData, options.logic);
        }

        // 4. Construct the prompt (mirroring Go logic)
        const biblePath = path.resolve(projectRoot, 'documents/quant/pine_v6_reference.md');
        const templatePath = path.resolve(projectRoot, 'documents/quant/golden_templates.md');

        let localContext = '';
        try {
            const bible = await fs.readFile(biblePath, 'utf-8');
            localContext += `\n### PINE SCRIPT V6 BIBLE (GROUND TRUTH):\n${bible}\n`;
        } catch (e) {
            console.warn(`Could not read bible at ${biblePath}`);
        }

        try {
            const templates = await fs.readFile(templatePath, 'utf-8');
            localContext += `\n### GOLDEN TEMPLATES (EXAMPLES):\n${templates}\n`;
        } catch (e) {
            console.warn(`Could not read templates at ${templatePath}`);
        }

        const marketPromptData = (options.distill && analystInsight) ? "(Raw data distilled into Analyst Report below)" : marketDataStr;

        const constructedPrompt = `### DATA SAMPLE (MANDATORY):
${marketPromptData}

### ANALYST REPORT:
${analystInsight}

### DOCUMENTATION CONTEXT:
${localContext}

### MANDATORY RULES (PHASE 6 HARDENING):
You are a God-tier Pine Script v6 expert. You MUST follow these structural rules:

1. BOILERPLATE: Always start with '//@version=6' and a 'strategy()' header.
2. PRE-CALCULATION (CRITICAL): ALL functions in the 'ta.' and 'math.' namespaces MUST be calculated as variables at the top of the script (Level 0).
   - NEVER call ta.* inside 'if', 'for', or complex logical expressions.
3. NAMESPACES: Mandatory 'ta.', 'request.', 'math.', 'strategy.', 'input.'.
4. REGIME-BASED DECISION TREE (GATING):
   - **MANDATORY**: Implement logic branching based on the Analyst's 'market_regime'.
   - **IF TRENDING**: Assign high weight (70%) to the Analyst's Meta-Score and low weight (30%) to technical indicators. Focus on trend-following entries.
   - **IF RANGING**: Assign low weight (30%) to the Analyst's Meta-Score and high weight (70%) to technical oscillators (RSI/Stoch). Require stricter confirmation for entries.
5. FEATURE ENGINEERING (ADVANCED):
   - Calculate 'market_structure' (ADX), 'momentum_bias' (Bias from 1D MA), and 'volatility_expansion' (BBWidth) as Level 0 variables.
   - Use these features to gate or scale your entry signals.
6. RISK MANAGEMENT (REGIME-ADAPTIVE):
   - Use wider stops in TRENDING regimes and tighter, faster trailing stops in RANGING regimes.
7. REASONING:
   - Include brief comments explaining how the Decision Tree is switching the strategy behavior.

USER LOGIC TO IMPLEMENT: ${options.logic || 'N/A (Provide general analysis and strategy suggestions)'}.
Output ONLY raw code starting with '//@version=6'. No markdown fences.`;

        let resultFilePath: string | undefined;
        if (options.outputFile) {
            console.log('Attempting to write constructed prompt to:', options.outputFile);
            let targetPath = path.resolve(projectRoot, options.outputFile);
            if (!targetPath.endsWith('.txt')) {
                targetPath = targetPath.replace(/\.[^.]+$/, '') + '.txt';
            }
            try {
                await fs.mkdir(path.dirname(targetPath), { recursive: true });
                await fs.writeFile(targetPath, constructedPrompt, 'utf-8');
                console.log('Successfully wrote prompt to:', targetPath);
                resultFilePath = targetPath;
            } catch (err: any) {
                console.error('Failed to write prompt file:', err.message);
            }
        }

        return {
            prompt: constructedPrompt,
            analysis: analystInsight,
            filePath: resultFilePath
        };
    }

    private async parseTradingViewCSV(filePath: string, limit: number): Promise<Candle[]> {
        const content = await fs.readFile(filePath, 'utf-8');
        const lines = content.split('\n');
        if (lines.length < 2) return [];

        const start = Math.max(1, lines.length - limit);
        const candles: Candle[] = [];

        for (let i = start; i < lines.length; i++) {
            const cols = lines[i].split(',');
            if (cols.length < 5) continue;

            candles.push({
                time: cols[0],
                open: parseFloat(cols[1]),
                high: parseFloat(cols[2]),
                low: parseFloat(cols[3]),
                close: parseFloat(cols[4]),
                volume: cols.length > 5 ? parseFloat(cols[5]) : 0
            });
        }
        return candles;
    }

    private detectTimeframe(filename: string): string {
        const lower = filename.toLowerCase();
        if (lower.includes('_1m')) return '1M';
        if (lower.includes('_5m')) return '5M';
        if (lower.includes('_15m')) return '15M';
        if (lower.includes('_30m')) return '30M';
        if (lower.includes('_1h')) return '1H';
        if (lower.includes('_4h')) return '4H';
        if (lower.includes('_1d')) return '1D';
        if (lower.includes('_1w')) return '1W';
        return 'Unknown';
    }

    // Convert timeframe string to minutes for comparison
    private getTimeframeMinutes(timeframe: string): number {
        const tfMap: { [key: string]: number } = {
            '1M': 1,
            '5M': 5,
            '15M': 15,
            '30M': 30,
            '1H': 60,
            '2H': 120,
            '4H': 240,
            '6H': 360,
            '12H': 720,
            '1D': 1440,
            '1W': 10080
        };
        return tfMap[timeframe] || 60; // default to 1h
    }

    // Calculate candle limit based on the largest timeframe
    // This ensures all timeframes cover the same time period
    private calculateCandleLimit(currentTf: string, largestTf: string, baseLimit: number): number {
        const currentMinutes = this.getTimeframeMinutes(currentTf);
        const largestMinutes = this.getTimeframeMinutes(largestTf);

        // If current timeframe is smaller, we need more candles to cover the same period
        // e.g., if largest is 1D (1440m) and current is 1H (60m), ratio = 1440/60 = 24
        const ratio = largestMinutes / currentMinutes;
        return Math.ceil(baseLimit * ratio);
    }


    private formatCandlesForLLM(candles: Candle[]): string {
        let res = "Market Data (Last Candles):\n";
        for (const c of candles) {
            res += `Time: ${c.time}, O: ${c.open.toFixed(2)}, H: ${c.high.toFixed(2)}, L: ${c.low.toFixed(2)}, C: ${c.close.toFixed(2)}\n`;
        }
        return res;
    }

    private formatMultiTimeframeData(allData: TimeframeData[]): string {
        let res = '';
        for (const data of allData) {
            res += `\n=== TIMEFRAME: ${data.timeframe} (${data.filename}) ===\n`;
            res += this.formatCandlesForLLM(data.candles);
        }
        res += "\n📊 MULTI-TIMEFRAME STRATEGY REQUIREMENTS:\n";
        res += "1. Use request.security() to fetch higher timeframe data\n";
        res += "2. Example MTF pattern:\n";
        res += "   dailyTrend = request.security(syminfo.tickerid, \"D\", ta.sma(close, 50))\n";
        return res;
    }
    private async analyzeMarketData(
        provider: LLMProvider,
        config: LLMConfig,
        allData: TimeframeData[],
        logic?: string
    ): Promise<string> {
        let dataDesc = '';
        for (const data of allData) {
            dataDesc += `\n=== ${data.timeframe} ===\n${this.formatCandlesForLLM(data.candles)}`;
        }

        const idea = logic?.trim() || "general market trend and potential strategy opportunities";
        const prompt = `You are a professional quantitative analyst.

MARKET DATA:
${dataDesc}

USER'S STRATEGY IDEA:
${idea}

### ANALYST TASK: META-LEARNER & FEATURE TAGGING
1. **FEATURE TAGGING**: Analyze and report these technical features:
   - **Market Structure**: "TRENDING" (ADX > 25) vs "RANGING" (ADX <= 25).
   - **Momentum Bias**: Calculate the deviation of current 1H price from the 1D Moving Average.
   - **Volatility Expansion**: Report the Bollinger Bandwidth (upper-lower)/basis.
2. **META-LEARNER ANALYSIS**:
   - Act as a **Meta-Learner**. Combine multi-timeframe indicators, volume profile, and current volatility.
   - Output a **Meta-Score** (-100 to 100) where -100 is absolute bearish conviction and 100 is absolute bullish conviction.
3. **STRATEGY RECOMMENDATIONS (REGIME-ADAPTIVE)**:
   - Provide separate entry/exit rules for TRENDING vs RANGING states.
   - If TRENDING: Focus on pullback entries and trend extensions.
   - If RANGING: Focus on mean reversion and overbought/oversold boundaries.

4. Provide a structured **META-ANALYSIS SCORE** in a JSON block (REQUIRED) at the end:
   {
     "timeframes": {
       "1D": {"trend": "Bullish", "strength": 85, "confidence": 90},
       "4H": {"trend": "Neutral", "strength": 40, "confidence": 60},
       "1H": {"trend": "Bullish", "strength": 60, "confidence": 75}
     },
     "market_regime": "TRENDING",
     "volatility_regime": "High",
     "meta_score": 75,
     "features": {
        "adx": 28,
        "bias_pct": 3.5,
        "bb_bandwidth": 0.12
     }
   }

Provide a detailed technical analysis focusing on structural logic for a Decision Tree strategy.`;

        return await provider.chat([{ role: 'user', content: prompt }], config);
    }

    private buildPrompt(options: QuantOptions): string {
        return `Generate a Pine Script v6 strategy named "${options.strategyName}".

Description:
${options.description}

Required Indicators:
${options.indicators.join(', ')}

Risk Management Rules:
${options.riskManagement}

Requirements:
1. Use 'strategy()' declaration with v6.
2. Include inputs for all key parameters.
3. Implement entry and exit logic clearly.
4. Add comments explaining the logic.
5. Ensure the code is syntactically correct for Pine Script v6.

Return ONLY the Pine Script code inside a markdown code block.`
    }

    private extractCode(content: string): string {
        const codeBlockMatch = content.match(/```(?:pine|pinescript)?\s*([\s\S]*?)```/i);
        if (codeBlockMatch) {
            return codeBlockMatch[1].trim();
        }
        return content.trim();
    }

    async fetchTradingData(
        options: FetchDataOptions,
        progressCallback?: (progress: FetchProgress) => void
    ): Promise<FetchResult> {
        const projectRoot = path.resolve(__dirname, '../../../../../');
        const { BinanceClient } = await import('./binance-client');
        const client = new BinanceClient();

        const filesCreated: string[] = [];
        let totalRecords = 0;

        try {
            // Parse dates to timestamps
            const startTime = new Date(options.startDate).getTime();
            const endTime = options.endDate ? new Date(options.endDate).getTime() : undefined;

            // Process each timeframe
            for (let i = 0; i < options.timeframes.length; i++) {
                const tf = options.timeframes[i].trim();
                const interval = client.normalizeInterval(tf);

                // Emit progress: fetching
                if (progressCallback) {
                    progressCallback({
                        current: i + 1,
                        total: options.timeframes.length,
                        timeframe: tf,
                        status: 'fetching'
                    });
                }

                console.log(`Fetching ${options.symbol} ${tf} data...`);

                // Fetch klines based on options
                let klines;

                if (options.limit && options.limit > 1000) {
                    // Need pagination for large limits
                    const allKlines = await client.fetchAllKlines(
                        options.symbol,
                        interval,
                        startTime || Date.now() - (options.limit * client['getIntervalMilliseconds'](interval)),
                        endTime
                    );
                    // Trim to requested limit
                    klines = allKlines.slice(-options.limit);
                } else if (startTime && !options.limit) {
                    // Use date range (pagination, no limit)
                    klines = await client.fetchAllKlines(options.symbol, interval, startTime, endTime);
                } else if (options.limit) {
                    // Small limit (≤ 1000), single request
                    klines = await client.fetchKlines(options.symbol, interval, options.limit, startTime, endTime);
                } else {
                    // Default: fetch last 1000 candles
                    klines = await client.fetchKlines(options.symbol, interval, 1000);
                }

                // Save to CSV
                const symbolLower = options.symbol.toLowerCase();
                const filename = `${symbolLower}_${tf}.csv`;
                const outputDir = path.resolve(projectRoot, options.outputDir);
                await fs.mkdir(outputDir, { recursive: true });

                const filepath = path.join(outputDir, filename);

                // Write CSV
                await this.saveKlinesToCSV(klines, filepath);

                filesCreated.push(filepath);
                totalRecords += klines.length;

                console.log(`✅ Saved ${klines.length} candles to: ${filepath}`);

                // Emit progress: complete for this timeframe
                if (progressCallback) {
                    progressCallback({
                        current: i + 1,
                        total: options.timeframes.length,
                        timeframe: tf,
                        status: 'complete'
                    });
                }
            }

            return {
                success: true,
                filesCreated,
                totalRecords
            };
        } catch (error: any) {
            console.error('Fetch error:', error);
            return {
                success: false,
                filesCreated,
                totalRecords,
                error: error.message
            };
        }
    }

    /**
     * Save klines to CSV format (matching TradingView export format)
     */
    private async saveKlinesToCSV(klines: any[], filepath: string): Promise<void> {
        const lines: string[] = [];

        // Header
        lines.push('time,open,high,low,close,volume');

        // Data rows
        for (const k of klines) {
            const timestamp = new Date(k.openTime).toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, '');
            lines.push(`${timestamp},${k.open},${k.high},${k.low},${k.close},${k.volume}`);
        }

        await fs.writeFile(filepath, lines.join('\n'), 'utf-8');
    }
}
