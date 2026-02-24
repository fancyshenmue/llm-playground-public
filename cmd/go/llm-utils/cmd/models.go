package cmd

import (
	"fmt"
	"llm-playground/cmd/go/llm-utils/config"
	"llm-playground/internal/go/api"

	"github.com/spf13/cobra"
)

// modelsCmd represents the models command
var modelsCmd = &cobra.Command{
	Use:   "models",
	Short: "Manage and list available models",
}

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List all local/remote models",
	RunE: func(cmd *cobra.Command, args []string) error {
		client := api.NewOllamaClient(config.AppConfig.Ollama.BaseURL)
		
		if verbose {
			fmt.Printf("Fetching models from: %s\n", config.AppConfig.Ollama.BaseURL)
		}

		models, err := client.ListModels()
		if err != nil {
			return err
		}

		fmt.Println("Available Ollama Models:")
		for _, m := range models {
			fmt.Printf("- %s\n", m)
		}
		return nil
	},
}

func init() {
	rootCmd.AddCommand(modelsCmd)
	modelsCmd.AddCommand(listCmd)
}
