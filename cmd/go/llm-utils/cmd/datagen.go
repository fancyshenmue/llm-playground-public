package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"llm-playground/cmd/go/llm-utils/config"
	"llm-playground/internal/go/api"

	"github.com/spf13/cobra"
)

var (
	totalImages  uint
	outputDir    string
	topic        string
	loraName     string
	loraWeight   float64
	noCaption    bool
	manualPrompt string
	useTimestamp bool
	triggerWord  string
)

// datagenCmd represents the data-gen command
var datagenCmd = &cobra.Command{
	Use:   "data-gen",
	Short: "Generate training data (prompts and images)",
	Long: `Automatically generates a dataset of images and their corresponding captions.
It uses Ollama to generate unique prompts and Forge (Stable Diffusion) to generate images.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		absOutputDir, err := filepath.Abs(outputDir)
		if err != nil {
			return err
		}

		if err := os.MkdirAll(absOutputDir, 0755); err != nil {
			return fmt.Errorf("failed to create output directory: %w", err)
		}

		ollamaClient := api.NewOllamaClient(config.AppConfig.Ollama.BaseURL)
		forgeClient := api.NewForgeClient(config.AppConfig.Forge.BaseURL)

		// Display what we're generating
		if manualPrompt != "" {
			fmt.Printf("🚀 Starting generation of %d images with manual prompt\n", totalImages)
			fmt.Printf("📝 Prompt: %s\n", manualPrompt)
		} else {
			fmt.Printf("🚀 Starting generation of %d images for topic: %s\n", totalImages, topic)
		}
		fmt.Printf("📍 Output location: %s\n", absOutputDir)

		for i := uint(0); i < totalImages; i++ {
			var prompt, caption string
			var err error

			if manualPrompt != "" {
				fmt.Printf("\n📝 [Iteration %d/%d] Using manual prompt...\n", i+1, totalImages)
				prompt = manualPrompt
				caption = manualPrompt // For manual prompt, we just use the same as caption
			} else {
				fmt.Printf("\n🧠 [Iteration %d/%d] Generating unique prompt and tags...\n", i+1, totalImages)
				prompt, caption, err = getPromptAndCaption(ollamaClient, i)
				if err != nil {
					fmt.Printf("❌ Ollama Error: %v. Using fallback.\n", err)
					prompt = fmt.Sprintf("a high quality photo of %s, cinematic lighting, detailed", topic)
					caption = fmt.Sprintf("a photo of %s", topic)
				}
			}

			// Inject LoRA if specified
			if loraName != "" {
				// Determine trigger word: use flag if provided, otherwise detect/default
				finalTrigger := triggerWord
				if finalTrigger == "" {
					finalTrigger = "FancyStyle"
					if strings.Contains(loraName, "BeautyGirlStyle") {
						finalTrigger = "BeautyGirlStyle"
					}
				}

				// Strip extension for the tag
				loraTag := loraName
				if idx := strings.LastIndex(loraName, "."); idx != -1 {
					loraTag = loraName[:idx]
				}
				prompt = fmt.Sprintf("%s, <lora:%s:%g>, %s", finalTrigger, loraTag, loraWeight, prompt)
				fmt.Printf("🧬 LoRA injected: %s (weight: %g, trigger: %s)\n", loraTag, loraWeight, finalTrigger)
			}

			safeTopic := strings.ReplaceAll(strings.ToLower(topic), " ", "_")
			filename := fmt.Sprintf("%s_%03d", safeTopic, i+1)
			if useTimestamp {
				filename = fmt.Sprintf("%d_%03d", time.Now().Unix(), i+1)
			}
			imagePath := filepath.Join(absOutputDir, filename+".png")
			captionPath := filepath.Join(absOutputDir, filename+".txt")

			fmt.Printf("🎨 Generating Image: %s...\n", filename)

			forgeReq := api.Txt2ImgRequest{
				Prompt:         prompt,
				NegativePrompt: "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
				Steps:          30,
				Width:          1024,
				Height:         1024,
				CFGScale:       7.0,
				SamplerName:    "DPM++ 2M Karras",
				OverrideSettings: map[string]interface{}{
					"sd_model_checkpoint": config.AppConfig.Forge.Model,
				},
			}

			if err := forgeClient.Txt2Img(forgeReq, imagePath); err != nil {
				fmt.Printf("❌ Forge Error: %v\n", err)
				continue
			}

			if !noCaption {
				if err := os.WriteFile(captionPath, []byte(caption), 0644); err != nil {
					fmt.Printf("❌ Failed to save caption: %v\n", err)
					continue
				}
				fmt.Printf("✅ Saved %s.png and %s.txt\n", filename, filename)
			} else {
				fmt.Printf("✅ Saved %s.png (Caption skipped)\n", filename)
			}
			time.Sleep(1 * time.Second)
		}

		fmt.Println("\n🎉 Training data generation complete!")
		return nil
	},
}

func getPromptAndCaption(client *api.OllamaClient, index uint) (string, string, error) {
	systemInstruction := fmt.Sprintf(`You are an expert at generating diversified training data for Stable Diffusion.
The goal is to generate a unique image description for the topic: "%s" and its corresponding BLIP-style caption.
Each description MUST be unique (different settings, poses, lighting, perspectives).
Return a JSON object with two keys:
'prompt': A highly detailed SDXL prompt (English).
'caption': A natural language BLIP-style caption describing the image content.
Example output: {"prompt": "a detailed description of %s...", "caption": "a photo of %s..."}`, topic, topic, topic)

	userPrompt := fmt.Sprintf("Topic: %s. This is iteration %d. Ensure it's different from previous ones.", topic, index+1)

	req := api.GenerateRequest{
		Model:  config.AppConfig.Ollama.Model,
		Prompt: fmt.Sprintf("%s\n\n%s", systemInstruction, userPrompt),
		Format: "json",
		Stream: false,
	}

	resp, err := client.Generate(req)
	if err != nil {
		return "", "", err
	}

	var result struct {
		Prompt  string `json:"prompt"`
		Caption string `json:"caption"`
	}

	if err := json.Unmarshal([]byte(resp.Response), &result); err != nil {
		return "", "", fmt.Errorf("failed to parse JSON response: %w", err)
	}

	return result.Prompt, result.Caption, nil
}

func init() {
	rootCmd.AddCommand(datagenCmd)

	datagenCmd.Flags().UintVarP(&totalImages, "total", "n", 30, "Total number of images to generate")
	datagenCmd.Flags().StringVarP(&outputDir, "output", "o", "./dataset/generated_data", "Output directory for the dataset")
	datagenCmd.Flags().StringVarP(&topic, "topic", "T", "random object", "Topic for image generation")
	datagenCmd.Flags().StringVarP(&loraName, "lora", "L", "", "LoRA model to use (autocomplete supported)")
	datagenCmd.Flags().Float64VarP(&loraWeight, "weight", "W", 1.0, "LoRA weight (0.1 to 1.0)")
	datagenCmd.Flags().BoolVarP(&noCaption, "no-caption", "C", false, "Skip generating .txt caption files")
	datagenCmd.Flags().StringVarP(&manualPrompt, "prompt", "p", "", "Manual base prompt (skips Ollama)")
	datagenCmd.Flags().BoolVar(&useTimestamp, "timestamp", false, "Include Unix timestamp in filenames")
	datagenCmd.Flags().StringVarP(&triggerWord, "trigger", "g", "", "Override the default LoRA trigger word")

	// Register autocomplete for the --lora flag
	datagenCmd.RegisterFlagCompletionFunc("lora", func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
		return config.AppConfig.Forge.Loras, cobra.ShellCompDirectiveNoFileComp
	})
}
