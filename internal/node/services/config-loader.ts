import * as fs from 'fs/promises';
import * as yaml from 'js-yaml';
import * as path from 'path';

export interface AppConfig {
    app: {
        name: string;
        version: string;
    };
    paths: {
        lora_project_root: string;
        datasets_raw: string;
        datasets_tagged: string;
        train_image_dir: string;
        train_configs: string;
        models_output: string;
        training_logs: string;
        training_samples: string;
    };
    kohya: {
        root_path: string;
        venv_path: string;
        scripts: {
            train: string;
            tag: string;
        };
    };
    forge: {
        api_url: string;
        base_model: string;
        available_models: string[];
    };
    ollama: {
        api_url: string;
        vision_model: string;
        providers: string[];
    };
    anythingllm?: {
        api_url: string;
        api_key: string;
        workspace_slug: string;
    };
    defaults: {
        datagen: {
            total_images: number;
            output_root: string;
        };
        tag: {
            model: string;
            general_threshold: number;
            character_threshold: number;
            batch_size: number;
            max_workers: number;
        };
        train: {
            max_train_steps: number;
            batch_size: number;
            learning_rate: number;
        };
    };
}

/**
 * Configuration loader with variable expansion support
 */
export class ConfigLoader {
    private static config: AppConfig | null = null;
    private static configPath: string | null = null;

    /**
     * Expand ${variable.path} references in config
     */
    private static expandVariables(obj: any, context: any = null): any {
        if (context === null) {
            context = obj;
        }

        if (typeof obj === 'string') {
            // Match ${variable.path} pattern
            return obj.replace(/\$\{([^}]+)\}/g, (match, varPath) => {
                let value = this.getNestedValue(context, varPath);

                // Fallback to paths prefix if not found (very common in our config.yaml)
                if (value === undefined && context.paths) {
                    value = this.getNestedValue(context.paths, varPath);
                }

                if (value === undefined) {
                    console.warn(`[ConfigLoader] Variable not found: ${varPath}`);
                    return match;
                }
                // Recursively expand nested variables
                return typeof value === 'string' ? this.expandVariables(value, context) : value;
            });
        } else if (Array.isArray(obj)) {
            return obj.map(item => this.expandVariables(item, context));
        } else if (typeof obj === 'object' && obj !== null) {
            const result: any = {};
            for (const key in obj) {
                result[key] = this.expandVariables(obj[key], context);
            }
            return result;
        }
        return obj;
    }

    /**
     * Get nested value from object using dot notation
     */
    private static getNestedValue(obj: any, path: string): any {
        const parts = path.split('.');
        let current = obj;
        for (const part of parts) {
            if (current && typeof current === 'object' && part in current) {
                current = current[part];
            } else {
                return undefined;
            }
        }
        return current;
    }

    /**
     * Load and parse config.yaml
     */
    static async load(configPath?: string): Promise<AppConfig> {
        // Return cached config if available
        if (this.config) {
            return this.config;
        }

        // Determine config path
        if (configPath) {
            this.configPath = configPath;
        } else if (!this.configPath) {
            // Default: config.yaml in the desktop app root
            this.configPath = path.join(__dirname, '../../config.yaml');
        }

        try {
            const content = await fs.readFile(this.configPath, 'utf-8');
            const rawConfig = yaml.load(content) as any;

            // Expand ${variable} references
            this.config = this.expandVariables(rawConfig);

            console.log('[ConfigLoader] Loaded config from:', this.configPath);

            if (!this.config) {
                throw new Error('Failed to parse config file');
            }

            return this.config;
        } catch (error: any) {
            console.error('[ConfigLoader] Failed to load config:', error);
            throw new Error(`Failed to load config: ${error.message}`);
        }
    }

    /**
     * Reload the configuration (useful for development)
     */
    static async reload(): Promise<AppConfig> {
        this.config = null;
        return this.load();
    }

    /**
     * Get Python executable path for kohya_ss
     */
    static async getPythonPath(): Promise<string> {
        const config = await this.load();
        const venvPath = config.kohya.venv_path;

        // Try Linux path first
        const linuxPath = path.join(venvPath, 'bin', 'python');
        try {
            await fs.access(linuxPath);
            return linuxPath;
        } catch {
            // Try Windows path
            const windowsPath = path.join(venvPath, 'python.exe');
            try {
                await fs.access(windowsPath);
                return windowsPath;
            } catch {
                throw new Error(`Python not found in venv: ${venvPath}`);
            }
        }
    }

    /**
     * Get Kohya script path by type
     */
    static async getKohyaScriptPath(scriptType: 'train' | 'train_sdxl' | 'tag'): Promise<string> {
        const config = await this.load();
        const rootPath = config.kohya.root_path;

        // Map script types to their full paths
        if (scriptType === 'train') {
            return path.join(rootPath, 'sd-scripts', 'train_network.py');
        } else if (scriptType === 'train_sdxl') {
            return path.join(rootPath, 'sd-scripts', 'sdxl_train_network.py');
        } else if (scriptType === 'tag') {
            return path.join(rootPath, config.kohya.scripts.tag);
        }

        throw new Error(`Unknown script type: ${scriptType}`);
    }
}
