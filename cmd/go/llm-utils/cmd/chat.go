package cmd

import (
	"fmt"
	"llm-playground/cmd/go/llm-utils/config"
	"llm-playground/internal/go/api"

	"github.com/spf13/cobra"
)

var (
	prompt      string
	system      string
	temperature float64
	maxTokens   int
)

// chatCmd represents the chat command
var chatCmd = &cobra.Command{
	Use:   "chat [model]",
	Short: "Send a prompt to a specific model",
	Args:  cobra.MaximumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		model := config.AppConfig.Ollama.Model
		if len(args) > 0 {
			model = args[0]
		}

		client := api.NewOllamaClient(config.AppConfig.Ollama.BaseURL)

		if prompt != "" {
			if verbose {
				fmt.Printf("Using model: %s\n", model)
				fmt.Printf("Endpoint: %s\n", config.AppConfig.Ollama.BaseURL)
			}

			req := api.GenerateRequest{
				Model:  model,
				Prompt: prompt,
				Stream: false,
			}

			resp, err := client.Generate(req)
			if err != nil {
				return err
			}

			fmt.Println(resp.Response)
			return nil
		}

		return fmt.Errorf("interactive chat mode not yet implemented. Please use --prompt flag")
	},
}

func init() {
	rootCmd.AddCommand(chatCmd)

	chatCmd.Flags().StringVarP(&prompt, "prompt", "p", "", "Single prompt to send")
	chatCmd.Flags().StringVarP(&system, "system", "s", "", "System message")
	chatCmd.Flags().Float64VarP(&temperature, "temp", "t", 0.7, "Sampling temperature")
	chatCmd.Flags().IntVar(&maxTokens, "max-tokens", 1024, "Maximum tokens to generate")
}
