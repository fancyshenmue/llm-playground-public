import { DataGenOptions, DataGenProgress, LLMProvider, ForgeConfig, LLMConfig } from '../types';
import { ForgeService } from './forge-service';
import fs from 'fs/promises';
import path from 'path';

export class DataGenService {
    private static instance: DataGenService | null = null;
    private forgeService = new ForgeService();
    private isCancelled = false;
    private isGenerating = false;

    /**
     * Get singleton instance
     */
    static getInstance(): DataGenService {
        if (!this.instance) {
            this.instance = new DataGenService();
        }
        return this.instance;
    }

    async generate(
        llmProvider: LLMProvider,
        llmConfig: LLMConfig,
        forgeConfig: ForgeConfig,
        options: DataGenOptions,
        onProgress: (progress: DataGenProgress) => void
    ): Promise<void> {
        this.isGenerating = true;
        this.isCancelled = false;
        try {
            const { total, topic, outputDir, manualPrompt, noCaption, lora, loraWeight, trigger, useTimestamp } = options;

            // Calculate project root (same logic as QuantService)
            // out/main -> out -> llm-utils-desktop -> node -> cmd -> llm-playground
            const projectRoot = path.resolve(__dirname, '../../../../../');

            // Resolve output directory relative to project root
            const resolvedOutputDir = path.resolve(projectRoot, outputDir);

            console.log('DataGen Path Resolution:', {
                outputDir,
                projectRoot,
                resolvedOutputDir
            });

            // Ensure output directory exists
            await fs.mkdir(resolvedOutputDir, { recursive: true });

            for (let i = 0; i < total; i++) {
                // Check for cancellation
                if (this.isCancelled) {
                    onProgress({
                        current: i + 1,
                        total,
                        status: 'Cancelled by user'
                    });
                    this.isCancelled = false; // Reset for next run
                    return;
                }

                onProgress({ current: i + 1, total, status: 'Generating prompt...' });

                let prompt = '';
                let caption = '';

                try {
                    if (manualPrompt) {
                        prompt = manualPrompt;
                        caption = manualPrompt;
                    } else {
                        const result = await this.getPromptAndCaption(llmProvider, llmConfig, topic, i);
                        prompt = result.prompt;
                        caption = result.caption;
                    }

                    // Inject LoRA
                    if (lora) {
                        const finalTrigger = trigger || 'FancyStyle';
                        const weight = loraWeight || 1.0;
                        // Strip extension for the tag
                        const loraTag = lora.split('.').slice(0, -1).join('.') || lora;
                        prompt = `${finalTrigger}, <lora:${loraTag}:${weight}>, ${prompt}`;
                    }

                    const safeTopic = topic.toLowerCase().replace(/\s+/g, '_');
                    const timestamp = Date.now();
                    const filename = useTimestamp
                        ? `${timestamp}_${(i + 1).toString().padStart(3, '0')}`
                        : `${safeTopic}_${(i + 1).toString().padStart(3, '0')}`;

                    const imagePath = path.join(resolvedOutputDir, `${filename}.png`);
                    const captionPath = path.join(resolvedOutputDir, `${filename}.txt`);

                    console.log(`Generating image ${i + 1}/${total}:`, {
                        filename: `${filename}.png`,
                        prompt: prompt,
                        baseModel: forgeConfig.model
                    });

                    onProgress({ current: i + 1, total, status: `Generating image: ${filename}.png...` });

                    await this.forgeService.txt2Img(forgeConfig, {
                        prompt: prompt,
                        // Standard negative prompt from Go CLI
                        negativePrompt: "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
                    }, imagePath);

                    if (!noCaption) {
                        await fs.writeFile(captionPath, caption);
                    }

                    onProgress({
                        current: i + 1,
                        total,
                        status: 'Saved successfully',
                        imagePath,
                        captionPath: noCaption ? undefined : captionPath
                    });

                } catch (error: any) {
                    console.error(`Error in iteration ${i + 1}:`, error);
                    onProgress({
                        current: i + 1,
                        total,
                        status: `Error: ${error.message}`
                    });
                    // Continue to next one? Or stop? Go CLI continues.
                }
            }
        } catch (error: any) {
            console.error('DataGen Critical Error:', error);
            throw error;
        } finally {
            this.isGenerating = false;
        }
    }

    private async getPromptAndCaption(
        provider: LLMProvider,
        config: LLMConfig,
        topic: string,
        index: number
    ): Promise<{ prompt: string; caption: string }> {
        const systemInstruction = `You are an expert at generating diversified training data for Stable Diffusion.
The goal is to generate a unique image description for the topic: "${topic}" and its corresponding BLIP-style caption.

STRICT REQUIREMENTS:
1. Return ONLY a valid JSON object.
2. Each description MUST be unique (different settings, poses, lighting, perspectives).
3. 'prompt': A highly detailed SDXL prompt (English).
4. 'caption': A natural language BLIP-style caption describing the image content.

JSON STRUCTURE:
{"prompt": "...", "caption": "..."}`;

        const userPrompt = `Topic: ${topic}. This is iteration ${index + 1}. Ensure it's different from previous ones.`;

        const response = await provider.chat([
            { role: 'system', content: systemInstruction },
            { role: 'user', content: userPrompt }
        ], {
            ...config,
            format: 'json'
        });

        try {
            // Find JSON in response (even if JSON mode is on, sometimes LLMs wrap in markdown or prefix text)
            // match the outermost { ... }
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            let jsonStr = jsonMatch ? jsonMatch[0] : response.trim();

            try {
                return JSON.parse(jsonStr);
            } catch (pError) {
                // Try to repair truncated JSON
                console.warn('Initial JSON parse failed, attempting repair:', pError);
                const repairedJson = this.tryRepairJson(jsonStr);
                try {
                    return JSON.parse(repairedJson);
                } catch (repairError: any) {
                    console.error('Failed to parse repaired JSON:', repairedJson, repairError);
                    throw new Error(`Failed to parse LLM response as JSON even after repair: ${repairError.message}. Original response: ${response}`);
                }
            }
        } catch (error: any) {
            console.error('Failed to extract or parse JSON from response:', response, error);
            throw new Error(`Failed to extract or parse LLM response as JSON: ${error.message}. Original response: ${response}`);
        }
    }

    /**
     * Attempt to repair common JSON truncation issues
     */
    private tryRepairJson(json: string): string {
        let repaired = json.trim();

        // Count braces and quotes
        const openBraces = (repaired.match(/\{/g) || []).length;
        const closeBraces = (repaired.match(/\}/g) || []).length;
        const quotes = (repaired.match(/"/g) || []).length;

        // If odd number of quotes, close the last one
        if (quotes % 2 !== 0) {
            repaired += '"';
        }

        // Add missing closing braces
        for (let i = 0; i < openBraces - closeBraces; i++) {
            repaired += '}';
        }

        return repaired;
    }

    cancel() {
        this.isCancelled = true;
    }

    /**
     * Check if data generation is currently running
     */
    isBusy(): boolean {
        return this.isGenerating;
    }
}
