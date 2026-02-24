package cmd

import (
	"encoding/base64"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"llm-playground/cmd/go/llm-utils/config"
	"llm-playground/internal/go/api"

	"github.com/spf13/cobra"
)

var (
	imagePath string
)

// analyzeCmd represents the analyze command
var analyzeCmd = &cobra.Command{
	Use:   "analyze [file]",
	Short: "Analyze an image using Llama Vision and store results",
	Long: `Analyzes a given image with llama3.2-vision and automatically 
stores the analysis in the AnythingLLM knowledge base.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		targetImage := imagePath
		if targetImage == "" {
			if len(args) > 0 {
				targetImage = args[0]
			} else {
				// Auto-find latest image from images/ if directory exists
				dir := "./images"
				files, err := os.ReadDir(dir)
				if err != nil {
					return fmt.Errorf("no image specified and could not read ./images: %w", err)
				}

				var imageFiles []os.DirEntry
				for _, f := range files {
					if !f.IsDir() && (filepath.Ext(f.Name()) == ".png" || filepath.Ext(f.Name()) == ".jpg") {
						imageFiles = append(imageFiles, f)
					}
				}

				if len(imageFiles) == 0 {
					return fmt.Errorf("no images found in ./images")
				}

				sort.Slice(imageFiles, func(i, j int) bool {
					infoI, _ := imageFiles[i].Info()
					infoJ, _ := imageFiles[j].Info()
					return infoI.ModTime().After(infoJ.ModTime())
				})
				targetImage = filepath.Join(dir, imageFiles[0].Name())
			}
		}

		fmt.Printf("🔍 Analyzing image: %s\n", targetImage)

		imgData, err := os.ReadFile(targetImage)
		if err != nil {
			return err
		}
		base64Img := base64.StdEncoding.EncodeToString(imgData)

		ollamaClient := api.NewOllamaClient(config.AppConfig.Ollama.BaseURL)
		
		fmt.Println("🧠 Sending to Ollama (llama3.2-vision)...")
		req := api.GenerateRequest{
			Model:  "llama3.2-vision",
			Prompt: "This is a Stable Diffusion generated image. Please analyze its composition, lighting details, and the presentation of the FancyStyle effect, then provide suggestions for improvement. Please answer in English.",
			Stream: false,
			Images: []string{base64Img},
		}

		resp, err := ollamaClient.Generate(req)
		if err != nil {
			return err
		}

		analysis := resp.Response
		fmt.Printf("\n--- Analysis Result ---\n%s\n-----------------------\n", analysis)

		if config.AppConfig.Anything.APIKey != "YOUR_API_KEY_HERE" && config.AppConfig.Anything.APIKey != "" {
			fmt.Println("📦 Storing result in AnythingLLM...")
			anythingClient := api.NewAnythingClient(config.AppConfig.Anything.BaseURL, config.AppConfig.Anything.APIKey)

			docName := fmt.Sprintf("Analysis_%s.txt", filepath.Base(targetImage))
			location, err := anythingClient.UploadRawText(api.RawTextRequest{
				TextContent: fmt.Sprintf("Image Full Path: %s\n\nAnalysis Result:\n%s", targetImage, analysis),
				Metadata: map[string]interface{}{
					"title":  docName,
					"source": "Ollama-Vision-Automation",
				},
			})
			if err != nil {
				return fmt.Errorf("failed to upload to AnythingLLM: %w", err)
			}

			if err := anythingClient.UpdateEmbeddings(config.AppConfig.Anything.Workspace, []string{location}); err != nil {
				return fmt.Errorf("failed to update embeddings: %w", err)
			}

			fmt.Println("✅ Automation process complete!")
		} else {
			fmt.Println("⚠️ AnythingLLM API Key not configured. Skipping storage phase.")
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(analyzeCmd)
	analyzeCmd.Flags().StringVarP(&imagePath, "image", "i", "", "Path to the image file (defaults to latest in ./images)")
}
