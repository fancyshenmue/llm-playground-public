package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"llm-playground/cmd/go/llm-utils/config"

	"github.com/spf13/cobra"
)

var (
	trainConfigFile string
)

// trainCmd represents the train command
var trainCmd = &cobra.Command{
	Use:   "train",
	Short: "Start a LoRA training session using Kohya_ss",
	Long: `Triggers a training session by calling the underlying Kohya_ss scripts
with a provided JSON configuration file.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		if trainConfigFile == "" {
			trainConfigFile = config.AppConfig.Kohya.DefaultConfig
		}

		if trainConfigFile == "" {
			return fmt.Errorf("config file is required (explicitly via --config or set in config.yaml)")
		}

		// Read and parse the config JSON to verify it and extract key paths
		data, err := os.ReadFile(trainConfigFile)
		if err != nil {
			return fmt.Errorf("failed to read config file: %w", err)
		}

		var trainCfg map[string]interface{}
		if err := json.Unmarshal(data, &trainCfg); err != nil {
			return fmt.Errorf("failed to parse config JSON: %w", err)
		}

		fmt.Printf("🎯 Starting training with config: %s\n", trainConfigFile)

		// Construct the command - support both Windows (python.exe) and Linux (bin/python)
		pythonPath := filepath.Join(config.AppConfig.Kohya.VenvPath, "python.exe")
		if _, err := os.Stat(pythonPath); os.IsNotExist(err) {
			// Try Linux-style path
			pythonPath = filepath.Join(config.AppConfig.Kohya.VenvPath, "bin", "python")
		}

		// Determine which script to run
		scriptName := "train_network.py"
		if isSDXL, ok := trainCfg["sdxl"].(bool); ok && isSDXL {
			scriptName = "sdxl_train_network.py"
		}
		scriptPath := filepath.Join(config.AppConfig.Kohya.RootPath, "sd-scripts", scriptName)

		// Separate Accelerate and Script arguments
		accelerateArgs := []string{"-m", "accelerate.commands.launch"}
		scriptArgs := []string{scriptPath}

		// Default accelerate settings
		accSettings := map[string]string{
			"num_cpu_threads_per_process": "1",
		}

		// Keys that belong to accelerate launch, not the script
		accKeys := map[string]bool{
			"num_processes":               true,
			"num_machines":                true,
			"main_process_port":           true,
			"num_cpu_threads_per_process": true,
		}

		// Keys to skip entirely
		skipKeys := map[string]bool{
			"sdxl":       true,
			"v2":         true,
			"model_list": true,
			"LoRA_type":  true,
			"epoch":      true, // GUI display field, conflicts with max_train_epochs

			// Internal GUI or incompatible settings
			"blocks_to_swap":              true,
			"double_blocks_to_swap":       true,
			"single_blocks_to_swap":       true,
			"train_single_block_indices":  true,
			"train_double_block_indices":  true,
			"discrete_flow_shift":         true,
			"weighting_scheme":            true,
			"unit":                        true,
			"factor":                      true,
			"noise_offset_type":           true,
			"timestep_sampling":           true,
			"pos_emb_random_crop_rate":    true,
			"constrain":                   true,
			"mode_scale":                  true,
			"model_prediction_type":       true,
			"stop_text_encoder_training":  true,
			"rank_dropout":                true,
			"module_dropout":              true,
			"v_pred_like_loss":            true,
			"sd3_text_encoder_batch_size": true,
			"train_on_input":              true,
			"clip_g_dropout_rate":         true,
			"dynamo_mode":                 true,
			"guidance_scale":              true,
			"train_blocks":                true,
			"conv_dim":                    true,
			"conv_alpha":                  true,
		}

		// Skip prefixes (Common for SD3/Flux or other models)
		skipPrefixes := []string{"sd3_", "flux_", "ggpo_", "logit_", "loraplus_", "LyCORIS_", "t5xxl_", "conv_"}

		// Key mappings (GUI -> Script)
		keyMap := map[string]string{
			"optimizer":                       "optimizer_type",
			"max_resolution":                  "resolution",
			"epoch":                           "max_train_epochs",
			"sdxl_cache_text_encoder_outputs": "cache_text_encoder_outputs", // Deprecated -> New name
		}

		// Handle Standard network module
		if loraType, ok := trainCfg["LoRA_type"].(string); ok && loraType == "Standard" {
			scriptArgs = append(scriptArgs, "--network_module", "networks.lora")
		}

		// Process JSON keys
		for key, value := range trainCfg {
			if skipKeys[key] {
				continue
			}

			shouldSkipPrefix := false
			for _, prefix := range skipPrefixes {
				if len(key) >= len(prefix) && key[:len(prefix)] == prefix {
					shouldSkipPrefix = true
					break
				}
			}
			if shouldSkipPrefix {
				continue
			}

			flagName := key
			if mapped, ok := keyMap[key]; ok {
				flagName = mapped
			}

			// Special case: skip max_train_epochs if it is 0 to let "epoch" key take over
			if flagName == "max_train_epochs" {
				if v, ok := value.(float64); ok && v == 0 {
					continue
				}
			}

			// Special case: skip max_train_steps if it is 0
			if flagName == "max_train_steps" {
				if v, ok := value.(float64); ok && v == 0 {
					continue
				}
			}

			// Special case: Skip 0 values for interval/every_n flags to avoid ZeroDivisionError
			intervalKeys := map[string]bool{
				"save_every_n_steps":       true,
				"save_every_n_epochs":      true,
				"sample_every_n_steps":     true,
				"sample_every_n_epochs":    true,
				"save_last_n_steps":        true,
				"save_last_n_epochs":       true,
				"save_last_n_steps_state":  true,
				"save_last_n_epochs_state": true,
			}
			if intervalKeys[flagName] {
				if v, ok := value.(float64); ok && v == 0 {
					continue
				}
			}

			// Value-based skipping
			if key == "max_token_length" {
				if v, ok := value.(float64); ok && v == 75 {
					continue
				}
			}
			if key == "dynamo_backend" {
				if v, ok := value.(string); ok && (v == "no" || v == "none" || v == "") {
					continue
				}
			}

			// Distribute value
			if accKeys[flagName] {
				accSettings[flagName] = fmt.Sprintf("%v", value)
				continue
			}

			flag := "--" + flagName
			switch v := value.(type) {
			case bool:
				if v {
					scriptArgs = append(scriptArgs, flag)
				}
			case string:
				if v != "" && v != "None" && v != "none" {
					if flagName == "xformers" && v == "xformers" {
						scriptArgs = append(scriptArgs, flag)
					} else if flagName == "optimizer_args" || flagName == "lr_scheduler_args" || flagName == "network_args" {
						// These flags expect multiple space-separated arguments
						parts := strings.Fields(v)
						scriptArgs = append(scriptArgs, flag)
						scriptArgs = append(scriptArgs, parts...)
					} else {
						scriptArgs = append(scriptArgs, flag, v)
					}
				}
			case float64:
				// Safety check: vae_batch_size must be at least 1 for latent caching
				if flagName == "vae_batch_size" && v == 0 {
					v = 1
				}
				scriptArgs = append(scriptArgs, flag, fmt.Sprintf("%v", v))
			}
		}

		// Auto-fix: If caching text encoder outputs, must train UNet only
		// Check if cache_text_encoder_outputs is in scriptArgs
		hasCacheTextEncoder := false
		for _, arg := range scriptArgs {
			if arg == "--cache_text_encoder_outputs" || arg == "--cache_text_encoder_outputs_to_disk" {
				hasCacheTextEncoder = true
				break
			}
		}
		if hasCacheTextEncoder {
			// Add network_train_unet_only to avoid conflict
			scriptArgs = append(scriptArgs, "--network_train_unet_only")
			fmt.Println("ℹ️  Auto-added --network_train_unet_only (required when caching text encoder outputs)")
		}

		// Combine accelerate settings
		for k, v := range accSettings {
			accelerateArgs = append(accelerateArgs, "--"+k, v)
		}

		// Final final command
		trainArgs := append(accelerateArgs, scriptArgs...)

		trainExec := exec.Command(pythonPath, trainArgs...)
		trainExec.Stdout = os.Stdout
		trainExec.Stderr = os.Stderr
		trainExec.Dir = config.AppConfig.Kohya.RootPath

		fmt.Printf("📂 Working directory: %s\n", trainExec.Dir)
		fmt.Printf("⚙️ Running command: %s %v\n", pythonPath, trainArgs)

		if err := trainExec.Run(); err != nil {
			return fmt.Errorf("training failed: %w", err)
		}

		fmt.Println("\n🎉 Training session complete!")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(trainCmd)
	trainCmd.Flags().StringVarP(&trainConfigFile, "config", "c", "", "Path to the training .json configuration file")
}
