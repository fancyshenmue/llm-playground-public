package cmd

import (
	"encoding/base64"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"llm-playground/cmd/go/llm-utils/config"
	"llm-playground/internal/go/api"

	"github.com/spf13/cobra"
)

var (
	rankDir string
)

// rankCmd represents the rank command
var rankCmd = &cobra.Command{
	Use:   "rank [directory]",
	Short: "Rank images in a directory using vision models",
	Long: `Loops through images in a directory and uses llama3.2-vision 
to score them based on a set of criteria (similarity to prompt, style, etc.).`,
	RunE: func(cmd *cobra.Command, args []string) error {
		targetDir := rankDir
		if targetDir == "" && len(args) > 0 {
			targetDir = args[0]
		}
		if targetDir == "" {
			targetDir = "./images"
		}

		fmt.Printf("📊 Ranking images in: %s\n", targetDir)

		files, err := os.ReadDir(targetDir)
		if err != nil {
			return err
		}

		var imageFiles []string
		for _, f := range files {
			if !f.IsDir() && (filepath.Ext(f.Name()) == ".png" || filepath.Ext(f.Name()) == ".jpg") {
				imageFiles = append(imageFiles, filepath.Join(targetDir, f.Name()))
			}
		}

		if len(imageFiles) == 0 {
			return fmt.Errorf("no images found in %s", targetDir)
		}

		ollamaClient := api.NewOllamaClient(config.AppConfig.Ollama.BaseURL)

		fmt.Println("🧠 Evaluating images...")
		for _, imgPath := range imageFiles {
			imgData, err := os.ReadFile(imgPath)
			if err != nil {
				fmt.Printf("❌ Failed to read %s: %v\n", imgPath, err)
				continue
			}
			base64Img := base64.StdEncoding.EncodeToString(imgData)

			req := api.GenerateRequest{
				Model:  "llama3.2-vision",
				Prompt: "Please rate this image from 1 to 10 based on visual appeal and style consistency. Return only the number and a short reason.",
				Stream: false,
				Images: []string{base64Img},
			}

			resp, err := ollamaClient.Generate(req)
			if err != nil {
				fmt.Printf("❌ Error analyzing %s: %v\n", filepath.Base(imgPath), err)
				continue
			}

			fmt.Printf("🖼️  %s: %s\n", filepath.Base(imgPath), strings.TrimSpace(resp.Response))
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(rankCmd)
	rankCmd.Flags().StringVarP(&rankDir, "dir", "d", "", "Directory containing images to rank")
}
