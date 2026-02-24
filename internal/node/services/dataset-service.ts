import * as fs from 'fs/promises';
import * as path from 'path';
import { ConfigLoader } from './config-loader';

export class DatasetService {
    private static instance: DatasetService | null = null;

    /**
     * Get singleton instance
     */
    static getInstance(): DatasetService {
        if (!this.instance) {
            this.instance = new DatasetService();
        }
        return this.instance;
    }

    /**
     * Promote a tagged dataset to the training directory
     * @param sourcePath Original path of the tagged dataset
     * @param topicName Topic name for the folder (e.g. "country_road")
     * @param repeats Number of repeats (e.g. 10)
     */
    async promote(sourcePath: string, topicName: string, repeats: number): Promise<{ success: boolean; error?: string; destPath?: string }> {
        try {
            const config = await ConfigLoader.load();
            const projectRoot = path.resolve(__dirname, '../../../../../');

            // Resolve source path (might be relative to project root)
            const absSourcePath = path.isAbsolute(sourcePath)
                ? sourcePath
                : path.resolve(projectRoot, sourcePath);

            // Verify source exists
            try {
                await fs.access(absSourcePath);
            } catch (e) {
                return { success: false, error: `Source path does not exist: ${absSourcePath}` };
            }

            // Construct destination path
            const trainImageDir = config.paths.train_image_dir;
            const absTrainImageRoot = path.isAbsolute(trainImageDir)
                ? trainImageDir
                : path.resolve(projectRoot, trainImageDir);

            const folderName = `${repeats}_${topicName}`;
            const absDestPath = path.join(absTrainImageRoot, folderName);

            console.log('Promoting dataset:', {
                source: absSourcePath,
                dest: absDestPath,
                repeats,
                topic: topicName
            });

            // Ensure destination root exists
            await fs.mkdir(absTrainImageRoot, { recursive: true });

            // Check if destination already exists
            try {
                await fs.access(absDestPath);
                return { success: false, error: `Destination already exists: ${absDestPath}. Please remove it first or use a different name.` };
            } catch (e) {
                // Good, destination doesn't exist
            }

            // Move the folder
            await fs.rename(absSourcePath, absDestPath);

            return {
                success: true,
                destPath: absDestPath
            };
        } catch (error: any) {
            console.error('Dataset promotion failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}
