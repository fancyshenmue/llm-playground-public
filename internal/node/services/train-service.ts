import { spawn, ChildProcess } from 'child_process';
import * as fs from 'fs/promises';
import { ConfigLoader } from './config-loader';

export interface TrainProgress {
    epoch?: number;
    maxEpochs?: number;
    step?: number;
    maxSteps?: number;
    loss?: number;
    status: string;
    type: 'stdout' | 'stderr' | 'info';
}

export interface TrainResult {
    success: boolean;
    error?: string;
}

export class TrainService {
    private static instance: TrainService | null = null;
    private currentProcess: ChildProcess | null = null;

    /**
     * Get singleton instance
     */
    static getInstance(): TrainService {
        if (!this.instance) {
            this.instance = new TrainService();
        }
        return this.instance;
    }

    /**
     * Start LoRA training with a given config file
     */
    async train(
        configPath: string,
        onProgress: (progress: TrainProgress) => void
    ): Promise<TrainResult> {
        try {
            // Load app config
            const config = await ConfigLoader.load();

            // Read training config JSON
            const configContent = await fs.readFile(configPath, 'utf-8');
            const trainConfig = JSON.parse(configContent);

            // Determine which script to use based on sdxl flag
            const isSDXL = trainConfig.sdxl === true;
            const scriptType = isSDXL ? 'train_sdxl' : 'train';

            // Get Python and script paths
            const pythonPath = await ConfigLoader.getPythonPath();
            const scriptPath = await ConfigLoader.getKohyaScriptPath(scriptType);

            console.log('[TrainService] Starting training:', {
                configPath,
                pythonPath,
                scriptPath,
                outputName: trainConfig.output_name,
                isSDXL
            });

            // Build script arguments first
            const { scriptArgs, accSettings } = this.buildTrainArgs(trainConfig);

            // Build accelerate arguments array
            const accelerateArgs = [
                '-m', 'accelerate.commands.launch',
            ];
            for (const [key, value] of Object.entries(accSettings)) {
                accelerateArgs.push(`--${key}`, value);
            }

            // Combine accelerate + script arguments
            const args = [
                ...accelerateArgs,
                scriptPath,
                ...scriptArgs
            ];

            console.log('[TrainService] Command:', pythonPath, args.join(' '));

            return new Promise((resolve, reject) => {
                // Use detached process group so we can kill all children
                this.currentProcess = spawn(pythonPath, args, {
                    cwd: config.kohya.root_path,
                    detached: true,  // Create new process group
                    stdio: ['ignore', 'pipe', 'pipe']
                });

                this.currentProcess.stdout?.on('data', (data) => {
                    const output = data.toString();
                    console.log('[Train stdout]', output);

                    // Parse training progress
                    const progress = this.parseOutput(output);
                    onProgress(progress);
                });

                this.currentProcess.stderr?.on('data', (data) => {
                    const output = data.toString();
                    console.log('[Train stderr]', output);
                    onProgress({ status: output, type: 'stderr' });
                });

                this.currentProcess.on('close', (code) => {
                    this.currentProcess = null;
                    if (code === 0) {
                        console.log('[TrainService] Training completed successfully');
                        resolve({ success: true });
                    } else {
                        const error = `Training failed with exit code ${code}`;
                        console.error('[TrainService]', error);
                        reject(new Error(error));
                    }
                });

                this.currentProcess.on('error', (error) => {
                    this.currentProcess = null;
                    console.error('[TrainService] Failed to spawn Python:', error);
                    reject(new Error(`Failed to spawn Python: ${error.message}`));
                });
            });
        } catch (error: any) {
            console.error('[TrainService] Error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Cancel the current training process
     */
    cancel() {
        if (this.currentProcess && this.currentProcess.pid) {
            console.log('[TrainService] Cancelling training...');
            try {
                // Kill entire process group (negative PID)
                // This kills accelerate launcher and all python subprocesses
                process.kill(-this.currentProcess.pid, 'SIGTERM');

                // Backup: also try killing the main process
                setTimeout(() => {
                    if (this.currentProcess && !this.currentProcess.killed) {
                        try {
                            process.kill(-this.currentProcess.pid!, 'SIGKILL');
                        } catch (e) {
                            console.log('[TrainService] Process already dead');
                        }
                    }
                }, 1000);
            } catch (error: any) {
                console.error('[TrainService] Failed to kill process:', error.message);
            }
            this.currentProcess = null;
        }
    }

    /**
     * Build training arguments from JSON config (script args only)
     * Match the full parameter set from Go llm-utils
     */
    private buildTrainArgs(config: any): { scriptArgs: string[], accSettings: Record<string, string> } {
        const scriptArgs: string[] = [];
        const accSettings: Record<string, string> = {
            "num_cpu_threads_per_process": "8" // Default
        };

        // Keys that belong to accelerate launch, not the script
        const accKeys = new Set([
            "num_processes",
            "num_machines",
            "main_process_port",
            "num_cpu_threads_per_process",
            "mixed_precision"
        ]);

        // Keys to skip entirely (GUI internal or handled elsewhere)
        const skipKeys = new Set([
            "sdxl",
            "v2",
            "model_list",
            "LoRA_type",
            "epoch",
            "blocks_to_swap",
            "double_blocks_to_swap",
            "single_blocks_to_swap",
            "train_single_block_indices",
            "train_double_block_indices",
            "discrete_flow_shift",
            "weighting_scheme",
            "unit",
            "factor",
            "noise_offset_type",
            "timestep_sampling",
            "pos_emb_random_crop_rate",
            "constrain",
            "mode_scale",
            "model_prediction_type",
            "stop_text_encoder_training",
            "rank_dropout",
            "module_dropout",
            "v_pred_like_loss",
            "sd3_text_encoder_batch_size",
            "train_on_input",
            "clip_g_dropout_rate",
            "dynamo_mode",
            "guidance_scale",
            "train_blocks",
            "conv_dim",
            "conv_alpha"
        ]);

        const skipPrefixes = ["sd3_", "flux_", "ggpo_", "logit_", "loraplus_", "LyCORIS_", "t5xxl_", "conv_"];

        const keyMap: Record<string, string> = {
            "optimizer": "optimizer_type",
            "max_resolution": "resolution",
            "epoch": "max_train_epochs",
            "sdxl_cache_text_encoder_outputs": "cache_text_encoder_outputs",
            "sdxl_cache_text_encoder_outputs_to_disk": "cache_text_encoder_outputs_to_disk"
        };

        // Network module
        if (config.LoRA_type === 'Standard' || !config.LoRA_type) {
            scriptArgs.push('--network_module', 'networks.lora');
        }

        for (const [key, value] of Object.entries(config)) {
            if (skipKeys.has(key)) continue;
            if (skipPrefixes.some(p => key.startsWith(p))) continue;

            let flagName = keyMap[key] || key;

            // Special cases for 0/empty/default values to skip
            if (flagName === 'max_train_epochs' && value === 0) continue;
            if (flagName === 'max_train_steps' && value === 0) continue;
            if (flagName === 'max_token_length' && value === 75) continue;
            if (flagName === 'dynamo_backend' && (value === 'no' || value === 'none' || value === '')) continue;

            const intervalKeys = [
                "save_every_n_steps", "save_every_n_epochs",
                "sample_every_n_steps", "sample_every_n_epochs",
                "save_last_n_steps", "save_last_n_epochs",
                "save_last_n_steps_state", "save_last_n_epochs_state"
            ];
            if (intervalKeys.includes(flagName) && value === 0) continue;

            // Distribute to Accelerate or Script
            if (accKeys.has(flagName)) {
                accSettings[flagName] = String(value);
                // Also pass mixed_precision to script as it expects it too if we want full_bf16
                if (flagName !== 'mixed_precision') {
                    continue;
                }
            }

            const flag = `--${flagName}`;
            if (typeof value === 'boolean') {
                if (value) scriptArgs.push(flag);
            } else if (typeof value === 'string') {
                if (value !== '' && value.toLowerCase() !== 'none') {
                    if (flagName === 'xformers' && value === 'xformers') {
                        scriptArgs.push(flag);
                    } else if (['optimizer_args', 'lr_scheduler_args', 'network_args'].includes(flagName)) {
                        const parts = value.split(/\s+/).filter(p => p.length > 0);
                        scriptArgs.push(flag, ...parts);
                    } else {
                        scriptArgs.push(flag, value);
                    }
                }
            } else if (typeof value === 'number') {
                let v = value;
                if (flagName === 'vae_batch_size' && v === 0) v = 1;
                scriptArgs.push(flag, String(v));
            }
        }

        // Auto-fix: Caching Text Encoder + Network Train UNet Only
        const hasCache = scriptArgs.some(a => a === '--cache_text_encoder_outputs' || a === '--cache_text_encoder_outputs_to_disk');
        if (hasCache && !scriptArgs.includes('--network_train_unet_only')) {
            scriptArgs.push('--network_train_unet_only');
        }

        // Remove hardcoded full_bf16 injection. Let the loop handle it based on the config JSON.

        return { scriptArgs, accSettings };
    }

    /**
     * Parse training output to extract progress information
     */
    private parseOutput(output: string): TrainProgress {
        // Example output: "epoch 1/16" or "steps: 4%|▉ | 66/1600 [01:43<39:59, 1.56s/it, avr_loss=0.165]"
        const progress: TrainProgress = {
            status: output.trim(),
            type: 'stdout'
        };

        // Parse epoch
        const epochMatch = output.match(/epoch[:\s]+(\d+)\/(\d+)/i);
        if (epochMatch) {
            progress.epoch = parseInt(epochMatch[1]);
            progress.maxEpochs = parseInt(epochMatch[2]);
        }

        // Parse step from tqdm progress bar
        const stepMatch = output.match(/(\d+)\/(\d+)\s+\[/);
        if (stepMatch) {
            progress.step = parseInt(stepMatch[1]);
            progress.maxSteps = parseInt(stepMatch[2]);
        }

        // Parse loss
        const lossMatch = output.match(/avr_loss=([0-9.]+)/i);
        if (lossMatch) {
            progress.loss = parseFloat(lossMatch[1]);
        }

        return progress;
    }

    /**
     * Check if training is currently running
     */
    isRunning(): boolean {
        return this.currentProcess !== null;
    }
}
