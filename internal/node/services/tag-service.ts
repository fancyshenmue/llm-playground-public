import { TagOptions, TagProgress, TagResult } from '../types';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import { ConfigLoader } from './config-loader';

export class TagService {
    private static instance: TagService | null = null;
    private currentProcess: ChildProcess | null = null;

    /**
     * Get singleton instance
     */
    static getInstance(): TagService {
        if (!this.instance) {
            this.instance = new TagService();
        }
        return this.instance;
    }

    async tagImages(
        options: TagOptions,
        onProgress: (progress: TagProgress) => void
    ): Promise<TagResult> {
        // Load config dynamically
        const config = await ConfigLoader.load();
        const projectRoot = path.resolve(__dirname, '../../../../../');
        const absPath = path.resolve(projectRoot, options.path);

        console.log('Tag Service Options:', {
            path: options.path,
            absPath,
            model: options.model,
            thresholds: {
                general: options.generalThreshold,
                character: options.characterThreshold
            }
        });

        try {
            // Get Python and script paths from config
            const pythonPath = await ConfigLoader.getPythonPath();
            const scriptPath = await ConfigLoader.getKohyaScriptPath('tag');

            console.log('Python path:', pythonPath);
            console.log('Script path:', scriptPath);

            // Build arguments
            const args = [
                scriptPath,
                absPath,
                '--batch_size', options.batchSize.toString(),
                '--thresh', options.threshold.toString(),
                '--general_threshold', options.generalThreshold.toString(),
                '--character_threshold', options.characterThreshold.toString(),
                '--repo_id', options.model,
                '--caption_extension', '.txt',
                '--remove_underscore',
                '--onnx'
            ];

            if (options.undesired) {
                args.push('--undesired_tags', options.undesired);
            }
            if (options.recursive) {
                args.push('--recursive');
            }
            if (options.debug) {
                args.push('--debug');
            }
            if (options.maxWorkers > 0) {
                args.push('--max_data_loader_n_workers', options.maxWorkers.toString());
            }

            console.log('Executing:', pythonPath, args.join(' '));

            return new Promise((resolve, reject) => {
                this.currentProcess = spawn(pythonPath, args, {
                    cwd: config.kohya.root_path
                });

                this.currentProcess.stdout?.on('data', (data) => {
                    const output = data.toString();
                    console.log('[Tag stdout]', output);
                    onProgress({ status: output, type: 'stdout' });
                });

                this.currentProcess.stderr?.on('data', (data) => {
                    const output = data.toString();
                    console.log('[Tag stderr]', output);
                    onProgress({ status: output, type: 'stderr' });
                });

                this.currentProcess.on('close', (code) => {
                    this.currentProcess = null;
                    if (code === 0) {
                        console.log('Tagging completed successfully');
                        resolve({ success: true });
                    } else {
                        const error = `Tagging failed with exit code ${code}`;
                        console.error(error);
                        reject(new Error(error));
                    }
                });

                this.currentProcess.on('error', (error) => {
                    this.currentProcess = null;
                    console.error('Failed to spawn Python process:', error);
                    reject(new Error(`Failed to spawn Python: ${error.message}`));
                });
            });
        } catch (error: any) {
            console.error('Tag service error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    cancel() {
        if (this.currentProcess) {
            console.log('Cancelling tagging process...');
            this.currentProcess.kill('SIGTERM');
            this.currentProcess = null;
        }
    }

    /**
     * Check if tagging is currently running
     */
    isRunning(): boolean {
        return this.currentProcess !== null;
    }
}
