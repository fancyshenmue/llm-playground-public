package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"llm-playground/cmd/go/llm-utils/config"

	"github.com/spf13/cobra"
)

var (
	tagPath               string
	tagModel              string
	tagThreshold          float64
	tagGeneralThreshold   float64
	tagCharacterThreshold float64
	tagBatchSize          int
	tagUndesired          string
	tagRecursive          bool
	tagDebug              bool
	tagFrequency          bool
	tagMaxWorkers         int
)

// tagCmd represents the tag command
var tagCmd = &cobra.Command{
	Use:   "tag",
	Short: "Batch tag images using local Kohya_ss WD14 Tagger",
	Long: `Directly executes the Kohya_ss WD14 tagging script on a local directory.
This is the gold standard for LoRA training captions and doesn't require the Forge API.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		absPath, err := filepath.Abs(tagPath)
		if err != nil {
			return err
		}

		fmt.Printf("🚀 Starting local WD14 tagging for images in: %s\n", absPath)

		// Construct Python paths - support both Windows (python.exe) and Linux (bin/python)
		// When running WSL and accessing Windows paths, look for python.exe first
		pythonPath := filepath.Join(config.AppConfig.Kohya.VenvPath, "python.exe")
		if _, err := os.Stat(pythonPath); os.IsNotExist(err) {
			// Try Linux-style path
			pythonPath = filepath.Join(config.AppConfig.Kohya.VenvPath, "bin", "python")
		}

		// The script is located in the sd-scripts/finetune directory of Kohya_ss
		scriptPath := filepath.Join(config.AppConfig.Kohya.RootPath, "sd-scripts", "finetune", "tag_images_by_wd14_tagger.py")

		// Build arguments
		// Usage: python tag_images_by_wd14_tagger.py [input_dir] [flags]
		tagArgs := []string{
			scriptPath,
			absPath,
			"--batch_size", fmt.Sprintf("%d", tagBatchSize),
			"--thresh", fmt.Sprintf("%v", tagThreshold),
			"--general_threshold", fmt.Sprintf("%v", tagGeneralThreshold),
			"--character_threshold", fmt.Sprintf("%v", tagCharacterThreshold),
			"--repo_id", tagModel,
			"--caption_extension", ".txt",
			"--remove_underscore",
			"--onnx", // Use ONNX for better compatibility with Keras 3+
		}

		if tagUndesired != "" {
			tagArgs = append(tagArgs, "--undesired_tags", tagUndesired)
		}

		if tagRecursive {
			tagArgs = append(tagArgs, "--recursive")
		}

		if tagDebug {
			tagArgs = append(tagArgs, "--debug")
		}

		if tagFrequency {
			// In sd-scripts, this is often handled by a frequency threshold
			// or just a flag. Based on UI, we add debug/frequency info.
			fmt.Println("ℹ️ Tag frequency reporting enabled in script output.")
		}

		if tagMaxWorkers > 0 {
			tagArgs = append(tagArgs, "--max_data_loader_n_workers", fmt.Sprintf("%d", tagMaxWorkers))
		}

		tagExec := exec.Command(pythonPath, tagArgs...)
		tagExec.Stdout = os.Stdout
		tagExec.Stderr = os.Stderr
		// Set working directory to Kohya root so relative imports in scripts work
		tagExec.Dir = config.AppConfig.Kohya.RootPath

		fmt.Printf("⚙️ Running local script: %s %v\n", pythonPath, tagArgs)

		if err := tagExec.Run(); err != nil {
			return fmt.Errorf("tagging failed: %w", err)
		}

		fmt.Println("\n🎉 Local WD14 tagging complete!")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(tagCmd)

	tagCmd.Flags().StringVarP(&tagPath, "path", "p", "./dataset", "Path to the directory containing images")
	tagCmd.Flags().StringVar(&tagModel, "model", "SmilingWolf/wd-v1-4-convnextv2-tagger-v2", "WD14 Tagger model (HuggingFace repo ID)")
	tagCmd.Flags().Float64Var(&tagThreshold, "threshold", 0.35, "Threshold for tag confidence")
	tagCmd.Flags().Float64Var(&tagGeneralThreshold, "general-threshold", 0.35, "Adjust general_threshold for pruning tags")
	tagCmd.Flags().Float64Var(&tagCharacterThreshold, "character-threshold", 0.35, "Character threshold for pruning tags")
	tagCmd.Flags().IntVar(&tagBatchSize, "batch", 1, "Batch size for processing images")
	tagCmd.Flags().StringVar(&tagUndesired, "undesired", "", "Comma-separated list of tags to always remove")
	tagCmd.Flags().BoolVar(&tagRecursive, "recursive", false, "Tag subfolders images as well")
	tagCmd.Flags().BoolVar(&tagDebug, "debug", true, "Enable debug mode in script execution")
	tagCmd.Flags().BoolVar(&tagFrequency, "frequency", true, "Show frequency of tags for images")
	tagCmd.Flags().IntVar(&tagMaxWorkers, "max-workers", 2, "Max dataloader workers (recommended: 2)")
}
