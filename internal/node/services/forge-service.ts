import { ForgeConfig, Txt2ImgRequest } from '../types';
import { ConfigLoader } from './config-loader';
import fs from 'fs/promises';

export class ForgeService {
    async txt2Img(config: ForgeConfig, request: Txt2ImgRequest, outputPath: string): Promise<void> {
        let baseUrl = config.baseUrl;
        if (!baseUrl) {
            const appConfig = await ConfigLoader.load();
            baseUrl = appConfig.forge.api_url || 'http://127.0.0.1:7861/sdapi/v1';
        }
        const url = `${baseUrl}/sdapi/v1/txt2img`;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ...request,
                // Ensure some defaults if not provided
                steps: request.steps || 30,
                width: request.width || 1024,
                height: request.height || 1024,
                cfg_scale: request.cfgScale || 7.0,
                sampler_name: request.samplerName || 'DPM++ 2M Karras',
                override_settings: {
                    ...request.overrideSettings,
                    sd_model_checkpoint: config.model,
                },
            }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Forge error: ${response.statusText} - ${errorText}`);
        }

        const data = await response.json();
        if (!data.images || data.images.length === 0) {
            throw new Error('Forge returned no images');
        }

        // Handle base64 image data
        const base64Image = data.images[0];
        const buffer = Buffer.from(base64Image, 'base64');

        await fs.writeFile(outputPath, buffer);
    }
}
