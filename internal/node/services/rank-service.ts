import fs from 'fs/promises';
import path from 'path';
import { LLMConfig, RankOptions, RankResult, RankProgress } from '../types';
import { OllamaProvider } from './ollama';

export class RankService {
    private static instance: RankService;
    private isBusy: boolean = false;
    private shouldCancel: boolean = false;
    private ollama = new OllamaProvider();

    static getInstance(): RankService {
        if (!RankService.instance) {
            RankService.instance = new RankService();
        }
        return RankService.instance;
    }

    async rank(
        options: RankOptions,
        llmConfig: LLMConfig,
        onProgress: (p: RankProgress) => void
    ): Promise<{ success: boolean; results: RankResult[]; error?: string }> {
        if (this.isBusy) {
            return { success: false, results: [], error: 'Service is busy' };
        }

        this.isBusy = true;
        this.shouldCancel = false;
        const results: RankResult[] = [];

        try {
            const files = await fs.readdir(options.dir);
            const imageFiles = files.filter(f =>
                ['.png', '.jpg', '.jpeg', '.webp'].includes(path.extname(f).toLowerCase())
            ).map(f => path.join(options.dir, f));

            if (imageFiles.length === 0) {
                throw new Error('No images found in directory');
            }

            const total = imageFiles.length;
            for (let i = 0; i < total; i++) {
                if (this.shouldCancel) {
                    onProgress({ current: i, total, status: 'Cancelled' });
                    break;
                }

                const imgPath = imageFiles[i];
                const filename = path.basename(imgPath);
                onProgress({ current: i + 1, total, status: `Evaluating ${filename}...`, currentImage: imgPath });

                try {
                    const imgData = await fs.readFile(imgPath);
                    const base64Img = imgData.toString('base64');

                    const prompt = options.prompt || "Please rate this image from 1 to 10 based on visual appeal and style consistency. Return only the number and a short reason.";

                    const response = await this.ollama.chat([
                        {
                            role: 'user',
                            content: prompt,
                            images: [base64Img]
                        }
                    ], llmConfig);

                    // Simple parsing: extract first number found for score
                    const scoreMatch = response.match(/\b([1-9]|10)\b/);
                    const score = scoreMatch ? parseInt(scoreMatch[1]) : 0;
                    const reason = response.replace(/\b([1-9]|10)\b/, '').trim();

                    results.push({
                        filename,
                        score,
                        reason,
                        imagePath: imgPath
                    });
                } catch (err: any) {
                    console.error(`Failed to rank ${filename}:`, err);
                    results.push({
                        filename,
                        score: 0,
                        reason: `Error: ${err.message}`,
                        imagePath: imgPath
                    });
                }
            }

            // Sort results by score (descending)
            results.sort((a, b) => b.score - a.score);

            // Handle Export
            if (options.outputFile) {
                await this.exportResults(results, options.format, options.outputFile);
            }

            return { success: !this.shouldCancel, results };
        } catch (error: any) {
            return { success: false, results: [], error: error.message };
        } finally {
            this.isBusy = false;
        }
    }

    cancel() {
        this.shouldCancel = true;
    }

    isRunning() {
        return this.isBusy;
    }

    private async exportResults(results: RankResult[], format: 'md' | 'html', outputPath: string) {
        let content = '';
        if (format === 'md') {
            content = '# Image Ranking Results\n\n';
            content += '| Rank | Image | Score | Reason |\n';
            content += '| :--- | :--- | :--- | :--- |\n';
            results.forEach((r, i) => {
                content += `| ${i + 1} | ${r.filename} | **${r.score}** | ${r.reason} |\n`;
            });
        } else {
            content = `
<html>
<head>
  <style>
    body { font-family: sans-serif; background: #1e1e1e; color: #ccc; padding: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #333; padding: 12px; text-align: left; }
    th { background: #252526; }
    tr:nth-child(even) { background: #2d2d2d; }
    .score { font-weight: bold; color: #007acc; }
  </style>
</head>
<body>
  <h1>Image Ranking Results</h1>
  <table>
    <tr><th>Rank</th><th>Image</th><th>Score</th><th>Reason</th></tr>
    ${results.map((r, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>${r.filename}</td>
        <td><span class="score">${r.score}</span></td>
        <td>${r.reason}</td>
      </tr>
    `).join('')}
  </table>
</body>
</html>`;
        }

        const dir = path.dirname(outputPath);
        await fs.mkdir(dir, { recursive: true });
        await fs.writeFile(outputPath, content);
    }
}
